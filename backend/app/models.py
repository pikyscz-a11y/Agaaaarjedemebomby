from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base
import uuid


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(255), default="default.png")
    color = Column(String(7), default="#4A90E2")  # Hex color
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    balances = relationship("Balance", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    payouts = relationship("Payout", back_populates="user")


class Balance(Base):
    __tablename__ = "balances"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    amount = Column(Integer, default=0)  # Amount in cents/smallest unit
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="balances")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)  # 'deposit', 'withdrawal', 'entry_fee', 'payout'
    amount = Column(Integer, nullable=False)  # Amount in cents
    ref = Column(String(255))  # External reference (payment ID, etc.)
    status = Column(String(20), default="pending")  # 'pending', 'completed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")


class Payout(Base):
    __tablename__ = "payouts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in cents
    address = Column(String(255), nullable=False)  # USDT wallet address
    status = Column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="payouts")


class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    mode = Column(String(20), nullable=False)  # 'classic', 'fast', 'hardcore'
    entry_fee = Column(Integer, nullable=False)  # Amount in cents
    active = Column(Boolean, default=True)
    max_players = Column(Integer, default=20)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    
    # Game state (stored as JSON-like text for simplicity)
    game_state = Column(Text)  # JSON string of current game state