from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("APP_SECRET_KEY", "micro-expression-demo-secret-key-2024")
ACCESS_TOKEN_TTL_SECONDS = 60 * 60 * 2  # 2小时（缩短以提高安全性）
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7  # 7天（缩短刷新令牌有效期）
security = HTTPBearer(auto_error=False)

# 存储刷新令牌（生产环境应使用数据库存储）
_refresh_tokens: dict[str, dict] = {}

# 黑名单存储（用于主动吊销token）
_revoked_tokens: set[str] = set()

# Token使用计数限制（防止滥用）
_token_usage: dict[str, int] = {}
MAX_TOKEN_USAGE_PER_HOUR = 1000


def hash_password(password: str, salt: str | None = None) -> str:
    """
    哈希密码
    :param password: 原始密码
    :param salt: 盐值（可选，不传则自动生成）
    :return: 格式为 "salt$hash" 的字符串
    """
    raw_salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    # 使用100000次迭代的PBKDF2-HMAC-SHA256
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), raw_salt.encode("utf-8"), 100_000)
    return f"{raw_salt}${base64.urlsafe_b64encode(digest).decode('utf-8')}"


def verify_password(password: str, stored_value: str) -> bool:
    """
    验证密码
    :param password: 输入的密码
    :param stored_value: 存储的哈希值
    :return: 是否匹配
    """
    try:
        salt, _ = stored_value.split("$", maxsplit=1)
    except ValueError:
        logger.warning("无效的密码哈希格式")
        return False
    
    # 使用hmac.compare_digest防止时序攻击
    return hmac.compare_digest(hash_password(password, salt), stored_value)


def _encode_payload(payload: dict[str, Any]) -> str:
    """Base64URL编码payload"""
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("utf-8").rstrip("=")


def _decode_payload(token_payload: str) -> dict[str, Any]:
    """Base64URL解码payload"""
    padding = "=" * (-len(token_payload) % 4)
    decoded = base64.urlsafe_b64decode(f"{token_payload}{padding}")
    return json.loads(decoded.decode("utf-8"))


def issue_tokens(user_id: int, email: str) -> dict[str, str]:
    """
    签发访问令牌和刷新令牌
    :param user_id: 用户ID
    :param email: 用户邮箱
    :return: 包含access_token和refresh_token的字典
    """
    # 签发访问令牌
    access_payload = {
        "user_id": user_id,
        "email": email,
        "token_type": "access",
        "exp": int(time.time()) + ACCESS_TOKEN_TTL_SECONDS,
        "iat": int(time.time())
    }
    access_token = _generate_token(access_payload)
    
    # 签发刷新令牌
    refresh_payload = {
        "user_id": user_id,
        "email": email,
        "token_type": "refresh",
        "exp": int(time.time()) + REFRESH_TOKEN_TTL_SECONDS,
        "iat": int(time.time()),
        "jti": hashlib.sha256(f"{user_id}_{time.time()}_{os.urandom(16)}".encode()).hexdigest()[:32]
    }
    refresh_token = _generate_token(refresh_payload)
    
    # 存储刷新令牌（生产环境应使用数据库存储，并关联用户ID）
    _refresh_tokens[refresh_token] = {
        "user_id": user_id,
        "email": email,
        "jti": refresh_payload["jti"],
        "expires_at": refresh_payload["exp"],
        "created_at": int(time.time())
    }
    
    logger.info(f"用户 {user_id} 签发新令牌")
    return {"access_token": access_token, "refresh_token": refresh_token}


def issue_token(user_id: int, email: str) -> str:
    """
    签发访问令牌（兼容旧代码）
    :param user_id: 用户ID
    :param email: 用户邮箱
    :return: 访问令牌字符串
    """
    tokens = issue_tokens(user_id, email)
    return tokens["access_token"]


def _generate_token(payload: dict[str, Any]) -> str:
    """生成JWT令牌"""
    encoded_payload = _encode_payload(payload)
    signature = hmac.new(SECRET_KEY.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_token(token: str, require_access_token: bool = True) -> dict[str, Any]:
    """
    解码并验证令牌
    :param token: JWT令牌
    :param require_access_token: 是否要求必须是access token
    :return: 解码后的payload
    """
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError as error:
        logger.warning("令牌格式无效")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌格式无效") from error

    # 检查黑名单
    if token in _revoked_tokens:
        logger.warning("令牌已被吊销")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已被吊销")

    # 验证签名
    expected_signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        logger.warning("令牌签名无效")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌签名无效")

    # 解码payload
    payload = _decode_payload(encoded_payload)
    
    # 检查过期时间
    if payload.get("exp", 0) < int(time.time()):
        logger.warning("令牌已过期")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已过期")
    
    # 检查令牌类型
    if require_access_token and payload.get("token_type") != "access":
        logger.warning("需要access令牌")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要访问令牌")
    
    # 检查token使用限制
    _check_token_usage(payload.get("user_id"))
    
    return payload

def _check_token_usage(user_id: int) -> None:
    """检查token使用频率限制"""
    if user_id is None:
        return
    
    current_hour = int(time.time() // 3600)
    key = f"{user_id}:{current_hour}"
    
    _token_usage[key] = _token_usage.get(key, 0) + 1
    
    if _token_usage[key] > MAX_TOKEN_USAGE_PER_HOUR:
        logger.warning(f"用户 {user_id} 的token使用超过限制")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="请求过于频繁，请稍后再试")

def revoke_access_token(token: str) -> bool:
    """
    吊销访问令牌（添加到黑名单）
    :param token: 访问令牌
    :return: 是否成功
    """
    _revoked_tokens.add(token)
    logger.info("访问令牌已吊销")
    return True

def cleanup_revoked_tokens() -> int:
    """清理过期的吊销令牌记录"""
    # 实际实现应该根据token的exp时间清理
    # 这里简化处理，定期清理
    count = len(_revoked_tokens)
    _revoked_tokens.clear()
    if count > 0:
        logger.info(f"清理了 {count} 个吊销令牌记录")
    return count


def refresh_access_token(refresh_token: str) -> dict[str, str]:
    """
    使用刷新令牌获取新的访问令牌
    :param refresh_token: 刷新令牌
    :return: 新的access_token
    """
    # 验证刷新令牌
    try:
        payload = decode_token(refresh_token, require_access_token=False)
    except HTTPException as e:
        logger.warning(f"刷新令牌无效: {e.detail}")
        raise
    
    # 检查令牌类型
    if payload.get("token_type") != "refresh":
        logger.warning("无效的令牌类型")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌类型")
    
    # 检查存储的刷新令牌
    stored_token = _refresh_tokens.get(refresh_token)
    if not stored_token:
        logger.warning("刷新令牌未找到")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效")
    
    # 验证JTI（防止token reuse）
    if stored_token["jti"] != payload.get("jti"):
        logger.warning("JTI不匹配")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌验证失败")
    
    user_id = payload["user_id"]
    email = payload["email"]
    
    # 删除旧的刷新令牌
    del _refresh_tokens[refresh_token]
    
    # 签发新令牌
    return issue_tokens(user_id, email)


def revoke_refresh_token(refresh_token: str) -> bool:
    """
    撤销刷新令牌
    :param refresh_token: 刷新令牌
    :return: 是否成功撤销
    """
    if refresh_token in _refresh_tokens:
        del _refresh_tokens[refresh_token]
        logger.info("刷新令牌已撤销")
        return True
    return False


def revoke_all_user_tokens(user_id: int) -> int:
    """
    撤销用户的所有刷新令牌
    :param user_id: 用户ID
    :return: 撤销的令牌数量
    """
    count = 0
    tokens_to_remove = []
    
    for token, data in _refresh_tokens.items():
        if data["user_id"] == user_id:
            tokens_to_remove.append(token)
            count += 1
    
    for token in tokens_to_remove:
        del _refresh_tokens[token]
    
    if count > 0:
        logger.info(f"用户 {user_id} 的 {count} 个令牌已撤销")
    
    return count


def get_current_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    """获取当前请求的令牌"""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return credentials.credentials


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    :param password: 密码
    :return: (是否通过, 错误信息)
    """
    if len(password) < 8:
        return False, "密码长度至少需要8位"
    
    if not any(c.isupper() for c in password):
        return False, "密码需要包含至少一个大写字母"
    
    if not any(c.islower() for c in password):
        return False, "密码需要包含至少一个小写字母"
    
    if not any(c.isdigit() for c in password):
        return False, "密码需要包含至少一个数字"
    
    return True, "密码强度符合要求"


def generate_secure_token(length: int = 32) -> str:
    """生成安全的随机令牌"""
    return base64.urlsafe_b64encode(os.urandom(length)).decode("utf-8").rstrip("=")


def cleanup_expired_refresh_tokens() -> int:
    """清理过期的刷新令牌"""
    now = int(time.time())
    expired_tokens = []
    
    for token, data in _refresh_tokens.items():
        if data["expires_at"] < now:
            expired_tokens.append(token)
    
    for token in expired_tokens:
        del _refresh_tokens[token]
    
    if expired_tokens:
        logger.info(f"清理了 {len(expired_tokens)} 个过期刷新令牌")
    
    return len(expired_tokens)