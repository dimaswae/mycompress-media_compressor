"""Shared test fixtures for all test modules."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes_health import router as health_router
from app.api.routes_image import router as image_router
from app.api.routes_jobs import router as jobs_router
from app.config import settings
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.middleware.error_handler import register_error_handlers


@pytest.fixture(scope="session", autouse=True)
def _ensure_prod_db_tables() -> Generator[None, None, None]:
    """Ensure the production DB (used by the background sweep task) has tables."""
    from app.db.database import engine as prod_engine

    Base.metadata.create_all(bind=prod_engine)
    yield
    Base.metadata.drop_all(bind=prod_engine)


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _make_app(db_session: Session, storage_dir: str) -> FastAPI:
    """Build a fresh FastAPI instance wired to the given *db_session*."""
    app = FastAPI(title="mycompress-test")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(image_router, prefix=settings.api_prefix)
    app.include_router(jobs_router, prefix=settings.api_prefix)
    app.dependency_overrides[get_db] = lambda: db_session

    return app


@pytest.fixture
def client(db_session: Session, tmp_path: Path) -> Generator[TestClient, None, None]:
    """Return a ``TestClient`` wired to an in-memory database and temp storage."""
    storage_dir = str(tmp_path / "storage")
    app = _make_app(db_session, storage_dir)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_job(db_session: Session) -> dict:
    """Create and return a minimal ``done`` job for use in job-route tests."""
    from app.db.models import Job
    from datetime import datetime, timedelta, timezone

    job = Job(
        id="test-job-001",
        media_type="image",
        operation="compress",
        status="done",
        original_filename="test.png",
        original_path="/tmp/test_original.png",
        result_path=None,
        algorithm="rle",
        encrypted=False,
        salt=None,
        error_code=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return {"id": job.id, "status": job.status, "result_path": job.result_path}


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Generate a small 4×4 RGB PNG image as bytes."""
    from io import BytesIO
    from PIL import Image

    img = Image.new("RGB", (4, 4), color=(128, 128, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_jpg_bytes() -> bytes:
    """Generate a small 4×4 RGB JPEG image as bytes."""
    from io import BytesIO
    from PIL import Image

    img = Image.new("RGB", (4, 4), color=(128, 128, 128))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()
