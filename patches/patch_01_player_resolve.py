"""Patch 01 — player resolve fixes.

Sanity-checks the KNOWN_USERNAMES map (no blank usernames, valid 2-letter
flag codes) so a bad entry fails fast at deploy time instead of silently
breaking avatar resolution mid-job.
"""
from __future__ import annotations


def apply() -> None:
    from app.player_assets import KNOWN_USERNAMES

    for name, entry in KNOWN_USERNAMES.items():
        assert entry.get("chesscom"), f"KNOWN_USERNAMES['{name}'] missing chesscom username"
        flag = entry.get("flag", "")
        assert len(flag) == 2 and flag.isalpha(), f"KNOWN_USERNAMES['{name}'] has bad flag '{flag}'"
