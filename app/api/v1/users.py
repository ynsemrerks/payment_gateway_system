"""User API endpoints."""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.transaction import TransactionStatus, TransactionType
from app.schemas.user import UserBalance
from app.schemas.transaction import TransactionResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.transaction_service import transaction_service
from app.api.deps import get_current_user, check_user_rate_limit
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/{user_id}/balance",
    response_model=UserBalance,
    summary="Get user balance",
    description="Get current balance for a user (rate limited: 10 req/min)"
)
async def get_user_balance(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get user balance with rate limiting."""
    # Check authorization
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check rate limit
    check_user_rate_limit(
        user=current_user,
        endpoint="balance",
        limit=settings.RATE_LIMIT_BALANCE_PER_MIN
    )
    
    return UserBalance(
        user_id=current_user.id,
        balance=current_user.balance
    )


@router.get(
    "/{user_id}/transactions",
    response_model=PaginatedResponse[TransactionResponse],
    summary="Get user transaction history",
    description="Get transaction history for a user with filtering (rate limited: 20 req/min)"
)
async def get_user_transactions(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends()],
    status_filter: Optional[TransactionStatus] = Query(None, alias="status"),
    type_filter: Optional[TransactionType] = Query(None, alias="type")
):
    """Get user transaction history with pagination and filtering."""
    # Check authorization
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check rate limit
    check_user_rate_limit(
        user=current_user,
        endpoint="transactions",
        limit=settings.RATE_LIMIT_TRANSACTIONS_PER_MIN
    )
    
    transactions, total = transaction_service.list_transactions(
        db=db,
        user_id=user_id,
        status=status_filter,
        transaction_type=type_filter,
        limit=pagination.limit,
        offset=pagination.offset
    )
    
    items = [TransactionResponse.model_validate(t) for t in transactions]
    
    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        has_more=(pagination.offset + pagination.limit) < total
    )
