"""SQLAlchemy ORM models for jobs and metrics."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.db.database import Base


class Job(Base):
    """Represents a compression/steganography job."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    media_type: Mapped[str] = mapped_column(String(16), nullable=False)
    operation: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(String(512), nullable=False)
    result_path: Mapped[str | None] = mapped_column(String(512), nullable=True, default=None)
    algorithm: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    salt: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    metrics: Mapped[list["Metric"]] = relationship(
        "Metric", back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_jobs_status_expires_at", "status", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} status={self.status} op={self.operation}>"

    @classmethod
    def new(
        cls,
        job_id: str,
        media_type: str,
        operation: str,
        original_filename: str,
        original_path: str,
        algorithm: str | None = None,
        encrypted: bool = False,
        salt: str | None = None,
        status: str = "pending",
    ) -> "Job":
        """Factory method creating a Job with automatic timestamps."""
        now = datetime.now(timezone.utc)
        return cls(
            id=job_id,
            media_type=media_type,
            operation=operation,
            status=status,
            original_filename=original_filename,
            original_path=original_path,
            algorithm=algorithm,
            encrypted=encrypted,
            salt=salt,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=settings.job_ttl_hours),
        )


class Metric(Base):
    """EAV-style metric row linked to a job."""

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)

    job: Mapped["Job"] = relationship("Job", back_populates="metrics")

    __table_args__ = (
        Index("idx_metrics_job_id", "job_id"),
    )

    def __repr__(self) -> str:
        return f"<Metric id={self.id} job={self.job_id} {self.metric_name}={self.metric_value}>"
