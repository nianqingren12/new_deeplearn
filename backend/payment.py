from __future__ import annotations

import os
import stripe
from typing import Any, Dict

from backend.db import create_order, get_user_by_id, utc_now


# 支付配置
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "sk_test_your_key")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_your_secret")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "pk_test_your_key")

# 初始化Stripe
stripe.api_key = STRIPE_API_KEY


class PaymentProcessor:
    """支付处理器"""
    
    @staticmethod
    def create_payment_intent(user_id: int, amount: float, product_type: str) -> Dict[str, Any]:
        """创建支付意图"""
        user = get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 创建订单
        order = create_order(user_id, product_type, amount, valid_days=30)
        
        # 创建Stripe支付意图
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # 转换为分
            currency="cny",
            metadata={
                "user_id": str(user_id),
                "order_id": str(order["id"]),
                "product_type": product_type
            },
            automatic_payment_methods={
                "enabled": True,
            },
        )
        
        return {
            "client_secret": intent.client_secret,
            "public_key": STRIPE_PUBLIC_KEY,
            "order": order
        }
    
    @staticmethod
    def handle_webhook(event: Dict[str, Any]) -> Dict[str, Any]:
        """处理Stripe webhook"""
        # 验证webhook签名
        # 注意：生产环境中应该验证签名
        
        event_type = event.get("type")
        
        if event_type == "payment_intent.succeeded":
            # 支付成功
            payment_intent = event["data"]["object"]
            user_id = int(payment_intent["metadata"].get("user_id"))
            order_id = int(payment_intent["metadata"].get("order_id"))
            
            # 更新订单状态
            # 这里可以添加更新订单状态的逻辑
            
            return {"status": "success", "message": "支付成功"}
        
        elif event_type == "payment_intent.payment_failed":
            # 支付失败
            return {"status": "error", "message": "支付失败"}
        
        return {"status": "ignored", "message": "未处理的事件类型"}
    
    @staticmethod
    def create_refund(payment_intent_id: str, amount: float) -> Dict[str, Any]:
        """创建退款"""
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=int(amount * 100),  # 转换为分
        )
        
        return {
            "refund_id": refund.id,
            "status": refund.status,
            "amount": refund.amount / 100
        }


def get_payment_config() -> Dict[str, Any]:
    """获取支付配置"""
    return {
        "public_key": STRIPE_PUBLIC_KEY,
        "currency": "cny",
        "supported_methods": ["alipay", "wechat_pay", "card"]
    }
