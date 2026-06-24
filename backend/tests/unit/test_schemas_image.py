"""Unit tests for schemas/image.py (IMG-21)."""

from pydantic import ValidationError

from app.schemas.image import (
    ImageCompareResponse,
    ImageExtractResponse,
    ImageJobResponse,
)


class TestImageJobResponse:
    def test_minimal(self) -> None:
        obj = ImageJobResponse(job_id="abc", status="done")
        assert obj.job_id == "abc"
        assert obj.status == "done"
        assert obj.metrics == {}

    def test_with_metrics(self) -> None:
        obj = ImageJobResponse(
            job_id="abc", status="done", metrics={"psnr": 45.0, "ssim": 0.99}
        )
        assert obj.metrics["psnr"] == 45.0
        assert obj.metrics["ssim"] == 0.99

    def test_missing_required_raises(self) -> None:
        try:
            ImageJobResponse(status="done")
            assert False, "expected ValidationError"
        except ValidationError:
            pass


class TestImageExtractResponse:
    def test_minimal(self) -> None:
        obj = ImageExtractResponse(job_id="abc", message="hello")
        assert obj.job_id == "abc"
        assert obj.message == "hello"
        assert obj.metrics == {}

    def test_with_metrics(self) -> None:
        obj = ImageExtractResponse(
            job_id="abc",
            message="secret",
            metrics={"processing_time_ms": 12.5},
        )
        assert obj.metrics["processing_time_ms"] == 12.5


class TestImageCompareResponse:
    def test_minimal(self) -> None:
        obj = ImageCompareResponse(
            job_id="abc", original_size=100, result_size=80
        )
        assert obj.job_id == "abc"
        assert obj.original_size == 100
        assert obj.result_size == 80
        assert obj.metrics == {}

    def test_with_metrics(self) -> None:
        obj = ImageCompareResponse(
            job_id="abc",
            original_size=200,
            result_size=100,
            metrics={"psnr": 35.0, "mse": 0.5},
        )
        assert obj.metrics["psnr"] == 35.0
