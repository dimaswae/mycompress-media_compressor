"""Integration tests for CORS middleware (API-10).

Verifies that preflight ``OPTIONS`` requests from allowed origins receive
the appropriate CORS headers.
"""

from fastapi.testclient import TestClient


class TestCORS:
    def test_preflight_from_allowed_origin(self, client: TestClient) -> None:
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
        assert "GET" in resp.headers.get("access-control-allow-methods", "")

    def test_preflight_from_disallowed_origin(self, client: TestClient) -> None:
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") is None

    def test_response_has_cors_headers(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
