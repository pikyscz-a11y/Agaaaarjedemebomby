"""
NOWPayments integration for USDT deposits and payouts.
Handles 1:1 USDT to credits conversion with secure webhook validation.
"""

import hashlib
import hmac
import json
import logging
import os
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

from models import DepositRequest, DepositResponse, PayoutRequest, PayoutResponse, Transaction

logger = logging.getLogger(__name__)

class NOWPaymentsConfig:
    """NOWPayments configuration"""
    API_KEY = os.getenv('NOWPAYMENTS_API_KEY', '')
    IPN_SECRET = os.getenv('NOWPAYMENTS_IPN_SECRET', '')
    SANDBOX = os.getenv('NOWPAYMENTS_SANDBOX', 'true').lower() == 'true'
    BASE_URL = 'https://api-sandbox.nowpayments.io' if SANDBOX else 'https://api.nowpayments.io'
    MIN_DEPOSIT = float(os.getenv('MIN_DEPOSIT_AMOUNT', '1.0'))
    MAX_DEPOSIT = float(os.getenv('MAX_DEPOSIT_AMOUNT', '10000.0'))
    MIN_PAYOUT = float(os.getenv('MIN_PAYOUT_AMOUNT', '10.0'))
    PAYOUT_FEE_PERCENTAGE = float(os.getenv('PAYOUT_FEE_PERCENTAGE', '2.5'))

class PaymentStatus:
    """Payment status constants"""
    WAITING = 'waiting'
    CONFIRMING = 'confirming' 
    CONFIRMED = 'confirmed'
    SENDING = 'sending'
    PARTIALLY_PAID = 'partially_paid'
    FINISHED = 'finished'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    EXPIRED = 'expired'

class PayoutStatus:
    """Payout status constants"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

class NOWPaymentsClient:
    """NOWPayments API client"""
    
    def __init__(self):
        self.config = NOWPaymentsConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.BASE_URL,
            headers={
                'x-api-key': self.config.API_KEY,
                'Content-Type': 'application/json'
            },
            timeout=30.0
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_status(self) -> Dict:
        """Get API status"""
        try:
            response = await self.client.get('/v1/status')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get API status: {e}")
            raise
    
    async def get_currencies(self) -> List[Dict]:
        """Get available currencies"""
        try:
            response = await self.client.get('/v1/currencies')
            response.raise_for_status()
            return response.json().get('currencies', [])
        except Exception as e:
            logger.error(f"Failed to get currencies: {e}")
            raise
    
    async def create_payment(self, deposit_request: DepositRequest, 
                           callback_url: str, success_url: str, 
                           cancel_url: str) -> DepositResponse:
        """Create a payment request"""
        try:
            # Validate amount
            if deposit_request.amount < self.config.MIN_DEPOSIT:
                raise ValueError(f"Minimum deposit is {self.config.MIN_DEPOSIT} USDT")
            if deposit_request.amount > self.config.MAX_DEPOSIT:
                raise ValueError(f"Maximum deposit is {self.config.MAX_DEPOSIT} USDT")
            
            # Prepare payment data
            payment_data = {
                'price_amount': deposit_request.amount,
                'price_currency': 'USDT',
                'pay_currency': deposit_request.currency,
                'order_id': f"deposit_{deposit_request.player_id}_{int(time.time())}",
                'order_description': f"Credit deposit for player {deposit_request.player_id}",
                'ipn_callback_url': callback_url,
                'success_url': success_url,
                'cancel_url': cancel_url,
                'is_fixed_rate': True,
                'is_fee_paid_by_user': False
            }
            
            # Add network specification for USDT
            if deposit_request.currency == 'USDT':
                payment_data['network'] = deposit_request.network
            
            logger.info(f"Creating payment for {deposit_request.amount} USDT")
            
            response = await self.client.post('/v1/payment', json=payment_data)
            response.raise_for_status()
            
            result = response.json()
            
            # Calculate expiration time (usually 24 hours)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            return DepositResponse(
                success=True,
                payment_id=result['payment_id'],
                invoice_url=result.get('invoice_url', ''),
                payment_address=result.get('pay_address', ''),
                amount=deposit_request.amount,
                currency=deposit_request.currency,
                status=PaymentStatus.WAITING,
                expires_at=expires_at,
                message="Payment created successfully"
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating payment: {e.response.text}")
            raise ValueError(f"Payment creation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise
    
    async def get_payment_status(self, payment_id: str) -> Dict:
        """Get payment status"""
        try:
            response = await self.client.get(f'/v1/payment/{payment_id}')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get payment status for {payment_id}: {e}")
            raise
    
    async def create_payout(self, payout_request: PayoutRequest) -> PayoutResponse:
        """Create a payout request"""
        try:
            # Validate amount
            if payout_request.amount < self.config.MIN_PAYOUT:
                raise ValueError(f"Minimum payout is {self.config.MIN_PAYOUT} USDT")
            
            # Calculate fees
            fee = (payout_request.amount * self.config.PAYOUT_FEE_PERCENTAGE) / 100
            net_amount = payout_request.amount - fee
            
            # Prepare payout data
            payout_data = {
                'address': payout_request.wallet_address,
                'currency': 'USDT',
                'amount': net_amount,
                'ipn_callback_url': payout_request.callback_url,
                'extra_id': f"payout_{payout_request.player_id}_{int(time.time())}"
            }
            
            # Add network for USDT
            if payout_request.network:
                payout_data['network'] = payout_request.network
            
            logger.info(f"Creating payout for {net_amount} USDT (fee: {fee})")
            
            response = await self.client.post('/v1/payout', json=payout_data)
            response.raise_for_status()
            
            result = response.json()
            
            return PayoutResponse(
                success=True,
                payout_id=result['id'],
                amount=payout_request.amount,
                fee=fee,
                net_amount=net_amount,
                status=PayoutStatus.PENDING,
                message="Payout request created successfully"
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating payout: {e.response.text}")
            raise ValueError(f"Payout creation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating payout: {e}")
            raise
    
    async def get_payout_status(self, payout_id: str) -> Dict:
        """Get payout status"""
        try:
            response = await self.client.get(f'/v1/payout/{payout_id}')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get payout status for {payout_id}: {e}")
            raise

class WebhookValidator:
    """Validates NOWPayments webhooks using HMAC"""
    
    @staticmethod
    def validate_webhook(payload: str, signature: str, secret: str) -> bool:
        """Validate webhook signature"""
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False

class PaymentManager:
    """Manages payment operations and database updates"""
    
    def __init__(self, database):
        self.database = database
        self.config = NOWPaymentsConfig()
    
    async def create_deposit(self, player_id: str, amount: float, 
                           currency: str = 'USDT', network: str = 'TRC20') -> DepositResponse:
        """Create a new deposit request"""
        try:
            deposit_request = DepositRequest(
                player_id=player_id,
                amount=amount,
                currency=currency,
                network=network
            )
            
            # Generate URLs
            base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            callback_url = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/payments/webhook"
            success_url = f"{base_url}/payment/success"
            cancel_url = f"{base_url}/payment/cancel"
            
            async with NOWPaymentsClient() as client:
                deposit_response = await client.create_payment(
                    deposit_request, callback_url, success_url, cancel_url
                )
            
            # Store transaction in database
            transaction = Transaction(
                playerId=player_id,
                type='deposit',
                amount=amount,
                currency=currency,
                status='pending',
                payment_id=deposit_response.payment_id,
                network=network,
                description=f"USDT deposit via {network}"
            )
            
            await self.database.create_transaction(transaction)
            
            logger.info(f"Created deposit for player {player_id}: {amount} {currency}")
            return deposit_response
            
        except Exception as e:
            logger.error(f"Error creating deposit: {e}")
            raise
    
    async def process_webhook(self, payload: Dict, signature: str) -> bool:
        """Process payment webhook from NOWPayments"""
        try:
            # Validate webhook signature
            payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            if not WebhookValidator.validate_webhook(payload_str, signature, self.config.IPN_SECRET):
                logger.warning("Invalid webhook signature")
                return False
            
            payment_id = payload.get('payment_id')
            payment_status = payload.get('payment_status')
            
            if not payment_id:
                logger.warning("Webhook missing payment_id")
                return False
            
            # Find transaction in database
            transactions = await self.database.get_transactions_by_payment_id(payment_id)
            if not transactions:
                logger.warning(f"No transaction found for payment_id: {payment_id}")
                return False
            
            transaction = transactions[0]
            
            # Update transaction status
            await self.database.update_transaction_status(transaction.id, payment_status)
            
            # Process based on status
            if payment_status == PaymentStatus.FINISHED:
                await self._credit_player_account(transaction)
            elif payment_status in [PaymentStatus.FAILED, PaymentStatus.EXPIRED, PaymentStatus.REFUNDED]:
                await self._handle_failed_payment(transaction)
            
            logger.info(f"Processed webhook for payment {payment_id}: {payment_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False
    
    async def _credit_player_account(self, transaction: Transaction):
        """Credit player account after successful payment"""
        try:
            # Get player
            player = await self.database.get_player(transaction.playerId)
            if not player:
                logger.error(f"Player not found: {transaction.playerId}")
                return
            
            # Add credits (1:1 USDT ratio)
            new_credits = player.credits + transaction.amount
            
            await self.database.update_player(transaction.playerId, {
                'credits': new_credits
            })
            
            # Update transaction as completed
            await self.database.update_transaction_status(transaction.id, 'completed')
            
            logger.info(f"Credited {transaction.amount} USDT to player {transaction.playerId}")
            
        except Exception as e:
            logger.error(f"Error crediting player account: {e}")
    
    async def _handle_failed_payment(self, transaction: Transaction):
        """Handle failed payment"""
        try:
            # Update transaction status
            await self.database.update_transaction_status(transaction.id, 'failed')
            
            # TODO: Send notification to player
            logger.info(f"Payment failed for transaction {transaction.id}")
            
        except Exception as e:
            logger.error(f"Error handling failed payment: {e}")
    
    async def create_payout_request(self, player_id: str, amount: float,
                                  wallet_address: str, network: str = 'TRC20') -> PayoutResponse:
        """Create a payout request"""
        try:
            # Get player and validate balance
            player = await self.database.get_player(player_id)
            if not player:
                raise ValueError("Player not found")
            
            if player.credits < amount:
                raise ValueError("Insufficient credits")
            
            if amount < self.config.MIN_PAYOUT:
                raise ValueError(f"Minimum payout is {self.config.MIN_PAYOUT} USDT")
            
            # Calculate fee
            fee = (amount * self.config.PAYOUT_FEE_PERCENTAGE) / 100
            net_amount = amount - fee
            
            # Create payout request in database
            transaction = Transaction(
                playerId=player_id,
                type='payout_request',
                amount=amount,
                currency='USDT',
                status='pending',
                network=network,
                wallet_address=wallet_address,
                fee=fee,
                description=f"Payout request to {wallet_address}",
                metadata={'requires_approval': True}
            )
            
            await self.database.create_transaction(transaction)
            
            # Reserve credits (deduct from available balance)
            await self.database.update_player(player_id, {
                'credits': player.credits - amount
            })
            
            logger.info(f"Created payout request for player {player_id}: {amount} USDT")
            
            return PayoutResponse(
                success=True,
                payout_id=transaction.id,
                amount=amount,
                fee=fee,
                net_amount=net_amount,
                status=PayoutStatus.PENDING,
                message="Payout request created and pending admin approval"
            )
            
        except Exception as e:
            logger.error(f"Error creating payout request: {e}")
            raise
    
    async def approve_payout(self, payout_id: str, admin_id: str) -> bool:
        """Approve a payout request (admin action)"""
        try:
            # Get transaction
            transaction = await self.database.get_transaction(payout_id)
            if not transaction or transaction.type != 'payout_request':
                raise ValueError("Payout request not found")
            
            if transaction.status != 'pending':
                raise ValueError("Payout request is not pending")
            
            # Create actual payout via NOWPayments
            payout_request = PayoutRequest(
                player_id=transaction.playerId,
                amount=transaction.amount - transaction.fee,  # Net amount
                wallet_address=transaction.wallet_address,
                network=transaction.network
            )
            
            async with NOWPaymentsClient() as client:
                payout_response = await client.create_payout(payout_request)
            
            # Update transaction with NOWPayments payout ID
            await self.database.update_transaction(payout_id, {
                'status': 'approved',
                'payment_id': payout_response.payout_id,
                'metadata': {
                    **transaction.metadata,
                    'approved_by': admin_id,
                    'approved_at': datetime.utcnow().isoformat()
                }
            })
            
            logger.info(f"Approved payout {payout_id} by admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving payout: {e}")
            raise
    
    async def reject_payout(self, payout_id: str, admin_id: str, reason: str) -> bool:
        """Reject a payout request (admin action)"""
        try:
            # Get transaction
            transaction = await self.database.get_transaction(payout_id)
            if not transaction or transaction.type != 'payout_request':
                raise ValueError("Payout request not found")
            
            if transaction.status != 'pending':
                raise ValueError("Payout request is not pending")
            
            # Refund credits to player
            player = await self.database.get_player(transaction.playerId)
            if player:
                await self.database.update_player(transaction.playerId, {
                    'credits': player.credits + transaction.amount
                })
            
            # Update transaction
            await self.database.update_transaction(payout_id, {
                'status': 'rejected',
                'metadata': {
                    **transaction.metadata,
                    'rejected_by': admin_id,
                    'rejected_at': datetime.utcnow().isoformat(),
                    'rejection_reason': reason
                }
            })
            
            logger.info(f"Rejected payout {payout_id} by admin {admin_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting payout: {e}")
            raise
    
    async def get_payment_status(self, payment_id: str) -> Optional[Dict]:
        """Get payment status from NOWPayments"""
        try:
            async with NOWPaymentsClient() as client:
                return await client.get_payment_status(payment_id)
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return None

# Global payment manager instance (to be initialized with database)
payment_manager = None

def initialize_payment_manager(database):
    """Initialize payment manager with database"""
    global payment_manager
    payment_manager = PaymentManager(database)