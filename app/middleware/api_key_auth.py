from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import get_settings
from app.core.errors import APIException, ErrorCode, ErrorCategory, ErrorSeverity


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):

        # Skip if disabled
        if not self.settings.API_KEY_ENABLED:
            return await call_next(request)

        # Skip health endpoint (optional)
        if request.url.path.startswith("/health"):
            return await call_next(request)

        provided_key = request.headers.get(self.settings.API_KEY_HEADER)

        if not provided_key:
            raise APIException(
                error_code=ErrorCode.UNAUTHORIZED,
                message="API key missing",
                status_code=401,
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.WARNING,
            )

        if provided_key != self.settings.API_KEY.get_secret_value():
            raise APIException(
                error_code=ErrorCode.UNAUTHORIZED,
                message="Invalid API key",
                status_code=401,
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.WARNING,
            )

        return await call_next(request)