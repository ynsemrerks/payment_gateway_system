"""User model for storing user information and balance."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index
from sqlalchemy.sql import func
from decimal import Decimal

from app.database import Base


class User(Base):
    """User model with balance tracking."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    balance = Column(Numeric(precision=15, scale=2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_api_key', 'api_key'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, balance={self.balance})>"
