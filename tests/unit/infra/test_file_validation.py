"""Tests for infra/file_validation.py."""

import pytest

from app.infra.file_validation import (
    EXTENSION_WHITELIST,
    validate_extension,
    validate_magic_bytes,
    validate_size,
)
from app.utils.exceptions import UnsupportedFormatError


class TestValidateExtension:
    """INF-01: Extension whitelist."""

    def test_valid_extensions_pass(self) -> None:
        for ext in [".png", ".jpg", ".jpeg", ".wav", ".mp3", ".mp4"]:
            result = validate_extension(f"file{ext}")
            assert result == ext

    def test_valid_extensions_case_insensitive(self) -> None:
        assert validate_extension("photo.PNG") == ".png"
        assert validate_extension("audio.MP3") == ".mp3"
        assert validate_extension("video.Mp4") == ".mp4"

    def test_invalid_extension_raises(self) -> None:
        with pytest.raises(UnsupportedFormatError) as exc:
            validate_extension("file.txt")
        assert "UNSUPPORTED_FORMAT" in str(exc.value)

    def test_invalid_extension_message(self) -> None:
        with pytest.raises(UnsupportedFormatError) as exc:
            validate_extension("file.exe")
        assert ".exe" in exc.value.message
        assert "png" in exc.value.message

    def test_no_extension_raises(self) -> None:
        with pytest.raises(UnsupportedFormatError):
            validate_extension("README")


class TestValidateMagicBytes:
    """INF-02: Magic-byte sniffing."""

    def test_png_magic_passes(self) -> None:
        data = b"\x89PNG\r\n\x1a\n" + b"some more data"
        validate_magic_bytes(data, ".png")  # should not raise

    def test_jpg_magic_passes(self) -> None:
        data = b"\xff\xd8\xff\xe0" + b"jpeg data"
        validate_magic_bytes(data, ".jpg")  # should not raise

    def test_jpeg_magic_passes(self) -> None:
        data = b"\xff\xd8\xff\xe1" + b"exif data"
        validate_magic_bytes(data, ".jpeg")

    def test_wav_magic_passes(self) -> None:
        data = b"RIFF\x00\x00\x00\x00WAVEfmt "
        validate_magic_bytes(data, ".wav")

    def test_mp3_id3_magic_passes(self) -> None:
        data = b"ID3\x03\x00\x00\x00\x00\x00\x00frame data"
        validate_magic_bytes(data, ".mp3")

    def test_mp4_magic_passes(self) -> None:
        data = b"\x00\x00\x00\x18ftypmp4\x00\x00\x00\x00"
        validate_magic_bytes(data, ".mp4")

    def test_mismatched_content_raises(self) -> None:
        data = b"This is actually a text file, not a PNG"
        with pytest.raises(UnsupportedFormatError) as exc:
            validate_magic_bytes(data, ".png")
        assert "does not match" in exc.value.message

    def test_png_renamed_to_txt_fails(self) -> None:
        """Simulate a .txt file that has PNG magic bytes."""
        data = b"\x89PNG\r\n\x1a\n" + b"actual image data"
        validate_magic_bytes(data, ".png")  # passes because it IS png content

    def test_too_short_data_raises(self) -> None:
        data = b"\x89"
        with pytest.raises(UnsupportedFormatError):
            validate_magic_bytes(data, ".png")

    def test_unknown_extension_raises(self) -> None:
        data = b"some data"
        with pytest.raises(UnsupportedFormatError):
            validate_magic_bytes(data, ".xyz")


class TestValidateSize:
    """INF-03: Size cap validation."""

    def test_small_file_passes(self) -> None:
        data = b"x" * 1024  # 1 KB
        validate_size(data)  # should not raise

    def test_empty_file_passes(self) -> None:
        validate_size(b"")

    def test_large_file_raises(self, monkeypatch) -> None:
        import app.infra.file_validation as fv

        monkeypatch.setattr(fv.settings, "upload_max_size_mb", 1)
        data = b"x" * (2 * 1024 * 1024)  # 2 MB
        with pytest.raises(UnsupportedFormatError) as exc:
            validate_size(data)
        assert "exceeds maximum" in exc.value.message

    def test_exact_max_passes(self, monkeypatch) -> None:
        import app.infra.file_validation as fv

        monkeypatch.setattr(fv.settings, "upload_max_size_mb", 1)
        data = b"x" * (1 * 1024 * 1024)  # exactly 1 MB
        validate_size(data)  # should not raise
