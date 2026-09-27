"""Patch 10 — start.

Final readiness check before scripts/start.sh launches the two Railway
processes: work directory is writable, ffmpeg is on PATH (required), and
Stockfish is on PATH (optional — analysis degrades gracefully without it,
but we want a loud warning rather than silent degradation).
"""
from __future__ import annotations

import logging
import os
import shutil

logger = logging.getLogger("chess64.patches")


def apply() -> None:
    from app.config import settings

    os.makedirs(settings.workdir, exist_ok=True)
    test_file = os.path.join(settings.workdir, ".write_test")
    with open(test_file, "w") as f:
        f.write("ok")
    os.remove(test_file)

    assert shutil.which("ffmpeg"), "ffmpeg is required and was not found on PATH"

    if not shutil.which("stockfish"):
        logger.warning(
            "Stockfish not found on PATH — jobs will render without eval bars, "
            "best-move arrows, or eval-swing-based Shorts selection."
        )

    logger.info("✅ Chess64 Elite Academy ready to start.")
