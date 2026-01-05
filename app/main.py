"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

from app.database import engine
from app.admin import UserAdmin, TransactionAdmin, IdempotencyKeyAdmin, authentication_backend

from app.config import settings
from app.utils.logging_config import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.api.v1 import deposits, withdrawals, users, webhooks, auth

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Payment Gateway API")
    yield
    # Shutdown
    logger.info("Shutting down Payment Gateway API")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade payment gateway API with async transaction processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Setup Admin
admin = Admin(app, engine, title="Payment Gateway Admin", authentication_backend=authentication_backend)
admin.add_view(UserAdmin)
admin.add_view(TransactionAdmin)
admin.add_view(IdempotencyKeyAdmin)

# Add middleware (order matters - first added is outermost)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    deposits.router,
    prefix=f"{settings.API_V1_PREFIX}/deposits",
    tags=["Deposits"]
)
app.include_router(
    withdrawals.router,
    prefix=f"{settings.API_V1_PREFIX}/withdrawals",
    tags=["Withdrawals"]
)
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"]
)
app.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["Webhooks"]
)
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "payment-gateway-api"
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "message": "Payment Gateway API",
        "version": "1.0.0",
        "docs": "/docs"
    }
