from __future__ import annotations

import os
import hashlib
import time
from typing import Any, Dict, List

from backend.db import get_connection, utc_now


class APIManager:
    """API管理类"""
    
    @staticmethod
    def generate_api_key(user_id: int) -> str:
        """生成API密钥"""
        timestamp = str(int(time.time()))
        random_str = os.urandom(16).hex()
        seed = f"{user_id}_{timestamp}_{random_str}"
        api_key = hashlib.sha256(seed.encode()).hexdigest()
        
        # 存储API密钥
        APIManager._save_api_key(user_id, api_key)
        
        return api_key
    
    @staticmethod
    def _save_api_key(user_id: int, api_key: str) -> None:
        """保存API密钥到数据库"""
        from backend.db import DB_TYPE
        
        now = utc_now()
        sql = """
        INSERT INTO api_keys (user_id, api_key, created_at, last_used_at, status)
        VALUES (?, ?, ?, ?, ?)
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id, api_key, now, now, "active"))
            conn.commit()
    
    @staticmethod
    def validate_api_key(api_key: str) -> Dict[str, Any] | None:
        """验证API密钥"""
        from backend.db import DB_TYPE
        
        sql = """
        SELECT * FROM api_keys 
        WHERE api_key = ? AND status = 'active'
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_key,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 更新最后使用时间
            update_sql = """
            UPDATE api_keys 
            SET last_used_at = ? 
            WHERE api_key = ?
            """
            if DB_TYPE == "mysql":
                update_sql = update_sql.replace("?", "%s")
            
            cursor.execute(update_sql, (utc_now(), api_key))
            conn.commit()
            
            return dict(row) if isinstance(row, dict) else {
                "id": row[0],
                "user_id": row[1],
                "api_key": row[2],
                "created_at": row[3],
                "last_used_at": row[4],
                "status": row[5]
            }
    
    @staticmethod
    def get_user_api_keys(user_id: int) -> List[Dict[str, Any]]:
        """获取用户的API密钥列表"""
        from backend.db import DB_TYPE
        
        sql = """
        SELECT * FROM api_keys 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                if isinstance(row, dict):
                    result.append(row)
                else:
                    result.append({
                        "id": row[0],
                        "user_id": row[1],
                        "api_key": row[2],
                        "created_at": row[3],
                        "last_used_at": row[4],
                        "status": row[5]
                    })
            return result
    
    @staticmethod
    def revoke_api_key(api_key_id: int, user_id: int) -> bool:
        """撤销API密钥"""
        from backend.db import DB_TYPE
        
        sql = """
        UPDATE api_keys 
        SET status = 'revoked' 
        WHERE id = ? AND user_id = ?
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_key_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_api_usage(user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取API使用情况"""
        from backend.db import DB_TYPE
        
        sql = """
        SELECT COUNT(*) as count, 
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
               SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
        FROM api_logs 
        WHERE user_id = ? 
        AND created_at >= datetime('now', '-' || ? || ' days')
        """
        
        if DB_TYPE == "mysql":
            sql = """
            SELECT COUNT(*) as count, 
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                   SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM api_logs 
            WHERE user_id = %s 
            AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id, days))
            row = cursor.fetchone()
            
            if not row:
                return {"total_calls": 0, "success_calls": 0, "error_calls": 0}
            
            return {
                "total_calls": row["count"] if isinstance(row, dict) else row[0],
                "success_calls": row["success_count"] if isinstance(row, dict) else row[1],
                "error_calls": row["error_count"] if isinstance(row, dict) else row[2]
            }
    
    @staticmethod
    def log_api_call(user_id: int, endpoint: str, status: str, response_time: float) -> None:
        """记录API调用"""
        from backend.db import DB_TYPE
        
        now = utc_now()
        sql = """
        INSERT INTO api_logs (user_id, endpoint, status, response_time, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id, endpoint, status, response_time, now))
            conn.commit()


def init_api_tables() -> None:
    """初始化API相关表"""
    from backend.db import get_connection, DB_TYPE
    
    # 创建API密钥表
    api_keys_table = """
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        user_id INTEGER NOT NULL,
        api_key VARCHAR(255) UNIQUE NOT NULL,
        created_at DATETIME NOT NULL,
        last_used_at DATETIME NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'active'
    )
    """
    
    # 创建API日志表
    api_logs_table = """
    CREATE TABLE IF NOT EXISTS api_logs (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        user_id INTEGER NOT NULL,
        endpoint VARCHAR(255) NOT NULL,
        status VARCHAR(20) NOT NULL,
        response_time FLOAT NOT NULL,
        created_at DATETIME NOT NULL
    )
    """
    
    if DB_TYPE == "sqlite":
        api_keys_table = api_keys_table.replace("AUTO_INCREMENT", "AUTOINCREMENT").replace("DATETIME", "TEXT")
        api_logs_table = api_logs_table.replace("AUTO_INCREMENT", "AUTOINCREMENT").replace("DATETIME", "TEXT")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(api_keys_table)
        cursor.execute(api_logs_table)
        conn.commit()
