"""Application configuration using Pydantic Settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://payment_user:payment_pass@localhost:5432/payment_gateway"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Payment Gateway API"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    WEBHOOK_SECRET: str = "your-webhook-secret-change-in-production"
    
    # Admin Panel
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    
    # Rate Limiting
    RATE_LIMIT_BALANCE_PER_MIN: int = 10
    RATE_LIMIT_TRANSACTIONS_PER_MIN: int = 20
    RATE_LIMIT_GLOBAL_PER_MIN: int = 1000
    
    # Bank Simulation
    BANK_MIN_DELAY_SECONDS: int = 2
    BANK_MAX_DELAY_SECONDS: int = 10
    BANK_SUCCESS_RATE: float = 0.9
    
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672/"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 300
    
    # Idempotency
    IDEMPOTENCY_KEY_EXPIRY_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
