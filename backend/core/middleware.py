import uuid
import contextvars
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variable to store Request ID globally for the request context (useful for logs/exception handling)
request_id_ctx_var = contextvars.ContextVar("request_id", default="")

def get_request_id() -> str:
    """
    Retrieves the current request's unique request ID.
    """
    return request_id_ctx_var.get()

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates/extracts a unique Request ID for every incoming request,
    attaches it as a response header, and injects secure baseline HTTP headers.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check if X-Request-ID is already provided by a client or proxy
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
            
        # Set the request ID in context variables
        token = request_id_ctx_var.set(request_id)
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
        except Exception as e:
            # Let the exception propagate to central error handlers
            raise e
        finally:
            # Reset context variable token
            request_id_ctx_var.reset(token)
            
        # Append request ID to the response headers
        response.headers["X-Request-ID"] = request_id
        
        # Add baseline security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
