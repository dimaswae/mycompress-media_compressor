"""FastAPI exception handlers that map ``AppError`` subclasses to HTTP responses.

Each handler produces a standard ``ErrorResponse`` body so clients always
receive a consistent error envelope regardless of which exception was raised.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse
from app.utils.exceptions import (
    AppError,
    CapacityExceededError,
    DecryptionError,
    FFmpegTimeoutError,
    NotFoundError,
    StorageQuotaError,
    UnsupportedFormatError,
    ValidationError,
    InvalidImageError,
    VideoProcessingError,
)

_STATUS_MAP: dict[type[AppError], int] = {
    UnsupportedFormatError: 400,
    CapacityExceededError: 400,
    DecryptionError: 400,
    NotFoundError: 404,
    FFmpegTimeoutError: 504,
    StorageQuotaError: 507,
    ValidationError: 400,
    InvalidImageError: 400,
    VideoProcessingError: 400,
}


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers for every ``AppError`` subclass on *app*.

    Unknown ``AppError`` subclasses (if any) are caught by the generic
    ``AppError`` handler and mapped to 400.
    """

    @app.exception_handler(UnsupportedFormatError)
    async def _handle_unsupported_format(
        request: Request, exc: UnsupportedFormatError
    ) -> JSONResponse:
        return _build_response(400, exc)

    @app.exception_handler(CapacityExceededError)
    async def _handle_capacity_exceeded(
        request: Request, exc: CapacityExceededError
    ) -> JSONResponse:
        return _build_response(400, exc)

    @app.exception_handler(DecryptionError)
    async def _handle_decryption_error(
        request: Request, exc: DecryptionError
    ) -> JSONResponse:
        return _build_response(400, exc)

    @app.exception_handler(FFmpegTimeoutError)
    async def _handle_ffmpeg_timeout(
        request: Request, exc: FFmpegTimeoutError
    ) -> JSONResponse:
        return _build_response(504, exc)

    @app.exception_handler(NotFoundError)
    async def _handle_not_found(
        request: Request, exc: NotFoundError
    ) -> JSONResponse:
        return _build_response(404, exc)

    @app.exception_handler(StorageQuotaError)
    async def _handle_storage_quota(
        request: Request, exc: StorageQuotaError
    ) -> JSONResponse:
        return _build_response(507, exc)

    @app.exception_handler(ValidationError)
    async def _handle_validation_error(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return _build_response(400, exc)

    @app.exception_handler(InvalidImageError)
    async def _handle_invalid_image_error(
        request: Request, exc: InvalidImageError
    ) -> JSONResponse:
        return _build_response(400, exc)

    @app.exception_handler(VideoProcessingError)
    async def _handle_video_processing_error(
        request: Request, exc: VideoProcessingError
    ) -> JSONResponse:
        return _build_response(400, exc)

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        status = _STATUS_MAP.get(type(exc), 400)
        return _build_response(status, exc)


def _build_response(status_code: int, exc: AppError) -> JSONResponse:
    """Construct a JSON response with a standard error envelope."""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message)
        ).model_dump(),
    )
