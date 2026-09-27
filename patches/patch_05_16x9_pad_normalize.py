"""Patch 05 — 16:9 pad + FFmpeg frame normalization.

Confirms FRAME_W/FRAME_H are 16:9 and even (yuv420p requirement), and that
normalize_frame is actually invoked at the end of render_frame/intro_card so
every exported PNG has consistent dimensions before hitting FFmpeg.
"""
from __future__ import annotations

import inspect


def apply() -> None:
    from app.render import board_renderer
    from app.utils import even

    w, h = board_renderer.FRAME_W, board_renderer.FRAME_H
    assert w == even(w) and h == even(h), "Frame dimensions must be even for yuv420p"
    assert abs((w / h) - (16 / 9)) < 0.01, "Frame must be 16:9"

    for fn in (board_renderer.render_frame, board_renderer.intro_card):
        src = inspect.getsource(fn)
        assert "normalize_frame(" in src, f"{fn.__name__} must call normalize_frame before returning"
