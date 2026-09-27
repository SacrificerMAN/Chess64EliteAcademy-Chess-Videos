"""Optional voice commentary via edge-tts (free Microsoft neural voices)."""
from __future__ import annotations

import asyncio
import logging
import os

import edge_tts

logger = logging.getLogger("chess64.tts")

DEFAULT_VOICE = "en-US-ChristopherNeural"
DEFAULT_RATE = "+8%"  # "slightly up" per spec


async def _synthesize(text: str, out_path: str, voice: str, rate: str) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(out_path)


def synthesize_commentary(lines: list[dict], out_path: str, voice: str = DEFAULT_VOICE,
                           rate: str = DEFAULT_RATE) -> str | None:
    """
    lines: [{"ply": int, "line": str}, ...] (empty "line" entries are skipped)
    Returns the audio path, or None if synthesis failed (fail soft — video
    still renders with move clicks only).
    """
    script = " ... ".join(l["line"] for l in lines if l.get("line"))
    if not script.strip():
        return None
    try:
        asyncio.run(_synthesize(script, out_path, voice, rate))
        if not os.path.isfile(out_path) or os.path.getsize(out_path) < 500:
            logger.warning("TTS output missing/too small; skipping narration")
            try:
                os.remove(out_path)
            except OSError:
                pass
            return None
        with open(out_path, "rb") as f:
            head = f.read(4)
        if not (head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0)):
            logger.warning("TTS output not valid audio; skipping narration")
            try:
                os.remove(out_path)
            except OSError:
                pass
            return None
        return out_path
    except Exception as exc:
        logger.warning("TTS synthesis failed, continuing with clicks only: %s", exc)
        return None
