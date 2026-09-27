"""Patch 03 — pro studio look.

Verifies every board theme defines light/dark/highlight colors, and that
the studio canvas color is a deep navy (not pure black), per QUALITY RULES.
"""
from __future__ import annotations


def apply() -> None:
    from app.config import settings

    for theme, colors in settings.THEMES.items():
        for key in ("light", "dark", "highlight"):
            assert key in colors, f"Theme '{theme}' missing '{key}' color"

    assert settings.NAVY_BG.lower() != "#000000", "Studio background must be deep navy, not pure black"
