"""Rate limiting middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.services.rate_limiter import rate_limiter
from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce global rate limiting."""
    
    async def dispatch(self, request: Request, call_next):
        """Check global rate limit before processing request."""
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Check global rate limit
        key = "global:rate_limit"
        is_allowed, remaining, reset_timestamp, retry_after = rate_limiter.check_rate_limit(
            key=key,
            limit=settings.RATE_LIMIT_GLOBAL_PER_MIN,
            window_seconds=60
        )
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after
                },
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_GLOBAL_PER_MIN),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_timestamp),
                    "Retry-After": str(retry_after)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_GLOBAL_PER_MIN)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
        
        return response
