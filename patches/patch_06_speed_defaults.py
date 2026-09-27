"""Patch 06 — speed defaults for Railway.

Clamps duration/depth/move-limit settings into the safe ranges documented in
SPEED / LIMITS so a bad env var can't push a job past what a Railway free/
small instance can render in time.
"""
from __future__ import annotations


def apply() -> None:
    from app.config import settings

    if not (1 <= settings.default_duration_per_move <= 15):
        settings.default_duration_per_move = 4.0
    if not (1 <= settings.default_depth <= 20):
        settings.default_depth = 10
    if not (1 <= settings.max_moves_for_bot <= 80):
        settings.max_moves_for_bot = 40
    if settings.ffmpeg_threads < 1:
        settings.ffmpeg_threads = 1
