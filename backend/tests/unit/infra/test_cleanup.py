"""Tests for infra/cleanup.py — sweep_expired_jobs."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from app.db.models import Job


class TestSweepExpiredJobs:
    """INF-07: sweep_expired_jobs()."""

    def test_sweep_expired_job(self, db_session, expired_job: Job) -> None:
        """An expired job should be swept: status changed to expired."""
        from app.infra.cleanup import sweep_expired_jobs
        import app.infra.cleanup as cleanup_mod

        with patch.multiple(
            cleanup_mod,
            SessionLocal=lambda: db_session,
            delete_job_files=lambda job_id: None,
        ):
            count = sweep_expired_jobs()
            assert count == 1

        fetched = db_session.query(Job).filter(Job.id == expired_job.id).first()
        assert fetched is not None
        assert fetched.status == "expired"

    def test_sweep_skips_active_jobs(self, db_session) -> None:
        """Jobs with future expires_at should not be swept."""
        from app.infra.cleanup import sweep_expired_jobs
        import app.infra.cleanup as cleanup_mod

        job_id = str(uuid4())
        future = datetime.now(timezone.utc) + timedelta(hours=48)
        active_job = Job(
            id=job_id,
            media_type="image",
            operation="compress",
            status="done",
            original_filename="active.png",
            original_path=f"storage/{job_id}/original.png",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=future,
        )
        db_session.add(active_job)
        db_session.commit()

        with patch.multiple(
            cleanup_mod,
            SessionLocal=lambda: db_session,
            delete_job_files=lambda job_id: None,
        ):
            count = sweep_expired_jobs()
            assert count == 0

        fetched = db_session.query(Job).filter(Job.id == job_id).first()
        assert fetched is not None
        assert fetched.status == "done"

    def test_sweep_multiple_expired(self, db_session) -> None:
        from app.infra.cleanup import sweep_expired_jobs
        import app.infra.cleanup as cleanup_mod

        past = datetime.now(timezone.utc) - timedelta(hours=2)
        job_ids = []
        for i in range(3):
            jid = str(uuid4())
            job_ids.append(jid)
            j = Job(
                id=jid,
                media_type="image",
                operation="compress",
                status="done",
                original_filename=f"f{i}.png",
                original_path=f"storage/{jid}/original.png",
                created_at=past - timedelta(hours=1),
                updated_at=past,
                expires_at=past,
            )
            db_session.add(j)
        db_session.commit()

        with patch.multiple(
            cleanup_mod,
            SessionLocal=lambda: db_session,
            delete_job_files=lambda job_id: None,
        ):
            count = sweep_expired_jobs()
            assert count == 3

        for jid in job_ids:
            fetched = db_session.query(Job).filter(Job.id == jid).first()
            assert fetched is not None
            assert fetched.status == "expired"
