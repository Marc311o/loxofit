import logging

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ==============================
# ERRORS / EXCEPTIONS
# ==============================


class ErrorResponse(BaseModel):
    detail: str
    code: str


class AppError(Exception):
    """Base app error model"""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    detail: str = "Internal server error"
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    """404 - no asset belonging to the user"""

    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    detail = "Asset not found"


class ConflictError(AppError):
    """409 - data conflict"""

    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"
    detail = "Conflict with actual state of the asset"


class AuthenticationError(AppError):
    """401 - unknown user"""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "NOT_AUTHENTICATED"
    detail = "Failed to authenticate"
    headers = {"WWW-Authenticate": "Bearer"}


class PermissionDeniedError(AppError):
    """403 - Insufficient permission"""

    status_code = status.HTTP_403_FORBIDDEN
    code = "PERMISSION_DENIED"
    detail = "Insufficient permission"


class ServiceUnavailableError(AppError):
    """503 - Service unavailable"""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "SERVICE_UNAVAILABLE"
    detail = "Service temporarily unavailable"


# ==============================
# HANDLERS
# ==============================


def _error(
    status_code: int, detail: object, code: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"detail": detail, "code": code}),
        headers=headers,
    )


async def _app_error_handler(request: Request, exception: AppError) -> JSONResponse:
    return _error(exception.status_code, exception.detail, exception.code, exception.headers)


async def _http_exception_handler(request: Request, exception: HTTPException) -> JSONResponse:
    return _error(
        exception.status_code, exception.detail, f"HTTP_{exception.status_code}", exception.headers
    )


async def _validation_error_handler(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    return _error(422, exception.errors(), "VALIDATION_ERROR")


async def _unhandled_error_handler(request: Request, exception: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s %s", request.method, request.url.path)
    return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, AppError.detail, AppError.code)
