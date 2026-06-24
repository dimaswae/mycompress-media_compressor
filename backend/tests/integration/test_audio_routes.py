"""Integration tests for audio endpoints (AUD-11/12/13/16/17)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


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


# ────────────────────────────── compress ──────────────────────────────


class TestCompressEndpoint:
    def test_compress_wav_success(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        with patch("app.services.audio_service.AudioBitrateCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-mp3-data"

            resp = client.post(
                "/api/v1/audio/compress",
                files={"file": ("test.wav", wav, "audio/wav")},
                data={"bitrate": "128k"},
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "done"
        assert "job_id" in body
        assert body["metrics"]["compression_ratio"] > 0
        assert "processing_time_ms" in body["metrics"]

    def test_compress_with_custom_bitrate(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        with patch("app.services.audio_service.AudioBitrateCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-mp3"

            resp = client.post(
                "/api/v1/audio/compress",
                files={"file": ("test.wav", wav, "audio/wav")},
                data={"bitrate": "64k"},
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"

    def test_compress_invalid_extension_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/audio/compress",
            files={"file": ("test.txt", b"data", "text/plain")},
            data={"bitrate": "128k"},
        )
        assert resp.status_code == 400, resp.text


# ────────────────────────────── decompress ──────────────────────────────


class TestDecompressEndpoint:
    def test_decompress_mp3_success(self, client: TestClient) -> None:
        mp3_bytes = b"\xff\xfb\x90\x00\x00\x00\x00\x00"
        with patch("app.services.audio_service.AudioBitrateCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.return_value = _make_wav_bytes()

            resp = client.post(
                "/api/v1/audio/decompress",
                files={"file": ("audio.mp3", mp3_bytes, "audio/mpeg")},
                data={"bitrate": "128k"},
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"
        assert "processing_time_ms" in resp.json()["metrics"]

    def test_decompress_bad_data_raises(self, client: TestClient) -> None:
        with patch("app.services.audio_service.AudioBitrateCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.side_effect = Exception("ffmpeg error")

            with pytest.raises(Exception):
                client.post(
                    "/api/v1/audio/decompress",
                    files={"file": ("bad.mp3", b"bad-data", "audio/mpeg")},
                    data={"bitrate": "128k"},
                )


# ────────────────────────────── embed ──────────────────────────────


class TestEmbedEndpoint:
    def test_embed_message_success(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        resp = client.post(
            "/api/v1/audio/embed",
            files={"file": ("test.wav", wav, "audio/wav")},
            data={"message": "hello world", "password": ""},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "done"
        assert "hidden_capacity_bits" in body["metrics"]

    def test_embed_with_password(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        resp = client.post(
            "/api/v1/audio/embed",
            files={"file": ("test.wav", wav, "audio/wav")},
            data={"message": "secret msg", "password": "p@ssw0rd"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "done"

    def test_embed_message_too_large_returns_400(self, client: TestClient) -> None:
        wav = _make_wav_bytes(duration_sec=0.02)
        resp = client.post(
            "/api/v1/audio/embed",
            files={"file": ("test.wav", wav, "audio/wav")},
            data={"message": "A" * 2000, "password": ""},
        )
        assert resp.status_code == 400, resp.text

    def test_embed_invalid_file_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/audio/embed",
            files={"file": ("test.txt", b"not a wav", "text/plain")},
            data={"message": "hi", "password": ""},
        )
        assert resp.status_code == 400, resp.text


# ────────────────────────────── extract ──────────────────────────────


class TestExtractEndpoint:
    def test_extract_roundtrip(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        original_msg = "Hello, WAV!"

        emb_resp = client.post(
            "/api/v1/audio/embed",
            files={"file": ("test.wav", wav, "audio/wav")},
            data={"message": original_msg, "password": ""},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/audio/extract",
            files={"file": ("stego.wav", stego_bytes, "audio/wav")},
            data={"password": ""},
        )
        assert ext_resp.status_code == 200, ext_resp.text
        assert ext_resp.json()["message"] == original_msg

    def test_extract_with_password(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        emb_resp = client.post(
            "/api/v1/audio/embed",
            files={"file": ("test.wav", wav, "audio/wav")},
            data={"message": "hidden", "password": "correct"},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/audio/extract",
            files={"file": ("stego.wav", stego_bytes, "audio/wav")},
            data={"password": "correct"},
        )
        assert ext_resp.status_code == 200, ext_resp.text
        assert ext_resp.json()["message"] == "hidden"

    def test_extract_wrong_password_returns_400(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        emb_resp = client.post(
            "/api/v1/audio/embed",
            files={"file": ("test.wav", wav, "audio/wav")},
            data={"message": "secret", "password": "correct"},
        )
        assert emb_resp.status_code == 200
        job_id = emb_resp.json()["job_id"]

        dl_resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert dl_resp.status_code == 200
        stego_bytes = dl_resp.content

        ext_resp = client.post(
            "/api/v1/audio/extract",
            files={"file": ("stego.wav", stego_bytes, "audio/wav")},
            data={"password": "wrong"},
        )
        assert ext_resp.status_code == 400, ext_resp.text

    def test_extract_from_clean_wav(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        ext_resp = client.post(
            "/api/v1/audio/extract",
            files={"file": ("clean.wav", wav, "audio/wav")},
            data={"password": ""},
        )
        assert ext_resp.status_code in (200, 400), ext_resp.text


# ────────────────────────────── compare ──────────────────────────────


class TestCompareEndpoint:
    def test_compare_compress_job(self, client: TestClient) -> None:
        wav = _make_wav_bytes()
        with patch("app.services.audio_service.AudioBitrateCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-mp3-data"

            comp_resp = client.post(
                "/api/v1/audio/compress",
                files={"file": ("test.wav", wav, "audio/wav")},
                data={"bitrate": "128k"},
            )
            assert comp_resp.status_code == 200
            job_id = comp_resp.json()["job_id"]

            comp_meta_resp = client.get(f"/api/v1/audio/{job_id}/compare")
            assert comp_meta_resp.status_code == 200, comp_meta_resp.text
            body = comp_meta_resp.json()
            assert body["job_id"] == job_id
            assert body["original_size"] > 0
            assert body["result_size"] > 0
            assert "compression_ratio" in body["metrics"]

    def test_compare_nonexistent_job_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/audio/no-such-job/compare")
        assert resp.status_code == 404, resp.text
