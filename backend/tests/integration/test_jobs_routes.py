"""Integration tests for job routes (API-06, API-07, API-08, API-09)."""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Job, Metric
from app.infra.storage import save_result


class TestGetJob:
    def test_known_job_returns_200(self, client: TestClient, sample_job: dict) -> None:
        resp = client.get(f"/api/v1/jobs/{sample_job['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"] == sample_job["id"]
        assert body["status"] == "done"

    def test_unknown_job_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/nonexistent-id")
        assert resp.status_code == 404


class TestDownloadJobResult:
    def test_download_without_result_returns_404(
        self, client: TestClient, sample_job: dict
    ) -> None:
        assert sample_job["result_path"] is None
        resp = client.get(f"/api/v1/jobs/{sample_job['id']}/download")
        assert resp.status_code == 404

    def test_download_with_result_returns_file(
        self, client: TestClient, db_session: Session, sample_job: dict
    ) -> None:
        result_path = save_result(sample_job["id"], ".txt", b"hello world")
        from app.services.job_service import update_job_status

        update_job_status(
            db_session,
            sample_job["id"],
            status="done",
            result_path=result_path,
        )
        resp = client.get(f"/api/v1/jobs/{sample_job['id']}/download")
        assert resp.status_code == 200
        assert resp.content == b"hello world"

    def test_download_unknown_job_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/no-such-job/download")
        assert resp.status_code == 404


class TestDeleteJob:
    def test_delete_removes_files_and_marks_deleted(
        self, client: TestClient, db_session: Session, sample_job: dict
    ) -> None:
        save_result(sample_job["id"], ".txt", b"data")
        resp = client.delete(f"/api/v1/jobs/{sample_job['id']}")
        assert resp.status_code == 204

        get_resp = client.get(f"/api/v1/jobs/{sample_job['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "deleted"

        job_dir = Path("storage") / sample_job["id"]
        assert not job_dir.exists()

    def test_delete_unknown_job_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/api/v1/jobs/no-such-job")
        assert resp.status_code == 404


class TestListJobs:
    def test_pagination_respects_limit(
        self, client: TestClient, db_session: Session
    ) -> None:
        from app.db.models import Job
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        for i in range(3):
            job = Job(
                id=f"list-job-{i:03d}",
                media_type="image",
                operation="compress",
                status="pending",
                original_filename=f"f{i}.png",
                original_path=f"/tmp/f{i}.png",
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(hours=24),
            )
            db_session.add(job)
        db_session.commit()

        resp = client.get("/api/v1/jobs?limit=2&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["jobs"]) == 2
        assert body["total"] == 3
        assert body["limit"] == 2
        assert body["offset"] == 0

    def test_empty_list(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs")
        assert resp.status_code == 200
        body = resp.json()
        assert body["jobs"] == []
        assert body["total"] == 0
