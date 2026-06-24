"""Unit tests for ``services/job_service.py`` (API-05)."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.services.job_service import create_job, get_job_status, update_job_status


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()


class TestCreateJob:
    def test_creates_job_with_expected_fields(self, db_session: Session) -> None:
        job = create_job(
            db=db_session,
            media_type="image",
            operation="compress",
            original_filename="photo.png",
            original_path="/tmp/photo.png",
            algorithm="rle",
        )
        assert job.id is not None
        assert job.media_type == "image"
        assert job.operation == "compress"
        assert job.algorithm == "rle"
        assert job.status == "pending"
        assert job.original_filename == "photo.png"
        assert isinstance(job.created_at, datetime)

    def test_can_retrieve_created_job(self, db_session: Session) -> None:
        job = create_job(
            db=db_session,
            media_type="audio",
            operation="embed",
            original_filename="clip.wav",
            original_path="/tmp/clip.wav",
        )
        retrieved = get_job_status(db_session, job.id)
        assert retrieved is not None
        assert retrieved.id == job.id
        assert retrieved.status == "pending"


class TestGetJobStatus:
    def test_returns_none_for_nonexistent_job(self, db_session: Session) -> None:
        result = get_job_status(db_session, "nonexistent-id")
        assert result is None


class TestUpdateJobStatus:
    def test_updates_status(self, db_session: Session) -> None:
        job = create_job(
            db=db_session,
            media_type="video",
            operation="compress",
            original_filename="clip.mp4",
            original_path="/tmp/clip.mp4",
        )
        updated = update_job_status(
            db_session, job.id, status="done", result_path="/tmp/result.mp4"
        )
        assert updated is not None
        assert updated.status == "done"
        assert updated.result_path == "/tmp/result.mp4"

    def test_returns_none_for_nonexistent_job(self, db_session: Session) -> None:
        result = update_job_status(db_session, "no-such-id", status="done")
        assert result is None
