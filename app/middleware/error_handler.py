"""Global error handling middleware."""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next):
        """Handle errors globally."""
        try:
            response = await call_next(request)
            return response
        except SQLAlchemyError as e:
            logger.error(
                f"Database error: {str(e)}",
                extra={"request_id": getattr(request.state, "request_id", None)}
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "database_error",
                    "message": "A database error occurred. Please try again later."
                }
            )
        except Exception as e:
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={"request_id": getattr(request.state, "request_id", None)},
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": "An unexpected error occurred. Please try again later."
                }
            )
