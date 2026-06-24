"""Unit tests for ``schemas/common.py`` (API-01)."""

from datetime import datetime, timezone

from app.schemas.common import ErrorDetail, ErrorResponse, JobListResponse, JobStatusResponse


class TestErrorDetail:
    def test_instantiate_and_serialize(self) -> None:
        detail = ErrorDetail(code="TEST_ERROR", message="Something went wrong")
        data = detail.model_dump()
        assert data == {"code": "TEST_ERROR", "message": "Something went wrong"}


class TestErrorResponse:
    def test_instantiate_and_serialize(self) -> None:
        resp = ErrorResponse(
            error=ErrorDetail(code="NOT_FOUND", message="Resource not found")
        )
        data = resp.model_dump()
        assert data == {"error": {"code": "NOT_FOUND", "message": "Resource not found"}}


class TestJobStatusResponse:
    def test_instantiate_and_serialize(self) -> None:
        now = datetime.now(timezone.utc)
        job = JobStatusResponse(
            job_id="abc-123",
            status="done",
            media_type="image",
            operation="compress",
            algorithm="rle",
            encrypted=False,
            created_at=now,
            updated_at=now,
            expires_at=now,
        )
        data = job.model_dump()
        assert data["job_id"] == "abc-123"
        assert data["status"] == "done"
        assert data["media_type"] == "image"


class TestJobListResponse:
    def test_instantiate_and_serialize(self) -> None:
        now = datetime.now(timezone.utc)
        job = JobStatusResponse(
            job_id="j1",
            status="pending",
            media_type="audio",
            operation="embed",
            created_at=now,
            updated_at=now,
            expires_at=now,
        )
        resp = JobListResponse(jobs=[job], total=1, limit=10, offset=0)
        data = resp.model_dump()
        assert data["total"] == 1
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["job_id"] == "j1"
