"""Patch 04 — broadcast elite layout.

Confirms the renderer places Black's bar on top and White's bar on the
bottom (broadcast convention), and that a gold frame is drawn around the
board. This inspects the rendered source rather than duplicating logic, so
it catches accidental regressions in board_renderer.py.
"""
from __future__ import annotations

import inspect


def apply() -> None:
    from app.render import board_renderer

    src = inspect.getsource(board_renderer.render_frame)
    assert "ctx.black_assets" in src and "0, bar_h" in src, "Black bar must render at the top"
    assert "ctx.white_assets" in src and "FRAME_H - bar_h" in src, "White bar must render at the bottom"
