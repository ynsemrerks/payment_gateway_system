"""Withdrawal API endpoints."""
import json
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.transaction import TransactionType
from app.schemas.transaction import WithdrawalCreate, WithdrawalResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.transaction_service import transaction_service, InsufficientBalanceError
from app.api.deps import get_current_user, get_idempotency_key
from app.tasks.transaction_tasks import process_withdrawal_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=WithdrawalResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a withdrawal",
    description="Create a new withdrawal transaction. Requires Idempotency-Key header."
)
async def create_withdrawal(
    withdrawal_data: WithdrawalCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    idempotency_key: Annotated[str, Depends(get_idempotency_key)],
    response: Response
):
    """
    Create a new withdrawal transaction.
    
    The transaction will be processed asynchronously. Use the returned transaction ID
    to check the status via GET /api/v1/withdrawals/{id}.
    """
    # Check idempotency key
    existing_key = transaction_service.check_idempotency_key(
        db=db,
        user_id=current_user.id,
        idempotency_key=idempotency_key
    )
    if existing_key:
        # Return cached response
        response.status_code = existing_key.response_status
        return json.loads(existing_key.response_body)
    
    try:
        # Create transaction (includes balance check)
        transaction = transaction_service.create_withdrawal(
            db=db,
            user_id=current_user.id,
            withdrawal_data=withdrawal_data,
            idempotency_key=idempotency_key
        )
        
        # Queue Celery task for async processing
        process_withdrawal_task.delay(transaction.id)
        
        # Prepare response
        response_data = WithdrawalResponse.model_validate(transaction)
        response_dict = response_data.model_dump(mode='json')
        
        # Save idempotency key
        transaction_service.save_idempotency_key(
            db=db,
            user_id=current_user.id,
            idempotency_key=idempotency_key,
            status_code=status.HTTP_202_ACCEPTED,
            response_body=response_dict
        )
        
        logger.info(f"Withdrawal transaction {transaction.id} created for user {current_user.id}")
        
        return response_data
        
    except InsufficientBalanceError as e:
        # Return 400 for insufficient balance
        error_response = {
            "error": "insufficient_balance",
            "message": str(e)
        }
        
        # Save idempotency key with error response
        transaction_service.save_idempotency_key(
            db=db,
            user_id=current_user.id,
            idempotency_key=idempotency_key,
            status_code=status.HTTP_400_BAD_REQUEST,
            response_body=error_response
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response
        )
        
    except Exception as e:
        logger.error(f"Error creating withdrawal: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create withdrawal transaction"
        )


@router.get(
    "/{transaction_id}",
    response_model=WithdrawalResponse,
    summary="Get withdrawal details",
    description="Get details of a specific withdrawal transaction"
)
async def get_withdrawal(
    transaction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get withdrawal transaction by ID."""
    transaction = transaction_service.get_transaction(db, transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Check ownership
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check transaction type
    if transaction.type != TransactionType.WITHDRAWAL:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction is not a withdrawal"
        )
    
    return WithdrawalResponse.model_validate(transaction)


@router.get(
    "",
    response_model=PaginatedResponse[WithdrawalResponse],
    summary="List withdrawals",
    description="List all withdrawal transactions for the current user with pagination"
)
async def list_withdrawals(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends()]
):
    """List withdrawal transactions with pagination."""
    transactions, total = transaction_service.list_transactions(
        db=db,
        user_id=current_user.id,
        transaction_type=TransactionType.WITHDRAWAL,
        limit=pagination.limit,
        offset=pagination.offset
    )
    
    items = [WithdrawalResponse.model_validate(t) for t in transactions]
    
    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        has_more=(pagination.offset + pagination.limit) < total
    )
