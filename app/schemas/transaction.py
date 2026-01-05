"""Transaction schemas for API requests and responses."""
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.models.transaction import TransactionType, TransactionStatus


class TransactionBase(BaseModel):
    """Base transaction schema."""
    amount: Decimal = Field(gt=0, decimal_places=2, description="Transaction amount (must be positive)")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class DepositCreate(TransactionBase):
    """Schema for creating a deposit."""
    pass


class WithdrawalCreate(TransactionBase):
    """Schema for creating a withdrawal."""
    pass


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    user_id: int
    type: TransactionType
    status: TransactionStatus
    amount: Decimal = Field(decimal_places=2)
    bank_reference: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DepositResponse(TransactionResponse):
    """Schema for deposit response."""
    pass


class WithdrawalResponse(TransactionResponse):
    """Schema for withdrawal response."""
    pass


class WebhookPayload(BaseModel):
    """Schema for bank webhook callback."""
    transaction_id: int
    bank_reference: str
    status: str  # "success" or "failed"
    error_message: Optional[str] = None
    signature: str
