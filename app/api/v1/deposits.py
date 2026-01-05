"""Deposit API endpoints."""
import json
import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.transaction import TransactionType
from app.schemas.transaction import DepositCreate, DepositResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.transaction_service import transaction_service
from app.api.deps import get_current_user, get_idempotency_key
from app.tasks.transaction_tasks import process_deposit_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=DepositResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a deposit",
    description="Create a new deposit transaction. Requires Idempotency-Key header."
)
async def create_deposit(
    deposit_data: DepositCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    idempotency_key: Annotated[str, Depends(get_idempotency_key)],
    response: Response
):
    """
    Create a new deposit transaction.
    
    The transaction will be processed asynchronously. Use the returned transaction ID
    to check the status via GET /api/v1/deposits/{id}.
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
        # Create transaction
        transaction = transaction_service.create_deposit(
            db=db,
            user_id=current_user.id,
            deposit_data=deposit_data,
            idempotency_key=idempotency_key
        )
        
        # Queue Celery task for async processing
        process_deposit_task.delay(transaction.id)
        
        # Prepare response
        response_data = DepositResponse.model_validate(transaction)
        response_dict = response_data.model_dump(mode='json')
        
        # Save idempotency key
        transaction_service.save_idempotency_key(
            db=db,
            user_id=current_user.id,
            idempotency_key=idempotency_key,
            status_code=status.HTTP_202_ACCEPTED,
            response_body=response_dict
        )
        
        logger.info(f"Deposit transaction {transaction.id} created for user {current_user.id}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error creating deposit: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create deposit transaction"
        )


@router.get(
    "/{transaction_id}",
    response_model=DepositResponse,
    summary="Get deposit details",
    description="Get details of a specific deposit transaction"
)
async def get_deposit(
    transaction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get deposit transaction by ID."""
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
    if transaction.type != TransactionType.DEPOSIT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction is not a deposit"
        )
    
    return DepositResponse.model_validate(transaction)


@router.get(
    "",
    response_model=PaginatedResponse[DepositResponse],
    summary="List deposits",
    description="List all deposit transactions for the current user with pagination"
)
async def list_deposits(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends()]
):
    """List deposit transactions with pagination."""
    transactions, total = transaction_service.list_transactions(
        db=db,
        user_id=current_user.id,
        transaction_type=TransactionType.DEPOSIT,
        limit=pagination.limit,
        offset=pagination.offset
    )
    
    items = [DepositResponse.model_validate(t) for t in transactions]
    
    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        has_more=(pagination.offset + pagination.limit) < total
    )
