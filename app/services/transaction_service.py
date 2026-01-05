"""Transaction service for business logic."""
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
import json

from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.user import User
from app.models.idempotency import IdempotencyKey
from app.schemas.transaction import DepositCreate, WithdrawalCreate


class InsufficientBalanceError(Exception):
    """Raised when user has insufficient balance for withdrawal."""
    pass


class TransactionService:
    """Service for transaction business logic."""
    
    @staticmethod
    def check_idempotency_key(
        db: Session,
        user_id: int,
        idempotency_key: str
    ) -> Optional[IdempotencyKey]:
        """
        Check if idempotency key exists for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            idempotency_key: Idempotency key to check
            
        Returns:
            IdempotencyKey if exists, None otherwise
        """
        return db.query(IdempotencyKey).filter(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.key == idempotency_key
        ).first()
    
    @staticmethod
    def save_idempotency_key(
        db: Session,
        user_id: int,
        idempotency_key: str,
        status_code: int,
        response_body: dict
    ) -> IdempotencyKey:
        """
        Save idempotency key with response for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            idempotency_key: Idempotency key
            status_code: HTTP status code
            response_body: Response body as dict
            
        Returns:
            Created IdempotencyKey
        """
        idem_key = IdempotencyKey(
            user_id=user_id,
            key=idempotency_key,
            response_status=status_code,
            response_body=json.dumps(response_body)
        )
        db.add(idem_key)
        db.commit()
        db.refresh(idem_key)
        return idem_key

    @staticmethod
    def cleanup_old_idempotency_keys(
        db: Session,
        hours: int = 24
    ) -> int:
        """
        Clean up idempotency keys older than specified hours.
        
        Args:
            db: Database session
            hours: Retention period in hours
            
        Returns:
            Number of keys deleted
        """
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        deleted = db.query(IdempotencyKey).filter(
            IdempotencyKey.created_at < cutoff
        ).delete()
        
        db.commit()
        return deleted
    
    @staticmethod
    def create_deposit(
        db: Session,
        user_id: int,
        deposit_data: DepositCreate,
        idempotency_key: str
    ) -> Transaction:
        """
        Create a new deposit transaction.
        
        Args:
            db: Database session
            user_id: User ID
            deposit_data: Deposit data
            idempotency_key: Idempotency key
            
        Returns:
            Created transaction
        """
        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            amount=deposit_data.amount,
            idempotency_key=idempotency_key
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    
    @staticmethod
    def create_withdrawal(
        db: Session,
        user_id: int,
        withdrawal_data: WithdrawalCreate,
        idempotency_key: str
    ) -> Transaction:
        """
        Create a new withdrawal transaction.
        
        Args:
            db: Database session
            user_id: User ID
            withdrawal_data: Withdrawal data
            idempotency_key: Idempotency key
            
        Returns:
            Created transaction
            
        Raises:
            InsufficientBalanceError: If user has insufficient balance
        """
        # Check user balance with row lock
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if user.balance < withdrawal_data.amount:
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: {user.balance}, Required: {withdrawal_data.amount}"
            )
        
        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAWAL,
            status=TransactionStatus.PENDING,
            amount=withdrawal_data.amount,
            idempotency_key=idempotency_key
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    
    @staticmethod
    def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""
        return db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    @staticmethod
    def list_transactions(
        db: Session,
        user_id: Optional[int] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Transaction], int]:
        """
        List transactions with filtering and pagination.
        
        Returns:
            Tuple of (transactions, total_count)
        """
        query = db.query(Transaction)
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        if status:
            query = query.filter(Transaction.status == status)
        
        total = query.count()
        transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        
        return transactions, total
    
    @staticmethod
    def update_transaction_status(
        db: Session,
        transaction_id: int,
        status: TransactionStatus,
        bank_reference: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Transaction:
        """
        Update transaction status.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            status: New status
            bank_reference: Bank reference (optional)
            error_message: Error message (optional)
            
        Returns:
            Updated transaction
        """
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).with_for_update().first()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        transaction.status = status
        if bank_reference:
            transaction.bank_reference = bank_reference
        if error_message:
            transaction.error_message = error_message
        
        db.commit()
        db.refresh(transaction)
        return transaction
    
    @staticmethod
    def update_user_balance(
        db: Session,
        user_id: int,
        amount: Decimal,
        operation: str  # "add" or "subtract"
    ) -> User:
        """
        Update user balance with locking.
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to add or subtract
            operation: "add" or "subtract"
            
        Returns:
            Updated user
        """
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if operation == "add":
            user.balance += amount
        elif operation == "subtract":
            if user.balance < amount:
                raise InsufficientBalanceError(
                    f"Insufficient balance. Available: {user.balance}, Required: {amount}"
                )
            user.balance -= amount
        else:
            raise ValueError(f"Invalid operation: {operation}")
        
        db.commit()
        db.refresh(user)
        return user


# Global transaction service instance
transaction_service = TransactionService()
