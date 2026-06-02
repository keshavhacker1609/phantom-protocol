from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logger import get_logger

logger = get_logger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception [{request_id}]: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


async def not_found_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": f"Endpoint {request.url.path} does not exist",
        },
    )


async def validation_error_handler(request: Request, exc) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors() if hasattr(exc, "errors") else str(exc),
            "request_id": request_id,
        },
    )
