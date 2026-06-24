"""Integration tests for error handler middleware (API-03).

Verifies that raising ``AppError`` subclasses in routes produces correct
HTTP status codes and the standard ``ErrorResponse`` envelope.
"""

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.middleware.error_handler import register_error_handlers
from app.utils.exceptions import (
    CapacityExceededError,
    DecryptionError,
    FFmpegTimeoutError,
    StorageQuotaError,
    UnsupportedFormatError,
)


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/raise/{exc_name}")
    async def raise_exception(exc_name: str) -> None:
        factory = {
            "UnsupportedFormatError": UnsupportedFormatError,
            "CapacityExceededError": CapacityExceededError,
            "DecryptionError": DecryptionError,
            "FFmpegTimeoutError": FFmpegTimeoutError,
            "StorageQuotaError": StorageQuotaError,
        }
        exc_cls = factory.get(exc_name)
        if exc_cls is None:
            raise ValueError(f"Unknown exception: {exc_name}")
        raise exc_cls()

    return app


class TestErrorHandlerIntegration:
    def setup_method(self) -> None:
        self.app = _build_test_app()
        self.client = TestClient(self.app)

    def test_unsupported_format_returns_400(self) -> None:
        resp = self.client.get("/raise/UnsupportedFormatError")
        assert resp.status_code == 400
        body = resp.json()
        assert body["error"]["code"] == "UNSUPPORTED_FORMAT"

    def test_capacity_exceeded_returns_400(self) -> None:
        resp = self.client.get("/raise/CapacityExceededError")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "CAPACITY_EXCEEDED"

    def test_decryption_error_returns_400(self) -> None:
        resp = self.client.get("/raise/DecryptionError")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "DECRYPTION_FAILED"

    def test_ffmpeg_timeout_returns_504(self) -> None:
        resp = self.client.get("/raise/FFmpegTimeoutError")
        assert resp.status_code == 504
        assert resp.json()["error"]["code"] == "FFMPEG_TIMEOUT"

    def test_storage_quota_returns_507(self) -> None:
        resp = self.client.get("/raise/StorageQuotaError")
        assert resp.status_code == 507
        assert resp.json()["error"]["code"] == "STORAGE_QUOTA_EXCEEDED"
