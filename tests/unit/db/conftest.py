"""Pytest fixtures for database tests."""

from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base
from app.db.models import Job


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
def sample_job(db_session: Session, sample_job_id: str) -> Job:
    """Create and persist a sample Job for repository tests."""
    job = Job.new(
        job_id=sample_job_id,
        media_type="image",
        operation="compress",
        original_filename="test.png",
        original_path="storage/job_id/original.png",
        algorithm="rle",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job
