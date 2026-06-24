"""FFmpeg subprocess runner with timeout and safe argument handling."""

import logging
import subprocess
import sys

from app.config import settings
from app.utils.exceptions import FFmpegTimeoutError

logger = logging.getLogger(__name__)


def run_ffmpeg(args: list[str], timeout: int | None = None) -> str:
    """Execute an FFmpeg command as a subprocess with a timeout.

    All arguments are passed as a list (``shell=False``) to prevent shell
    injection.  The process is killed and ``FFmpegTimeoutError`` raised if
    execution exceeds the timeout.

    Args:
        args: Full command line as a list (e.g. ``["ffmpeg", "-version"]``).
        timeout: Maximum wall-clock seconds.  Defaults to
            ``settings.ffmpeg_timeout_seconds``.

    Returns:
        Combined stdout+stderr output as a string.

    Raises:
        FFmpegTimeoutError: If the process does not finish within the timeout.
        subprocess.CalledProcessError: If ffmpeg returns a non-zero exit code
            (but this can be caught by callers that expect failures).
    """
    effective_timeout = timeout if timeout is not None else settings.ffmpeg_timeout_seconds
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            shell=False,
        )
        if proc.returncode != 0:
            msg = f"FFmpeg failed (exit {proc.returncode}): {proc.stderr.strip()}"
            logger.error(msg)
            raise subprocess.CalledProcessError(
                proc.returncode, args, output=proc.stdout, stderr=proc.stderr
            )
        return (proc.stdout + "\n" + proc.stderr).strip()
    except subprocess.TimeoutExpired:
        raise FFmpegTimeoutError(
            f"FFmpeg process timed out after {effective_timeout}s"
        )
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg executable not found. Ensure FFmpeg is installed and on PATH."
        )
