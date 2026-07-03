"""Integration tests for video endpoints (VID-14)."""

import struct
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def _make_mp4_bytes(mdat_payload_size: int = 200) -> bytes:
    """Generate a minimal MP4 byte string with ftyp + mdat boxes."""
    ftyp_content = b"mp42\x00\x00\x00\x00mp42mp41"
    ftyp_size = 8 + len(ftyp_content)
    ftyp = struct.pack(">I", ftyp_size) + b"ftyp" + ftyp_content

    mdat_payload = b"\x00" * mdat_payload_size
    mdat_size = 8 + len(mdat_payload)
    mdat = struct.pack(">I", mdat_size) + b"mdat" + mdat_payload

    return ftyp + mdat


# ────────────────────────────── compress ──────────────────────────────


class TestCompressEndpoint:
    def test_compress_mp4_success(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes()
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-compressed"

            resp = client.post(
                "/api/v1/video/compress",
                files={"file": ("test.mp4", mp4, "video/mp4")},
                data={"crf": "28"},
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["status"] == "done"
            assert "job_id" in body
            assert body["metrics"]["compression_ratio"] > 0
            assert "processing_time_ms" in body["metrics"]

    def test_compress_with_custom_crf(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes()
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-compressed"

            resp = client.post(
                "/api/v1/video/compress",
                files={"file": ("test.mp4", mp4, "video/mp4")},
                data={"crf": "35"},
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["status"] == "done"

    def test_compress_invalid_extension_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/video/compress",
            files={"file": ("test.txt", b"data", "text/plain")},
            data={"crf": "28"},
        )
        assert resp.status_code == 400, resp.text


# ────────────────────────────── decompress ──────────────────────────────


class TestDecompressEndpoint:
    def test_decompress_mp4_success(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes()
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.return_value = b"fake-decompressed"

            resp = client.post(
                "/api/v1/video/decompress",
                files={"file": ("video.mp4", mp4, "video/mp4")},
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["status"] == "done"
            assert "processing_time_ms" in resp.json()["metrics"]

    def test_decompress_failure_raises(self, client: TestClient) -> None:
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.side_effect = Exception("ffmpeg error")

            with pytest.raises(Exception):
                client.post(
                    "/api/v1/video/decompress",
                    files={"file": ("bad.mp4", b"bad-data", "video/mp4")},
                )


# ────────────────────────────── embed ──────────────────────────────


class TestEmbedEndpoint:
    def test_embed_message_success(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes()
        resp = client.post(
            "/api/v1/video/embed",
            files={"file": ("test.mp4", mp4, "video/mp4")},
            data={"message": "hello world", "password": ""},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "done"
        assert "hidden_capacity_bits" in body["metrics"]

    def test_embed_with_password(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes(mdat_payload_size=500)  # Larger for encrypted payload
        resp = client.post(
            "/api/v1/video/embed",
            files={"file": ("test.mp4", mp4, "video/mp4")},
            data={"message": "secret msg", "password": "p@ssw0rd"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"

    def test_embed_message_too_large_returns_400(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes(mdat_payload_size=20)
        resp = client.post(
            "/api/v1/video/embed",
            files={"file": ("test.mp4", mp4, "video/mp4")},
            data={"message": "A" * 2000, "password": ""},
        )
        assert resp.status_code == 400, resp.text

    def test_embed_invalid_file_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/video/embed",
            files={"file": ("test.txt", b"not an mp4", "text/plain")},
            data={"message": "hi", "password": ""},
        )
        assert resp.status_code == 400, resp.text


# ────────────────────────────── extract ──────────────────────────────


class TestExtractEndpoint:
    def test_extract_roundtrip(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes()
        original_msg = "Hello, MP4!"

        emb_resp = client.post(
            "/api/v1/video/embed",
            files={"file": ("test.mp4", mp4, "video/mp4")},
            data={"message": original_msg, "password": ""},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/video/extract",
            files={"file": ("stego.mp4", stego_bytes, "video/mp4")},
            data={"password": ""},
        )
        assert ext_resp.status_code == 200, ext_resp.text
        assert ext_resp.json()["message"] == original_msg

    def test_extract_with_password(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes(mdat_payload_size=500)  # Larger for encrypted payload
        emb_resp = client.post(
            "/api/v1/video/embed",
            files={"file": ("test.mp4", mp4, "video/mp4")},
            data={"message": "hidden", "password": "correct"},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/video/extract",
            files={"file": ("stego.mp4", stego_bytes, "video/mp4")},
            data={"password": "correct"},
        )
        assert ext_resp.status_code == 200, ext_resp.text
        assert ext_resp.json()["message"] == "hidden"

    def test_extract_wrong_password_returns_400(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes(mdat_payload_size=500)  # Larger for encrypted payload
        emb_resp = client.post(
            "/api/v1/video/embed",
            files={"file": ("test.mp4", mp4, "video/mp4")},
            data={"message": "secret", "password": "correct"},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/video/extract",
            files={"file": ("stego.mp4", stego_bytes, "video/mp4")},
            data={"password": "wrong"},
        )
        assert ext_resp.status_code == 400, ext_resp.text

    def test_extract_from_clean_mp4(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes()
        ext_resp = client.post(
            "/api/v1/video/extract",
            files={"file": ("clean.mp4", mp4, "video/mp4")},
            data={"password": ""},
        )
        assert ext_resp.status_code in (200, 400), ext_resp.text


# ────────────────────────────── compare ──────────────────────────────


class TestCompareEndpoint:
    def test_compare_compress_job(self, client: TestClient) -> None:
        mp4 = _make_mp4_bytes()
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-compressed"

            comp_resp = client.post(
                "/api/v1/video/compress",
                files={"file": ("test.mp4", mp4, "video/mp4")},
                data={"crf": "28"},
            )
            assert comp_resp.status_code == 200
            job_id = comp_resp.json()["job_id"]

            comp_meta_resp = client.get(f"/api/v1/video/{job_id}/compare")
            assert comp_meta_resp.status_code == 200, comp_meta_resp.text
            body = comp_meta_resp.json()
            assert body["job_id"] == job_id
            assert body["original_size"] > 0
            assert body["result_size"] > 0
            assert "compression_ratio" in body["metrics"]

    def test_compare_nonexistent_job_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/video/no-such-job/compare")
        assert resp.status_code == 404, resp.text