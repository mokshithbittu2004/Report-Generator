import hmac
import sentry_sdk
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import APIKeyHeader
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import get_settings
from app.core.logger import setup_logging, get_logger
from app.core.exceptions import api_exception_handler, general_exception_handler
from app.core.errors import APIException, ErrorCode, ErrorCategory, ErrorSeverity
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import rate_limiter
from app.routes import health, report


# ------------------------------------------------------------------------------
# Settings & Logging
# ------------------------------------------------------------------------------
settings = get_settings()

setup_logging(
    log_level=settings.LOG_LEVEL,
    service_name=settings.SERVICE_NAME,
    environment=settings.ENVIRONMENT,
)

logger = get_logger("bootstrap")


# ------------------------------------------------------------------------------
# API Key Security (Swagger Compatible)
# ------------------------------------------------------------------------------
api_key_header = APIKeyHeader(
    name=settings.API_KEY_HEADER,
    auto_error=False,
)


async def verify_api_key(api_key: str = Security(api_key_header)):

    if not settings.API_KEY_ENABLED:
        return

    if not api_key:
        raise APIException(
            error_code=ErrorCode.UNAUTHORIZED,
            message="API key missing",
            status_code=401,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.WARNING,
        )

    expected_key = settings.API_KEY.get_secret_value()

    if not hmac.compare_digest(api_key, expected_key):
        raise APIException(
            error_code=ErrorCode.UNAUTHORIZED,
            message="Invalid API key",
            status_code=401,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.WARNING,
        )


# ------------------------------------------------------------------------------
# Observability: Sentry
# ------------------------------------------------------------------------------
if settings.SENTRY_ENABLED and not settings.DEBUG and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN.get_secret_value(),
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        debug=False,
    )
    logger.info("Sentry initialized")
else:
    logger.info("Sentry not enabled or DSN missing — skipping initialization")


# ------------------------------------------------------------------------------
# Lifespan
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if not settings.SERVICE_NAME:
            raise RuntimeError("SERVICE_NAME not configured")

        logger.info("==========================================")
        logger.info(f"Starting {settings.SERVICE_NAME}")
        logger.info(f"Version: {settings.SERVICE_VERSION}")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"LLM Model: {settings.GEMINI_MODEL}")
        logger.info("==========================================")

        yield

    finally:
        logger.info("==========================================")
        logger.info("Shutting down gracefully...")

        if settings.SENTRY_ENABLED and not settings.DEBUG:
            sentry_sdk.flush(timeout=5)

        logger.info("Shutdown complete")
        logger.info("==========================================")


# ------------------------------------------------------------------------------
# App Factory
# ------------------------------------------------------------------------------
def create_app() -> FastAPI:

    openapi_tags = [
        {"name": "Health", "description": "Health check endpoints"},
        {"name": "Reports", "description": "Report generation APIs"},
    ]

    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        description="Generate AI-powered HTML and PDF reports from automation artifacts",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        openapi_tags=openapi_tags,
        lifespan=lifespan,
    )

    register_middlewares(app)
    register_exception_handlers(app)
    register_routes(app)

    return app


# ------------------------------------------------------------------------------
# Middleware Registration
# ------------------------------------------------------------------------------
def register_middlewares(app: FastAPI):

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    if settings.TRUSTED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.TRUSTED_HOSTS,
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        if settings.RATE_LIMIT_ENABLED:
            await rate_limiter.check_rate_limit(request)
        return await call_next(request)

    app.add_middleware(RequestLoggingMiddleware)


# ------------------------------------------------------------------------------
# Exception Handlers
# ------------------------------------------------------------------------------
def register_exception_handlers(app: FastAPI):

    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):

        api_exc = APIException(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            status_code=422,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            details={"errors": exc.errors()},
        )

        logger.warning(
            "Validation error",
            extra={"path": request.url.path, "errors": exc.errors()},
        )

        return JSONResponse(
            status_code=api_exc.status_code,
            content=api_exc.to_dict(),
        )


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
def register_routes(app: FastAPI):
    # Public route
    app.include_router(health.router, tags=["Health"])

    # Protected routes
    app.include_router(
        report.router,
        tags=["Reports"],
        dependencies=[Security(verify_api_key)],
    )


# ------------------------------------------------------------------------------
# Create App
# ------------------------------------------------------------------------------
app = create_app()