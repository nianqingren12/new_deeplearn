from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


SECRET_KEY = os.getenv("APP_SECRET_KEY", "micro-expression-demo-secret")
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7
security = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> str:
    raw_salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), raw_salt.encode("utf-8"), 100_000)
    return f"{raw_salt}${base64.urlsafe_b64encode(digest).decode('utf-8')}"


def verify_password(password: str, stored_value: str) -> bool:
    try:
        salt, _ = stored_value.split("$", maxsplit=1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored_value)


def _encode_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("utf-8").rstrip("=")


def _decode_payload(token_payload: str) -> dict[str, Any]:
    padding = "=" * (-len(token_payload) % 4)
    decoded = base64.urlsafe_b64decode(f"{token_payload}{padding}")
    return json.loads(decoded.decode("utf-8"))


def issue_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    encoded_payload = _encode_payload(payload)
    signature = hmac.new(SECRET_KEY.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_token(token: str) -> dict[str, Any]:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌格式无效") from error

    expected_signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌签名无效")

    payload = _decode_payload(encoded_payload)
    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已过期")
    return payload


def get_current_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return credentials.credentials
