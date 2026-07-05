"""Tests for infra/ffmpeg_runner.py."""

import subprocess

import pytest

from app.utils.exceptions import FFmpegTimeoutError


class TestRunFFmpeg:
    """INF-09: run_ffmpeg()."""

    def test_success_path_with_python(self) -> None:
        """Use a harmless command (python --version) to verify the runner logic."""
        from app.infra.ffmpeg_runner import run_ffmpeg

        result = run_ffmpeg(["python", "--version"], timeout=10)
        assert "Python" in result

    def test_called_process_error(self) -> None:
        """A failing command should raise CalledProcessError."""
        from app.infra.ffmpeg_runner import run_ffmpeg

        with pytest.raises(subprocess.CalledProcessError):
            run_ffmpeg(["python", "-c", "import sys; sys.exit(1)"], timeout=5)

    def test_timeout_raised(self) -> None:
        """A timed-out process raises FFmpegTimeoutError."""
        from app.infra.ffmpeg_runner import run_ffmpeg

        with pytest.raises(FFmpegTimeoutError):
            run_ffmpeg(["python", "-c", "import time; time.sleep(10)"], timeout=1)

    def test_file_not_found(self) -> None:
        """A missing executable raises a RuntimeError."""
        from app.infra.ffmpeg_runner import run_ffmpeg

        with pytest.raises(RuntimeError, match="FFmpeg executable not found"):
            run_ffmpeg(["nonexistent-command-12345"], timeout=5)

    def test_default_timeout_from_settings(self) -> None:
        """When no timeout is passed, settings.ffmpeg_timeout_seconds is used."""
        from app.infra.ffmpeg_runner import run_ffmpeg

        result = run_ffmpeg(["python", "--version"])
        assert "Python" in result

    def test_stdout_and_stderr_combined(self) -> None:
        """Combined stdout+stderr should be returned."""
        from app.infra.ffmpeg_runner import run_ffmpeg

        result = run_ffmpeg(
            ["python", "-c", "import sys; print('out'); sys.stderr.write('err')"],
            timeout=5,
        )
        assert "out" in result
        assert "err" in result
