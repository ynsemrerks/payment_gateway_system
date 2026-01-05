"""Celery tasks for webhook processing."""
import logging
from app.tasks.celery_app import celery_app
from app.tasks.transaction_tasks import DatabaseTask
from app.models.transaction import TransactionStatus
from app.services.transaction_service import transaction_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=DatabaseTask)
def process_webhook_task(self, transaction_id: int, bank_reference: str, status: str, error_message: str = None):
    """
    Process bank webhook callback asynchronously.
    
    Args:
        transaction_id: Transaction ID
        bank_reference: Bank reference number
        status: Transaction status ("success" or "failed")
        error_message: Error message if failed
    """
    logger.info(f"Processing webhook for transaction {transaction_id}")
    
    try:
        # Get transaction
        transaction = transaction_service.get_transaction(self.db, transaction_id)
        
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return
        
        # Check if already in final state
        if transaction.status in [TransactionStatus.SUCCESS, TransactionStatus.FAILED]:
            logger.info(f"Transaction {transaction_id} already in final state: {transaction.status}")
            return
        
        # Update based on webhook status
        if status == "success":
            new_status = TransactionStatus.SUCCESS
            
            # Update user balance based on transaction type
            if transaction.type.value == "deposit":
                transaction_service.update_user_balance(
                    self.db,
                    transaction.user_id,
                    transaction.amount,
                    operation="add"
                )
            elif transaction.type.value == "withdrawal":
                transaction_service.update_user_balance(
                    self.db,
                    transaction.user_id,
                    transaction.amount,
                    operation="subtract"
                )
            
            logger.info(f"Webhook: Transaction {transaction_id} marked as success")
            
        else:
            new_status = TransactionStatus.FAILED
            logger.info(f"Webhook: Transaction {transaction_id} marked as failed")
        
        # Update transaction
        transaction_service.update_transaction_status(
            self.db,
            transaction_id,
            new_status,
            bank_reference=bank_reference,
            error_message=error_message
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook for transaction {transaction_id}: {str(e)}", exc_info=True)
        raise
