"""Webhook API endpoints."""
import logging
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel

from app.schemas.transaction import WebhookPayload
from app.utils.security import verify_webhook_signature
from app.tasks.webhook_tasks import process_webhook_task

logger = logging.getLogger(__name__)
router = APIRouter()


class WebhookResponse(BaseModel):
    """Webhook response schema."""
    message: str
    transaction_id: int


@router.post(
    "/bank-callback",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Bank callback webhook",
    description="Endpoint for receiving bank transaction callbacks"
)
async def bank_callback(
    request: Request,
    payload: WebhookPayload
):
    """
    Handle bank callback webhook.
    
    Validates the webhook signature and queues the webhook for async processing.
    """
    # Get raw body for signature verification
    body = await request.body()
    body_str = body.decode('utf-8')
    
    # Verify signature
    if not verify_webhook_signature(body_str, payload.signature):
        logger.warning(f"Invalid webhook signature for transaction {payload.transaction_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    # Queue webhook processing task
    process_webhook_task.delay(
        transaction_id=payload.transaction_id,
        bank_reference=payload.bank_reference,
        status=payload.status,
        error_message=payload.error_message
    )
    
    logger.info(f"Webhook received for transaction {payload.transaction_id}")
    
    return WebhookResponse(
        message="Webhook received and queued for processing",
        transaction_id=payload.transaction_id
    )
