"""API dependencies for authentication and rate limiting."""
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.config import settings
from app.services.rate_limiter import rate_limiter

# Define the security scheme for Swagger UI
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    api_key: str = Depends(api_key_header)
) -> User:
    """
    Get current user from API key.
    
    Args:
        db: Database session
        api_key: API key from header (provided via Security Scheme)
        
    Returns:
        User object
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is missing"
        )

    user = db.query(User).filter(User.api_key == api_key).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user


def get_idempotency_key(
    idempotency_key: str = Header(..., alias="Idempotency-Key")
) -> str:
    """
    Get idempotency key from header.
    
    Args:
        idempotency_key: Idempotency key from header
        
    Returns:
        Idempotency key
        
    Raises:
        HTTPException: If idempotency key is missing
    """
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required"
        )
    
    return idempotency_key


def check_user_rate_limit(
    user: Annotated[User, Depends(get_current_user)],
    endpoint: str,
    limit: int
) -> None:
    """
    Check user-specific rate limit.
    
    Args:
        user: Current user
        endpoint: Endpoint name
        limit: Rate limit
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    key = f"user:{user.id}:{endpoint}"
    is_allowed, remaining, reset_timestamp, retry_after = rate_limiter.check_rate_limit(
        key=key,
        limit=limit,
        window_seconds=60
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_timestamp),
                "Retry-After": str(retry_after)
            }
        )
