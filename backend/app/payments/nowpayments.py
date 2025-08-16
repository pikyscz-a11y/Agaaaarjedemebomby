import httpx
import hmac
import hashlib
import json
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ..config import settings
from ..models import User, Balance, Transaction


class NOWPaymentsAPI:
    """NOWPayments API integration for USDT deposits"""
    
    def __init__(self):
        self.api_key = settings.nowpayments_api_key
        self.ipn_secret = settings.nowpayments_ipn_secret
        self.api_url = settings.nowpayments_api_url
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_invoice(self, user_id: str, amount_usd: float) -> Dict:
        """Create a payment invoice for USDT deposit"""
        payload = {
            "price_amount": amount_usd,
            "price_currency": "usd",
            "pay_currency": "usdt",
            "order_id": f"deposit_{user_id}_{int(time.time())}",
            "order_description": f"USDT deposit for user {user_id}",
            "ipn_callback_url": f"{settings.public_base_url}/api/payments/ipn",
            "success_url": f"{settings.public_base_url}/deposit/success",
            "cancel_url": f"{settings.public_base_url}/deposit/cancel",
            "pay_currency_network": settings.usdt_network
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/payment",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to create invoice: {response.text}")
    
    def verify_ipn_signature(self, payload: str, received_signature: str) -> bool:
        """Verify IPN webhook signature"""
        calculated_signature = hmac.new(
            self.ipn_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(calculated_signature, received_signature)
    
    async def process_ipn_webhook(self, db: Session, payload: Dict, signature: str) -> bool:
        """Process IPN webhook for payment confirmation"""
        # Verify signature
        payload_str = json.dumps(payload, separators=(',', ':'))
        if not self.verify_ipn_signature(payload_str, signature):
            return False
        
        # Extract payment info
        payment_status = payload.get("payment_status")
        order_id = payload.get("order_id")
        amount_received = float(payload.get("actually_paid", 0))
        
        if payment_status != "finished":
            return False
        
        # Extract user_id from order_id
        if not order_id or not order_id.startswith("deposit_"):
            return False
        
        try:
            user_id = order_id.split("_")[1]
        except IndexError:
            return False
        
        # Find user and update balance
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Convert USDT to credits (1 USDT = 100 credits/cents)
        credit_amount = int(amount_received * 100)
        
        # Update user balance
        balance = db.query(Balance).filter(Balance.user_id == user_id).first()
        if balance:
            balance.amount += credit_amount
        else:
            balance = Balance(user_id=user_id, amount=credit_amount)
            db.add(balance)
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            type="deposit",
            amount=credit_amount,
            ref=order_id,
            status="completed"
        )
        db.add(transaction)
        
        db.commit()
        return True


# Import time at the top
import time
nowpayments = NOWPaymentsAPI()