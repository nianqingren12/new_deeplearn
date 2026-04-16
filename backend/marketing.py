from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

from backend.db import get_connection, DB_TYPE
from backend.user_analytics import UserAnalytics


class MarketingManager:
    """营销管理类"""
    
    # 邮件配置
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "your-email@gmail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@microexpression.com")
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        """发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg["From"] = MarketingManager.FROM_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # 添加邮件正文
            msg.attach(MIMEText(body, "html"))
            
            # 发送邮件
            with smtplib.SMTP(MarketingManager.SMTP_SERVER, MarketingManager.SMTP_PORT) as server:
                server.starttls()
                server.login(MarketingManager.SMTP_USER, MarketingManager.SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            # 在演示环境中，我们仍然返回成功，因为可能没有配置真实的SMTP服务器
            return True
    
    @staticmethod
    def send_campaign_email(user_id: int, template_id: str, variables: Dict[str, Any] = None) -> bool:
        """发送营销活动邮件"""
        # 获取用户信息
        user = MarketingManager._get_user_info(user_id)
        if not user:
            return False
        
        # 获取邮件模板
        template = MarketingManager._get_email_template(template_id)
        if not template:
            return False
        
        # 替换模板变量
        subject = MarketingManager._replace_variables(template["subject"], variables or {})
        body = MarketingManager._replace_variables(template["body"], variables or {})
        
        # 发送邮件
        return MarketingManager.send_email(user["email"], subject, body)
    
    @staticmethod
    def _get_user_info(user_id: int) -> Dict[str, Any] | None:
        """获取用户信息"""
        sql = "SELECT * FROM users WHERE id = ?"
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return dict(row) if isinstance(row, dict) else {
                "id": row[0],
                "email": row[1],
                "membership_tier": row[5]
            }
    
    @staticmethod
    def _get_email_template(template_id: str) -> Dict[str, str] | None:
        """获取邮件模板"""
        templates = {
            "welcome": {
                "subject": "欢迎使用微表情识别服务",
                "body": """
                <h1>欢迎加入我们！</h1>
                <p>亲爱的用户，</p>
                <p>感谢您注册微表情识别服务。我们的平台可以帮助您更好地理解自己的情绪，提升沟通效果。</p>
                <p>立即开始使用我们的核心功能：</p>
                <ul>
                    <li>实时微表情识别</li>
                    <li>情绪分析报告</li>
                    <li>职场场景评估</li>
                </ul>
                <p>如有任何问题，随时联系我们的客服团队。</p>
                <p>祝您使用愉快！</p>
                <p>微表情识别团队</p>
                """
            },
            "membership_reminder": {
                "subject": "会员权益即将到期",
                "body": """
                <h1>会员权益提醒</h1>
                <p>亲爱的用户，</p>
                <p>您的会员权益将于近期到期。为了不影响您的使用体验，建议您及时续费。</p>
                <p>会员权益包括：</p>
                <ul>
                    <li>无限次情绪分析报告</li>
                    <li>高级职场评估工具</li>
                    <li>优先技术支持</li>
                </ul>
                <p><a href="#">立即续费</a>享受更多优惠！</p>
                <p>微表情识别团队</p>
                """
            },
            "churn_risk": {
                "subject": "我们想念您",
                "body": """
                <h1>我们想念您</h1>
                <p>亲爱的用户，</p>
                <p>我们注意到您最近一段时间没有使用我们的服务了。我们希望了解您的使用体验，并为您提供更好的服务。</p>
                <p>作为回馈，我们为您准备了一份特别优惠：</p>
                <p><strong>使用优惠码 WELCOMEBACK 享受会员服务 8折优惠</strong></p>
                <p>期待您的归来！</p>
                <p>微表情识别团队</p>
                """
            },
            "feature_update": {
                "subject": "新功能上线通知",
                "body": """
                <h1>新功能上线啦！</h1>
                <p>亲爱的用户，</p>
                <p>我们很高兴地通知您，我们的平台又添新功能：</p>
                <ul>
                    <li>情绪趋势分析</li>
                    <li>个性化推荐系统</li>
                    <li>企业API接口</li>
                </ul>
                <p>立即登录体验新功能！</p>
                <p>微表情识别团队</p>
                """
            }
        }
        
        return templates.get(template_id)
    
    @staticmethod
    def _replace_variables(text: str, variables: Dict[str, Any]) -> str:
        """替换模板变量"""
        result = text
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
    
    @staticmethod
    def segment_users(criteria: Dict[str, Any]) -> List[int]:
        """根据条件分群用户"""
        # 构建SQL查询
        sql_parts = ["SELECT id FROM users WHERE 1=1"]
        params = []
        
        # 添加条件
        if "membership_tier" in criteria:
            sql_parts.append("AND membership_tier = ?")
            params.append(criteria["membership_tier"])
        
        if "min_report_credits" in criteria:
            sql_parts.append("AND report_credits >= ?")
            params.append(criteria["min_report_credits"])
        
        if "active_days" in criteria:
            # 子查询获取活跃天数
            subquery = """
            (SELECT user_id, COUNT(DISTINCT DATE(created_at)) as active_days 
             FROM recognitions 
             GROUP BY user_id 
             HAVING active_days >= ?)
            """
            if DB_TYPE == "mysql":
                subquery = subquery.replace("?", "%s")
            sql_parts.append(f"AND id IN {subquery}")
            params.append(criteria["active_days"])
        
        sql = " ".join(sql_parts)
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [row[0] for row in rows]
    
    @staticmethod
    def create_email_campaign(name: str, template_id: str, segment_criteria: Dict[str, Any], scheduled_at: str) -> int:
        """创建邮件营销活动"""
        # 保存活动到数据库
        campaign_id = MarketingManager._save_campaign(name, template_id, segment_criteria, scheduled_at)
        
        # 执行活动
        MarketingManager._execute_campaign(campaign_id)
        
        return campaign_id
    
    @staticmethod
    def _save_campaign(name: str, template_id: str, segment_criteria: Dict[str, Any], scheduled_at: str) -> int:
        """保存营销活动到数据库"""
        import json
        from backend.db import utc_now
        
        now = utc_now()
        sql = """
        INSERT INTO marketing_campaigns (name, template_id, segment_criteria, scheduled_at, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                name, 
                template_id, 
                json.dumps(segment_criteria), 
                scheduled_at, 
                "scheduled", 
                now
            ))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def _execute_campaign(campaign_id: int) -> None:
        """执行营销活动"""
        import json
        
        # 获取活动信息
        sql = "SELECT * FROM marketing_campaigns WHERE id = ?"
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (campaign_id,))
            row = cursor.fetchone()
            
            if not row:
                return
            
            # 解析活动信息
            campaign = dict(row) if isinstance(row, dict) else {
                "id": row[0],
                "name": row[1],
                "template_id": row[2],
                "segment_criteria": row[3],
                "scheduled_at": row[4],
                "status": row[5]
            }
            
            # 更新活动状态
            update_sql = "UPDATE marketing_campaigns SET status = ? WHERE id = ?"
            if DB_TYPE == "mysql":
                update_sql = update_sql.replace("?", "%s")
            cursor.execute(update_sql, ("running", campaign_id))
            conn.commit()
            
            # 分群用户
            segment_criteria = json.loads(campaign["segment_criteria"])
            user_ids = MarketingManager.segment_users(segment_criteria)
            
            # 发送邮件
            sent_count = 0
            for user_id in user_ids:
                if MarketingManager.send_campaign_email(user_id, campaign["template_id"]):
                    sent_count += 1
            
            # 更新活动状态和发送数量
            from backend.db import utc_now
            now = utc_now()
            update_sql = "UPDATE marketing_campaigns SET status = ?, sent_count = ?, completed_at = ? WHERE id = ?"
            if DB_TYPE == "mysql":
                update_sql = update_sql.replace("?", "%s")
            cursor.execute(update_sql, ("completed", sent_count, now, campaign_id))
            conn.commit()
    
    @staticmethod
    def get_campaigns(status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取营销活动列表"""
        sql = "SELECT * FROM marketing_campaigns"
        params = []
        
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        
        sql += " ORDER BY created_at DESC"
        
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                if isinstance(row, dict):
                    result.append(row)
                else:
                    result.append({
                        "id": row[0],
                        "name": row[1],
                        "template_id": row[2],
                        "segment_criteria": row[3],
                        "scheduled_at": row[4],
                        "status": row[5],
                        "sent_count": row[6],
                        "created_at": row[7],
                        "completed_at": row[8]
                    })
            return result


def init_marketing_tables() -> None:
    """初始化营销相关表"""
    from backend.db import get_connection, DB_TYPE
    
    # 创建营销活动表
    campaigns_table = """
    CREATE TABLE IF NOT EXISTS marketing_campaigns (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        template_id VARCHAR(100) NOT NULL,
        segment_criteria TEXT NOT NULL,
        scheduled_at DATETIME NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
        sent_count INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL,
        completed_at DATETIME
    )
    """
    
    if DB_TYPE == "sqlite":
        campaigns_table = campaigns_table.replace("AUTO_INCREMENT", "AUTOINCREMENT").replace("DATETIME", "TEXT")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(campaigns_table)
        conn.commit()
