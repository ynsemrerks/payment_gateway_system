"""User schemas for API requests and responses."""
from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr


class UserBalance(BaseModel):
    """Schema for user balance response."""
    user_id: int
    balance: Decimal = Field(decimal_places=2)
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    balance: Decimal = Field(decimal_places=2)
    created_at: datetime
    
    class Config:
        from_attributes = True
