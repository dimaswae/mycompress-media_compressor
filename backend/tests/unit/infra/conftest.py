"""Shared fixtures for infra unit tests."""

from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base
from app.db.models import Job


@pytest.fixture
def tmp_storage(tmp_path: Path) -> Path:
    """Return a temporary directory for storage tests."""
    return tmp_path / "storage"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a fresh in-memory SQLite database for each test with FK enforcement."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def _set_fk_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_job_id() -> str:
    return str(uuid4())


@pytest.fixture
def expired_job(db_session: Session, sample_job_id: str) -> Job:
    """Create a Job with an expired expires_at timestamp."""
    from datetime import datetime, timedelta, timezone

    past = datetime.now(timezone.utc) - timedelta(hours=1)
    job = Job(
        id=sample_job_id,
        media_type="image",
        operation="compress",
        status="done",
        original_filename="old.png",
        original_path=f"storage/{sample_job_id}/original.png",
        result_path=f"storage/{sample_job_id}/result.png",
        created_at=past - timedelta(hours=25),
        updated_at=past,
        expires_at=past,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job
