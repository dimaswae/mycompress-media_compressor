"""Integration tests for image endpoints (IMG-22/23/24/25/26)."""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session


def _make_test_png_bytes(size: int = 8) -> bytes:
    """Generate a small solid-color PNG image as bytes."""
    img = Image.new("RGB", (size, size), color=(64, 128, 192))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_test_jpg_bytes(size: int = 16) -> bytes:
    """Generate a small solid-color JPEG image as bytes."""
    img = Image.new("RGB", (size, size), color=(64, 128, 192))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ────────────────────────────── compress ──────────────────────────────


class TestCompressEndpoint:
    def test_compress_png_with_rle(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        resp = client.post(
            "/api/v1/image/compress",
            files={"file": ("test.png", png, "image/png")},
            data={"algorithm": "rle"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "done"
        assert "job_id" in body
        assert body["metrics"]["compression_ratio"] > 0
        assert "processing_time_ms" in body["metrics"]
        assert "psnr" in body["metrics"]

    def test_compress_png_with_huffman(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        resp = client.post(
            "/api/v1/image/compress",
            files={"file": ("test.png", png, "image/png")},
            data={"algorithm": "huffman"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"

    def test_compress_jpg_with_rle(self, client: TestClient) -> None:
        jpg = _make_test_jpg_bytes()
        resp = client.post(
            "/api/v1/image/compress",
            files={"file": ("test.jpg", jpg, "image/jpeg")},
            data={"algorithm": "rle"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"

    def test_compress_unknown_algorithm_returns_400(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        resp = client.post(
            "/api/v1/image/compress",
            files={"file": ("test.png", png, "image/png")},
            data={"algorithm": "unknown"},
        )
        assert resp.status_code == 400, resp.text

    def test_compress_invalid_extension_returns_400(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        resp = client.post(
            "/api/v1/image/compress",
            files={"file": ("test.txt", png, "text/plain")},
            data={"algorithm": "rle"},
        )
        assert resp.status_code == 400, resp.text


# ────────────────────────────── decompress ──────────────────────────────


class TestDecompressEndpoint:
    def test_decompress_rle_roundtrip(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        comp_resp = client.post(
            "/api/v1/image/compress",
            files={"file": ("test.png", png, "image/png")},
            data={"algorithm": "rle"},
        )
        assert comp_resp.status_code == 200
        job_id = comp_resp.json()["job_id"]

        # download compressed file
        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        compressed_bytes = dl_resp.content

        # now decompress
        decomp_resp = client.post(
            "/api/v1/image/decompress",
            files={"file": ("data.cmp", compressed_bytes, "application/octet-stream")},
            data={"algorithm": "rle"},
        )
        assert decomp_resp.status_code == 200, decomp_resp.text
        assert decomp_resp.json()["status"] == "done"

    def test_decompress_bad_data_returns_500(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/image/decompress",
            files={"file": ("bad.cmp", b"not compressed data", "application/octet-stream")},
            data={"algorithm": "rle"},
        )
        assert resp.status_code == 500 or resp.status_code == 400, resp.text

    def test_decompress_unknown_algorithm_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/image/decompress",
            files={"file": ("data.cmp", b"some data", "application/octet-stream")},
            data={"algorithm": "bogus"},
        )
        assert resp.status_code == 400, resp.text


# ────────────────────────────── embed ──────────────────────────────


class TestEmbedEndpoint:
    def test_embed_without_compression(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.png", png, "image/png")},
            data={"message": "hello world", "password": "", "algorithm": ""},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "done"
        assert "hidden_capacity_bits" in body["metrics"]

    def test_embed_with_password(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.png", png, "image/png")},
            data={"message": "secret", "password": "p@ssw0rd", "algorithm": ""},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"

    def test_embed_with_rle_compression(self, client: TestClient) -> None:
        png = _make_test_png_bytes(size=32)
        resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.png", png, "image/png")},
            data={"message": "secret message", "password": "", "algorithm": "rle"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"

    def test_embed_message_too_large_returns_400(self, client: TestClient) -> None:
        png = _make_test_png_bytes(size=4)
        resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.png", png, "image/png")},
            data={"message": "A" * 100, "password": "", "algorithm": ""},
        )
        assert resp.status_code == 400, resp.text

    def test_embed_invalid_file_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            data={"message": "hi", "password": "", "algorithm": ""},
        )
        assert resp.status_code == 400, resp.text


# ────────────────────────────── extract ──────────────────────────────


class TestExtractEndpoint:
    def test_extract_roundtrip(self, client: TestClient) -> None:
        png = _make_test_png_bytes(size=16)
        original_msg = "Hello, world!"
        emb_resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.png", png, "image/png")},
            data={"message": original_msg, "password": "", "algorithm": ""},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/image/extract",
            files={"file": ("stego.png", stego_bytes, "image/png")},
            data={"password": "", "algorithm": ""},
        )
        assert ext_resp.status_code == 200, ext_resp.text
        assert ext_resp.json()["message"] == original_msg

    def test_extract_with_password(self, client: TestClient) -> None:
        png = _make_test_png_bytes(size=16)
        emb_resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.png", png, "image/png")},
            data={"message": "hidden", "password": "correct", "algorithm": ""},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/image/extract",
            files={"file": ("stego.png", stego_bytes, "image/png")},
            data={"password": "correct", "algorithm": ""},
        )
        assert ext_resp.status_code == 200, ext_resp.text
        assert ext_resp.json()["message"] == "hidden"

    def test_extract_wrong_password_returns_400(self, client: TestClient) -> None:
        png = _make_test_png_bytes(size=16)
        emb_resp = client.post(
            "/api/v1/image/embed",
            files={"file": ("test.png", png, "image/png")},
            data={"message": "secret", "password": "correct", "algorithm": ""},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/image/extract",
            files={"file": ("stego.png", stego_bytes, "image/png")},
            data={"password": "wrong", "algorithm": ""},
        )
        assert ext_resp.status_code == 400, ext_resp.text

    def test_extract_from_clean_image_returns_200_empty_400(
        self, client: TestClient
    ) -> None:
        png = _make_test_png_bytes(size=16)
        ext_resp = client.post(
            "/api/v1/image/extract",
            files={"file": ("clean.png", png, "image/png")},
            data={"password": "", "algorithm": ""},
        )
        # clean image has random LSBs — may return empty (200) or raise (400)
        assert ext_resp.status_code in (200, 400), ext_resp.text


# ────────────────────────────── compare ──────────────────────────────


class TestCompareEndpoint:
    def test_compare_compress_job(self, client: TestClient) -> None:
        png = _make_test_png_bytes()
        comp_resp = client.post(
            "/api/v1/image/compress",
            files={"file": ("test.png", png, "image/png")},
            data={"algorithm": "rle"},
        )
        assert comp_resp.status_code == 200
        job_id = comp_resp.json()["job_id"]

        comp_meta_resp = client.get(f"/api/v1/image/{job_id}/compare")
        assert comp_meta_resp.status_code == 200, comp_meta_resp.text
        body = comp_meta_resp.json()
        assert body["job_id"] == job_id
        assert body["original_size"] > 0
        assert body["result_size"] > 0
        assert "psnr" in body["metrics"]
        assert "ssim" in body["metrics"]
        assert "mse" in body["metrics"]
        assert "compression_ratio" in body["metrics"]

    def test_compare_nonexistent_job_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/image/no-such-job/compare")
        assert resp.status_code == 404, resp.text
