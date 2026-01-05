"""Celery tasks for transaction processing."""
import logging
from decimal import Decimal
from celery import Task
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.transaction import Transaction, TransactionStatus
from app.services.bank_simulator import (
    bank_simulator,
    BankAPIError,
    BankTimeoutError,
    InsufficientFundsError,
    BankSystemUnavailableError
)
from app.services.transaction_service import transaction_service

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""
    
    _db: Session = None
    
    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    autoretry_for=(BankTimeoutError, BankSystemUnavailableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5
)
def process_deposit_task(self, transaction_id: int):
    """
    Process deposit transaction asynchronously.
    
    Args:
        transaction_id: Transaction ID to process
    """
    import asyncio
    logger.info(f"Processing deposit transaction {transaction_id}")
    
    try:
        # Get transaction
        transaction = transaction_service.get_transaction(self.db, transaction_id)
        
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return
        
        # Check if already processed
        if transaction.status in [TransactionStatus.SUCCESS, TransactionStatus.FAILED]:
            logger.info(f"Transaction {transaction_id} already processed with status {transaction.status}")
            return
        
        # Update status to processing
        transaction_service.update_transaction_status(
            self.db,
            transaction_id,
            TransactionStatus.PROCESSING
        )
        
        # Call bank API (run async function in sync context)
        try:
            result = asyncio.run(bank_simulator.process_deposit(
                amount=float(transaction.amount),
                user_id=transaction.user_id
            ))
            
            # Update transaction as success
            transaction_service.update_transaction_status(
                self.db,
                transaction_id,
                TransactionStatus.SUCCESS,
                bank_reference=result["bank_reference"]
            )
            
            # Update user balance
            transaction_service.update_user_balance(
                self.db,
                transaction.user_id,
                transaction.amount,
                operation="add"
            )
            
            logger.info(
                f"Deposit transaction {transaction_id} completed successfully. "
                f"Bank reference: {result['bank_reference']}"
            )
            
        except (BankTimeoutError, BankSystemUnavailableError) as e:
            # These errors trigger automatic retry
            logger.warning(f"Retryable error for transaction {transaction_id}: {str(e)}")
            # Reset to pending for retry
            transaction_service.update_transaction_status(
                self.db,
                transaction_id,
                TransactionStatus.PENDING,
                error_message=str(e)
            )
            raise  # Re-raise to trigger Celery retry
            
        except BankAPIError as e:
            # Non-retryable bank error
            logger.error(f"Bank error for transaction {transaction_id}: {str(e)}")
            transaction_service.update_transaction_status(
                self.db,
                transaction_id,
                TransactionStatus.FAILED,
                error_message=str(e)
            )
            
    except Exception as e:
        logger.error(f"Unexpected error processing transaction {transaction_id}: {str(e)}", exc_info=True)
        transaction_service.update_transaction_status(
            self.db,
            transaction_id,
            TransactionStatus.FAILED,
            error_message=f"Internal error: {str(e)}"
        )


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    autoretry_for=(BankTimeoutError, BankSystemUnavailableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5
)
def process_withdrawal_task(self, transaction_id: int):
    """
    Process withdrawal transaction asynchronously.
    
    Args:
        transaction_id: Transaction ID to process
    """
    import asyncio
    logger.info(f"Processing withdrawal transaction {transaction_id}")
    
    try:
        # Get transaction
        transaction = transaction_service.get_transaction(self.db, transaction_id)
        
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return
        
        # Check if already processed
        if transaction.status in [TransactionStatus.SUCCESS, TransactionStatus.FAILED]:
            logger.info(f"Transaction {transaction_id} already processed with status {transaction.status}")
            return
        
        # Update status to processing
        transaction_service.update_transaction_status(
            self.db,
            transaction_id,
            TransactionStatus.PROCESSING
        )
        
        # Call bank API (run async function in sync context)
        try:
            result = asyncio.run(bank_simulator.process_withdrawal(
                amount=float(transaction.amount),
                user_id=transaction.user_id
            ))
            
            # Update user balance first (with locking)
            transaction_service.update_user_balance(
                self.db,
                transaction.user_id,
                transaction.amount,
                operation="subtract"
            )
            
            # Update transaction as success
            transaction_service.update_transaction_status(
                self.db,
                transaction_id,
                TransactionStatus.SUCCESS,
                bank_reference=result["bank_reference"]
            )
            
            logger.info(
                f"Withdrawal transaction {transaction_id} completed successfully. "
                f"Bank reference: {result['bank_reference']}"
            )
            
        except (BankTimeoutError, BankSystemUnavailableError) as e:
            # These errors trigger automatic retry
            logger.warning(f"Retryable error for transaction {transaction_id}: {str(e)}")
            # Reset to pending for retry
            transaction_service.update_transaction_status(
                self.db,
                transaction_id,
                TransactionStatus.PENDING,
                error_message=str(e)
            )
            raise  # Re-raise to trigger Celery retry
            
        except (BankAPIError, InsufficientFundsError) as e:
            # Non-retryable errors
            logger.error(f"Bank error for transaction {transaction_id}: {str(e)}")
            transaction_service.update_transaction_status(
                self.db,
                transaction_id,
                TransactionStatus.FAILED,
                error_message=str(e)
            )
            
    except Exception as e:
        logger.error(f"Unexpected error processing transaction {transaction_id}: {str(e)}", exc_info=True)
        transaction_service.update_transaction_status(
            self.db,
            transaction_id,
            TransactionStatus.FAILED,
            error_message=f"Internal error: {str(e)}"
        )


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.transaction_tasks.cleanup_idempotency_keys_task"
)
def cleanup_idempotency_keys_task(self, hours: int = 24):
    """
    Periodic task to clean up old idempotency keys.
    """
    logger.info(f"Starting cleanup of idempotency keys older than {hours} hours")
    try:
        deleted_count = transaction_service.cleanup_old_idempotency_keys(self.db, hours)
        logger.info(f"Cleaned up {deleted_count} idempotency keys")
        return {"deleted": deleted_count}
    except Exception as e:
        logger.error(f"Error during idempotency key cleanup: {str(e)}", exc_info=True)
        raise
