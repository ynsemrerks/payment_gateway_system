"""Security utilities for authentication and webhook verification."""
import hmac
import hashlib
import secrets
from typing import Optional
from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.config import settings


def generate_api_key() -> str:
    """Generate a random API key."""
    return secrets.token_urlsafe(32)


def verify_api_key(
    db: Session,
    api_key: str = Header(..., alias=settings.API_KEY_HEADER)
) -> User:
    """
    Verify API key and return user.
    
    Args:
        db: Database session
        api_key: API key from header
        
    Returns:
        User object
        
    Raises:
        HTTPException: If API key is invalid
    """
    user = db.query(User).filter(User.api_key == api_key).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user


def generate_webhook_signature(payload: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.
    
    Args:
        payload: Webhook payload as string
        
    Returns:
        Hex-encoded signature
    """
    signature = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_webhook_signature(payload: str, signature: str) -> bool:
    """
    Verify webhook signature.
    
    Args:
        payload: Webhook payload as string (raw JSON)
        signature: Signature to verify
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Parse JSON to handle whitespace differences and remove signature
        import json
        payload_dict = json.loads(payload)
        
        # Remove signature from payload if present
        payload_dict.pop('signature', None)
        
        # Canonicalize payload: sort keys, no spaces
        canonical_payload = json.dumps(
            payload_dict,
            separators=(',', ':'),
            sort_keys=True
        )
        
        expected_signature = generate_webhook_signature(canonical_payload)
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        # If payload is not valid JSON or other error
        return False
