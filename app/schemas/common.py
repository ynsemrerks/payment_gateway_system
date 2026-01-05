"""Common schemas for pagination and error responses."""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters."""
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    details: Optional[dict] = None


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit error response."""
    retry_after: int
