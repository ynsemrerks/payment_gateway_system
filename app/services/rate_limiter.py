"""Rate limiter service using Redis."""
import time
from typing import Tuple
import redis
from app.config import settings


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    """
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> Tuple[bool, int, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique key for rate limiting (e.g., "user:123:balance")
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds (default: 60)
            
        Returns:
            Tuple of (is_allowed, remaining, reset_timestamp, retry_after)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Use Redis sorted set with timestamps as scores
        pipe = self.redis_client.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiry on the key
        pipe.expire(key, window_seconds)
        
        results = pipe.execute()
        current_count = results[1]
        
        # Calculate remaining and reset time
        remaining = max(0, limit - current_count - 1)
        reset_timestamp = int(now + window_seconds)
        retry_after = window_seconds if current_count >= limit else 0
        
        is_allowed = current_count < limit
        
        return is_allowed, remaining, reset_timestamp, retry_after
    
    def get_rate_limit_headers(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> dict:
        """
        Get rate limit headers for response.
        
        Args:
            key: Unique key for rate limiting
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Dictionary of rate limit headers
        """
        is_allowed, remaining, reset_timestamp, retry_after = self.check_rate_limit(
            key, limit, window_seconds
        )
        
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_timestamp)
        }


# Global rate limiter instance
rate_limiter = RateLimiter()
