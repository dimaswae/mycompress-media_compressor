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
    return _make_mp4_bytes(1024)  # Increased to fit encrypted messages


@pytest.fixture
def sample_video_fixture_bytes() -> bytes:
    """Load the sample MP4 fixture file from tests/fixtures/."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixture_path = fixtures_dir / "sample_video.mp4"
    if fixture_path.exists():
        return fixture_path.read_bytes()
    return _make_mp4_bytes(10240)


@pytest.fixture(autouse=True)
def _mock_video_stego_codec(monkeypatch) -> None:
    """Mock VideoLsbCodec capacity, embed, and extract methods for mock MP4 files.

    If the video bytes are small (mock file), we mock the calls to avoid executing
    real ffprobe/ffmpeg/cv2 subprocesses which would fail on mock files.
    For real video fixture files, we delegate to the real implementations.
    """
    from app.core.steganography.video_lsb import VideoLsbCodec
    from app.utils.exceptions import VideoProcessingError, CapacityExceededError, UnsupportedFormatError

    real_capacity = VideoLsbCodec.capacity
    real_embed = VideoLsbCodec.embed
    real_extract = VideoLsbCodec.extract

    def find_mdat_offset_and_size(data: bytes) -> tuple[int, int]:
        import struct
        pos = 0
        while pos + 8 <= len(data):
            (box_size,) = struct.unpack_from(">I", data, pos)
            box_type = data[pos + 4 : pos + 8]
            if box_type == b"mdat":
                payload_offset = pos + 8
                if box_size == 0:
                    box_size = len(data) - pos
                actual_payload = box_size - 8
                if payload_offset + actual_payload > len(data):
                    actual_payload = len(data) - payload_offset
                return payload_offset, actual_payload
            if box_size == 0:
                break
            pos += box_size
        return 0, 0

    def mock_capacity(self, video_bytes: bytes) -> int:
        from app.core.steganography.video_lsb import _is_mp4
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")
        if len(video_bytes) > 20000:
            return real_capacity(self, video_bytes)
        offset, size = find_mdat_offset_and_size(video_bytes)
        if offset == 0:
            raise VideoProcessingError("Failed to calculate video capacity: MP4 file contains no mdat box")
        return size

    def mock_embed(self, video_bytes: bytes, message: bytes) -> bytes:
        from app.core.steganography.video_lsb import _is_mp4
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")
        if len(video_bytes) > 20000:
            return real_embed(self, video_bytes, message)
        offset, data_size = find_mdat_offset_and_size(video_bytes)
        if offset == 0:
            raise VideoProcessingError("Failed to embed message into video: MP4 file contains no mdat box")
        length_bytes = len(message).to_bytes(4, "big")
        payload = length_bytes + message
        if len(payload) * 8 > data_size:
            raise CapacityExceededError(
                f"Message size {len(message)} bytes exceeds capacity"
            )
        header = video_bytes[:offset]
        mdat_payload = bytearray(video_bytes[offset : offset + data_size])
        for i, byte_val in enumerate(payload):
            for bit_idx in range(8):
                bit = (byte_val >> (7 - bit_idx)) & 1
                mdat_payload[i * 8 + bit_idx] = (mdat_payload[i * 8 + bit_idx] & 0xFE) | bit
        return bytes(header) + bytes(mdat_payload) + video_bytes[offset + data_size:]

    def mock_extract(self, video_bytes: bytes) -> bytes:
        from app.core.steganography.video_lsb import _is_mp4
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")
        if len(video_bytes) > 20000:
            return real_extract(self, video_bytes)
        offset, data_size = find_mdat_offset_and_size(video_bytes)
        if offset == 0:
            raise VideoProcessingError("Failed to extract message from video: MP4 file contains no mdat box")
        mdat_payload = video_bytes[offset : offset + data_size]
        all_bits = [int(b & 1) for b in mdat_payload]
        usable_bits = (data_size // 8) * 8
        raw_bytes_list = []
        for i in range(0, usable_bits, 8):
            chunk = all_bits[i : i + 8]
            if len(chunk) < 8:
                break
            byte_val = 0
            for b in chunk:
                byte_val = (byte_val << 1) | b
            raw_bytes_list.append(byte_val)
        raw_bytes = bytes(raw_bytes_list)
        if len(raw_bytes) < 4:
            raise VideoProcessingError("Failed to extract message: truncated payload")
        msg_len = int.from_bytes(raw_bytes[:4], "big")
        if msg_len > len(raw_bytes) - 4:
            raise VideoProcessingError("Failed to extract message: corrupt payload size")
        return raw_bytes[4 : 4 + msg_len]

    monkeypatch.setattr(VideoLsbCodec, "capacity", mock_capacity)
    monkeypatch.setattr(VideoLsbCodec, "embed", mock_embed)
    monkeypatch.setattr(VideoLsbCodec, "extract", mock_extract)

