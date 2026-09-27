"""
Assembles a sequence of PNG frames (each held for its move's duration) into
an MP4 with FFmpeg, optionally muxing a narration track.

Kept deliberately simple and subprocess-based (no MoviePy in the hot path)
so behavior on Railway's slim containers is predictable: libx264, ultrafast,
yuv420p, faststart, threads pinned via settings.ffmpeg_threads.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass

from app.config import settings


@dataclass
class TimedFrame:
    path: str
    duration_sec: float


def _write_concat_file(frames: list[TimedFrame], list_path: str) -> None:
    with open(list_path, "w") as f:
        for tf in frames:
            f.write(f"file '{os.path.abspath(tf.path)}'\n")
            f.write(f"duration {tf.duration_sec}\n")


def build_video(
    frames: list[TimedFrame],
    output_path: str,
    audio_path: str | None = None,
    fps: int = 30,
) -> str:
    if not frames:
        raise ValueError("No frames to render.")

    workdir = os.path.dirname(output_path) or "."
    list_path = os.path.join(workdir, "concat_list.txt")
    _write_concat_file(frames, list_path)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_path,
    ]
    if audio_path:
        cmd += ["-i", audio_path]

    cmd += [
        "-r", str(fps),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-threads", str(settings.ffmpeg_threads),
    ]
    if audio_path:
        cmd += ["-c:a", "aac", "-shortest"]

    cmd.append(output_path)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed (code {proc.returncode}). Consider reducing duration/moves/board "
            f"size per the QUALITY RULES.\nstderr tail:\n{proc.stderr[-2000:]}"
        )
    return output_path


def probe_duration_sec(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return 0.0
    try:
        return float(json.loads(proc.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def crop_segment(input_path: str, output_path: str, start_sec: float, end_sec: float,
                  vertical: bool = False) -> str:
    """Cut [start_sec, end_sec] out of a long video, optionally reframing to 9:16 for Shorts."""
    duration = max(0.1, end_sec - start_sec)
    cmd = ["ffmpeg", "-y", "-ss", str(start_sec), "-i", input_path, "-t", str(duration)]
    if vertical:
        # center-crop the 16:9 source into a 9:16 canvas with blurred padding
        vf = (
            "split[bg][fg];"
            "[bg]scale=1080:1920,boxblur=20:5[bgblur];"
            "[fg]scale=1080:-1[fgscaled];"
            "[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2"
        )
        cmd += ["-vf", vf]
    cmd += [
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-threads", str(settings.ffmpeg_threads),
        "-c:a", "aac",
        output_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg crop failed: {proc.stderr[-1500:]}")
    return output_path
