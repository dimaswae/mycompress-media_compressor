"""Tests for db/models.py — Job and Metric ORM models."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import inspect

from app.db.models import Job, Metric


class TestJobModel:
    """Tests for the Job ORM model."""

    def test_job_instantiation(self, sample_job_id: str) -> None:
        """Job can be instantiated with required fields."""
        job = Job.new(
            job_id=sample_job_id,
            media_type="image",
            operation="compress",
            original_filename="photo.png",
            original_path="storage/job_id/original.png",
            algorithm="huffman",
        )
        assert job.id == sample_job_id
        assert job.media_type == "image"
        assert job.operation == "compress"
        assert job.status == "pending"
        assert job.original_filename == "photo.png"
        assert job.original_path == "storage/job_id/original.png"
        assert job.algorithm == "huffman"
        assert job.encrypted is False
        assert job.salt is None
        assert job.error_code is None
        assert job.error_message is None
        assert job.result_path is None
        assert isinstance(job.created_at, datetime)
        assert isinstance(job.updated_at, datetime)
        assert isinstance(job.expires_at, datetime)

    def test_job_default_expiry(self, sample_job_id: str) -> None:
        """Job expires_at should be ~24h after created_at."""
        job = Job.new(
            job_id=sample_job_id,
            media_type="audio",
            operation="embed",
            original_filename="song.wav",
            original_path="storage/job_id/original.wav",
        )
        expected_expiry = job.created_at + timedelta(hours=24)
        diff = abs((job.expires_at - expected_expiry).total_seconds())
        assert diff < 1

    def test_job_encrypted_flag(self, sample_job_id: str) -> None:
        """Job can be created with encrypted=True and salt."""
        job = Job.new(
            job_id=sample_job_id,
            media_type="image",
            operation="embed",
            original_filename="secret.png",
            original_path="storage/job_id/original.png",
            encrypted=True,
            salt="abc123salt",
        )
        assert job.encrypted is True
        assert job.salt == "abc123salt"

    def test_job_repr(self, sample_job_id: str) -> None:
        """__repr__ returns useful summary."""
        job = Job.new(
            job_id=sample_job_id,
            media_type="video",
            operation="compress",
            original_filename="clip.mp4",
            original_path="storage/job_id/original.mp4",
        )
        assert sample_job_id in repr(job)
        assert "pending" in repr(job)
        assert "compress" in repr(job)

    def test_job_all_fields_settable(self, db_session, sample_job_id: str) -> None:
        """All Job columns can be set and persisted."""
        now = datetime.now(timezone.utc)
        job = Job(
            id=sample_job_id,
            media_type="video",
            operation="extract",
            status="done",
            original_filename="test.mp4",
            original_path="storage/j_id/original.mp4",
            result_path="storage/j_id/result.mp4",
            algorithm="frame_embed",
            encrypted=True,
            salt="mysalt",
            error_code=None,
            error_message=None,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=24),
        )
        db_session.add(job)
        db_session.commit()

        fetched = db_session.get(Job, sample_job_id)
        assert fetched is not None
        assert fetched.status == "done"
        assert fetched.result_path == "storage/j_id/result.mp4"
        assert fetched.encrypted is True
        assert fetched.salt == "mysalt"


class TestMetricModel:
    """Tests for the Metric ORM model."""

    def test_metric_instantiation(self) -> None:
        """Metric can be instantiated with required fields."""
        metric = Metric(
            job_id="some-job-uuid", metric_name="psnr", metric_value=42.5
        )
        assert metric.job_id == "some-job-uuid"
        assert metric.metric_name == "psnr"
        assert metric.metric_value == 42.5

    def test_metric_auto_increment_id(self, db_session, sample_job: Job) -> None:
        """Metric.id auto-increments."""
        m1 = Metric(job_id=sample_job.id, metric_name="psnr", metric_value=30.0)
        m2 = Metric(job_id=sample_job.id, metric_name="ssim", metric_value=0.95)
        db_session.add_all([m1, m2])
        db_session.commit()
        assert m1.id == 1
        assert m2.id == 2

    def test_metric_fk_constraint(self, db_session) -> None:
        """Metric with invalid job_id fails FK constraint when FK enforcement is on."""
        from sqlalchemy import text
        db_session.execute(text("PRAGMA foreign_keys = ON"))
        db_session.commit()
        m = Metric(job_id="nonexistent", metric_name="mse", metric_value=0.01)
        db_session.add(m)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_metric_repr(self) -> None:
        """__repr__ returns useful summary."""
        m = Metric(job_id="abc", metric_name="psnr", metric_value=35.2)
        assert "psnr" in repr(m)
        assert "35.2" in repr(m)


class TestJobMetricRelationship:
    """Tests for the Job <-> Metric relationship."""

    def test_job_has_metrics(self, db_session, sample_job: Job) -> None:
        """Job.metrics returns related Metric objects."""
        m1 = Metric(job_id=sample_job.id, metric_name="psnr", metric_value=40.0)
        m2 = Metric(job_id=sample_job.id, metric_name="mse", metric_value=0.5)
        db_session.add_all([m1, m2])
        db_session.commit()

        fetched = db_session.get(Job, sample_job.id)
        assert len(fetched.metrics) == 2
        names = {m.metric_name for m in fetched.metrics}
        assert names == {"psnr", "mse"}

    def test_cascade_delete(self, db_session, sample_job: Job) -> None:
        """Deleting a Job cascades to its Metrics."""
        m = Metric(job_id=sample_job.id, metric_name="psnr", metric_value=40.0)
        db_session.add(m)
        db_session.commit()

        db_session.delete(sample_job)
        db_session.commit()

        metrics = db_session.query(Metric).filter(Metric.job_id == sample_job.id).all()
        assert len(metrics) == 0
