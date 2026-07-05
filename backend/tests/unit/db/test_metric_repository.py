"""Tests for db/metric_repository.py — add_metric, get_metrics_for_job."""

import pytest
from sqlalchemy.orm import Session

from app.db.metric_repository import add_metric, get_metrics_for_job
from app.db.models import Job, Metric


class TestAddMetric:
    """Tests for add_metric()."""

    def test_add_metric_persists(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """add_metric persists a metric and returns it."""
        metric = add_metric(db_session, sample_job.id, "psnr", 35.2)
        assert metric.job_id == sample_job.id
        assert metric.metric_name == "psnr"
        assert metric.metric_value == 35.2
        assert metric.id is not None

    def test_add_metric_creates_row(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """add_metric actually inserts into the database."""
        add_metric(db_session, sample_job.id, "compression_ratio", 2.5)
        count = (
            db_session.query(Metric)
            .filter(Metric.job_id == sample_job.id)
            .count()
        )
        assert count == 1

    def test_add_multiple_metrics(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """Multiple metrics can be added for the same job."""
        add_metric(db_session, sample_job.id, "psnr", 40.0)
        add_metric(db_session, sample_job.id, "ssim", 0.98)
        add_metric(db_session, sample_job.id, "mse", 0.01)
        count = (
            db_session.query(Metric)
            .filter(Metric.job_id == sample_job.id)
            .count()
        )
        assert count == 3


class TestGetMetricsForJob:
    """Tests for get_metrics_for_job()."""

    def test_get_metrics_returns_empty(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """get_metrics_for_job returns empty list when no metrics exist."""
        metrics = get_metrics_for_job(db_session, sample_job.id)
        assert metrics == []

    def test_get_metrics_returns_all(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """get_metrics_for_job returns all metrics for the job."""
        add_metric(db_session, sample_job.id, "psnr", 30.5)
        add_metric(db_session, sample_job.id, "compression_ratio", 3.2)

        metrics = get_metrics_for_job(db_session, sample_job.id)
        assert len(metrics) == 2
        names = {m.metric_name for m in metrics}
        assert names == {"psnr", "compression_ratio"}

    def test_get_metrics_values_match(
        self, db_session: Session, sample_job: Job
    ) -> None:
        """Returned metric values match what was inserted."""
        add_metric(db_session, sample_job.id, "psnr", 42.0)
        add_metric(db_session, sample_job.id, "processing_time_ms", 150.0)

        metrics = get_metrics_for_job(db_session, sample_job.id)
        values = {m.metric_name: m.metric_value for m in metrics}
        assert values["psnr"] == 42.0
        assert values["processing_time_ms"] == 150.0

    def test_get_metrics_scoped_to_job(
        self, db_session: Session, sample_job_id: str
    ) -> None:
        """Metrics from different jobs are not mixed."""
        job_a = Job.new(
            job_id=sample_job_id,
            media_type="image",
            operation="compress",
            original_filename="a.png",
            original_path="storage/a/original.png",
        )
        job_b_id = "job-b-uuid"
        job_b = Job.new(
            job_id=job_b_id,
            media_type="audio",
            operation="embed",
            original_filename="b.wav",
            original_path="storage/b/original.wav",
        )
        db_session.add_all([job_a, job_b])
        db_session.commit()

        add_metric(db_session, job_a.id, "psnr", 35.0)
        add_metric(db_session, job_b.id, "compression_ratio", 5.0)

        metrics_a = get_metrics_for_job(db_session, job_a.id)
        metrics_b = get_metrics_for_job(db_session, job_b.id)

        assert len(metrics_a) == 1
        assert len(metrics_b) == 1
        assert metrics_a[0].metric_name == "psnr"
        assert metrics_b[0].metric_name == "compression_ratio"
