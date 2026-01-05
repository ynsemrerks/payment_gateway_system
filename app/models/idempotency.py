"""Idempotency key model for request deduplication."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class IdempotencyKey(Base):
    """Idempotency key model for preventing duplicate requests."""
    
    __tablename__ = "idempotency_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    response_status = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Ensure key is unique per user
    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='unique_user_idempotency_key'),
    )
    
    def __repr__(self):
        return f"<IdempotencyKey(user_id={self.user_id}, key={self.key}, status={self.response_status})>"
