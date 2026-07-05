"""Tests for db/job_repository.py — create_job, get_job, update_job_status."""

import pytest
from sqlalchemy.orm import Session

from app.db.job_repository import create_job, get_job, update_job_status
from app.db.models import Job


class TestCreateJob:
    """Tests for create_job()."""

    def test_create_job_persists(self, db_session: Session, sample_job_id: str) -> None:
        """create_job persists a Job and returns it with an id."""
        job = Job.new(
            job_id=sample_job_id,
            media_type="image",
            operation="compress",
            original_filename="test.png",
            original_path="storage/j_id/original.png",
        )
        result = create_job(db_session, job)
        assert result.id == sample_job_id
        assert result.status == "pending"

        fetched = db_session.get(Job, sample_job_id)
        assert fetched is not None
        assert fetched.media_type == "image"

    def test_create_job_returns_refreshed(self, db_session: Session) -> None:
        """Returned Job has all fields populated."""
        job = Job.new(
            job_id="create-return-test",
            media_type="audio",
            operation="embed",
            original_filename="song.wav",
            original_path="storage/j_id/original.wav",
            algorithm="lsb",
            encrypted=True,
        )
        result = create_job(db_session, job)
        assert result.encrypted is True
        assert result.algorithm == "lsb"


class TestGetJob:
    """Tests for get_job()."""

    def test_get_job_returns_job(self, db_session: Session, sample_job: Job) -> None:
        """get_job returns the correct Job."""
        result = get_job(db_session, sample_job.id)
        assert result is not None
        assert result.id == sample_job.id
        assert result.original_filename == "test.png"

    def test_get_job_returns_none_for_missing(self, db_session: Session) -> None:
        """get_job returns None for non-existent job_id."""
        result = get_job(db_session, "nonexistent-id")
        assert result is None


class TestUpdateJobStatus:
    """Tests for update_job_status()."""

    def test_update_status(self, db_session: Session, sample_job: Job) -> None:
        """update_job_status changes the status field."""
        result = update_job_status(db_session, sample_job.id, status="done")
        assert result is not None
        assert result.status == "done"
        assert result.error_code is None

    def test_update_with_error(self, db_session: Session, sample_job: Job) -> None:
        """update_job_status sets error fields when provided."""
        result = update_job_status(
            db_session,
            sample_job.id,
            status="error",
            error_code="CAPACITY_EXCEEDED",
            error_message="Message too large",
        )
        assert result is not None
        assert result.status == "error"
        assert result.error_code == "CAPACITY_EXCEEDED"
        assert result.error_message == "Message too large"

    def test_update_with_result_path(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """update_job_status sets result_path when provided."""
        result = update_job_status(
            db_session, sample_job.id, status="done", result_path="storage/j_id/result.png"
        )
        assert result is not None
        assert result.status == "done"
        assert result.result_path == "storage/j_id/result.png"

    def test_update_nonexistent_job(
        self, db_session: Session, sample_job_id: str
    ) -> None:
        """update_job_status returns None for non-existent job."""
        result = update_job_status(db_session, sample_job_id, status="done")
        assert result is None

    def test_update_updates_timestamp(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """update_job_status changes updated_at."""
        original_updated = sample_job.updated_at
        import time

        time.sleep(0.01)
        result = update_job_status(db_session, sample_job.id, status="done")
        assert result.updated_at > original_updated


class TestCreateGetRoundTrip:
    """End-to-end round-trip test."""

    def test_create_then_get(self, db_session: Session, sample_job_id: str) -> None:
        """create_job then get_job returns identical data."""
        job = Job.new(
            job_id=sample_job_id,
            media_type="video",
            operation="compress",
            original_filename="clip.mp4",
            original_path="storage/j_id/original.mp4",
        )
        create_job(db_session, job)

        fetched = get_job(db_session, sample_job_id)
        assert fetched is not None
        assert fetched.id == job.id
        assert fetched.media_type == job.media_type
        assert fetched.operation == job.operation
        assert fetched.status == job.status
        assert fetched.original_filename == job.original_filename

    def test_create_update_get(
        self, db_session: Session, sample_job_id: str
    ) -> None:
        """create -> update -> get round-trip works."""
        job = Job.new(
            job_id=sample_job_id,
            media_type="image",
            operation="compress",
            original_filename="photo.png",
            original_path="storage/j_id/original.png",
        )
        create_job(db_session, job)

        update_job_status(
            db_session,
            sample_job_id,
            status="error",
            error_code="UNSUPPORTED_FORMAT",
            error_message="Invalid file type",
        )

        fetched = get_job(db_session, sample_job_id)
        assert fetched.status == "error"
        assert fetched.error_code == "UNSUPPORTED_FORMAT"
        assert fetched.error_message == "Invalid file type"
