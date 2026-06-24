"""Shared test fixtures for all test modules."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes_audio import router as audio_router
from app.api.routes_health import router as health_router
from app.api.routes_image import router as image_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_video import router as video_router
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
    app.include_router(audio_router, prefix=settings.api_prefix)
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(image_router, prefix=settings.api_prefix)
    app.include_router(jobs_router, prefix=settings.api_prefix)
    app.include_router(video_router, prefix=settings.api_prefix)
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


def _make_wav_bytes(
    sample_rate: int = 8000,
    duration_sec: float = 0.1,
    n_channels: int = 1,
    sampwidth: int = 2,
) -> bytes:
    """Generate a silent WAV file as bytes."""
    import struct
    import wave
    from io import BytesIO

    buf = BytesIO()
    n_frames = int(sample_rate * duration_sec)
    with wave.open(buf, "wb") as w:
        w.setnchannels(n_channels)
        w.setsampwidth(sampwidth)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack(f"<{n_frames}h", *([0] * n_frames)))
    return buf.getvalue()


@pytest.fixture
def sample_wav_bytes() -> bytes:
    """Generate a small silent WAV file for testing."""
    return _make_wav_bytes()


@pytest.fixture
def sample_mp3_bytes() -> bytes:
    """Generate minimal bytes that pass MP3 magic-byte validation."""
    return b"\xff\xfb\x90\x00\x00\x00\x00\x00"


def _make_mp4_bytes(mdat_payload_size: int = 200) -> bytes:
    """Generate a minimal MP4 byte string with a valid ftyp box and mdat box."""
    import struct

    ftyp_content = b"mp42\x00\x00\x00\x00mp42mp41"
    ftyp_size = 8 + len(ftyp_content)
    ftyp = struct.pack(">I", ftyp_size) + b"ftyp" + ftyp_content

    mdat_payload = b"\x00" * mdat_payload_size
    mdat_size = 8 + len(mdat_payload)
    mdat = struct.pack(">I", mdat_size) + b"mdat" + mdat_payload

    return ftyp + mdat


@pytest.fixture
def sample_mp4_bytes() -> bytes:
    """Generate a minimal MP4 file that passes magic-byte validation."""
    return _make_mp4_bytes()
