"""
Builds Shorts/Reels cuts from the finished long video by locating critical
moments (sharp eval swings, mates, sacrifices) and cropping vertical clips
around them. Designed to fail soft: any error here must never fail the long
video job (per QUALITY RULES).
"""
from __future__ import annotations

import logging
import os

from app.analysis import GameData, eval_swings
from app.render.video_builder import crop_segment

logger = logging.getLogger("chess64.shorts")


def build_shorts(
    long_video_path: str,
    game: GameData,
    per_move_duration: float,
    intro_offset_sec: float,
    output_dir: str,
    max_clips: int = 3,
    pad_before: float = 6.0,
    pad_after: float = 4.0,
) -> list[str]:
    outputs: list[str] = []
    try:
        swing_idxs = eval_swings(game)[:max_clips] or list(range(min(max_clips, len(game.moves))))
        for n, idx in enumerate(swing_idxs, start=1):
            center_sec = intro_offset_sec + idx * per_move_duration
            start = max(0.0, center_sec - pad_before)
            end = center_sec + pad_after
            out_path = os.path.join(output_dir, f"short_{n}.mp4")
            crop_segment(long_video_path, out_path, start, end, vertical=True)
            outputs.append(out_path)
    except Exception as exc:  # fail soft — never kill the long video job
        logger.warning("Shorts generation failed, continuing without shorts: %s", exc)
    return outputs
