"""Transaction model for tracking deposits and withdrawals."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from decimal import Decimal

from app.database import Base


class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class Transaction(Base):
    """Transaction model for deposits and withdrawals."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING, index=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    bank_reference = Column(String(255), nullable=True, unique=True)
    error_message = Column(Text, nullable=True)
    idempotency_key = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transaction_user_id', 'user_id'),
        Index('idx_transaction_status', 'status'),
        Index('idx_transaction_created_at', 'created_at'),
        Index('idx_transaction_idempotency_key', 'idempotency_key'),
        Index('idx_transaction_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.type}, status={self.status}, amount={self.amount})>"
