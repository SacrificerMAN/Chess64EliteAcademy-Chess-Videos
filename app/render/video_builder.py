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


def build_move_click_track(
    move_timestamps_sec: list[float],
    total_duration_sec: float,
    out_path: str,
    click_freq_hz: int = 1500,
    click_len_sec: float = 0.06,
) -> str:
    """
    Synthesizes a short percussive "click" at each move timestamp and mixes
    them into one audio track spanning the whole video. No external sound
    asset needed — each click is a synthesized sine blip with a fast fade,
    generated entirely by ffmpeg's lavfi source. Silence-only track if there
    are no timestamps (still returns a valid, playable file).
    """
    if not move_timestamps_sec:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", str(total_duration_sec), "-c:a", "aac", out_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg silence track failed: {proc.stderr[-1500:]}")
        return out_path

    inputs: list[str] = []
    filter_parts: list[str] = []
    for i, ts in enumerate(move_timestamps_sec):
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={click_freq_hz}:duration={click_len_sec}"]
        delay_ms = max(0, int(ts * 1000))
        filter_parts.append(
            f"[{i}:a]volume=0.55,afade=t=out:st=0:d={click_len_sec},"
            f"adelay={delay_ms}|{delay_ms}[c{i}]"
        )
    mix_inputs = "".join(f"[c{i}]" for i in range(len(move_timestamps_sec)))
    filter_complex = ";".join(filter_parts) + (
        f";{mix_inputs}amix=inputs={len(move_timestamps_sec)}:duration=longest:normalize=0,"
        f"apad=whole_dur={total_duration_sec}[mixed]"
    )
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[mixed]",
        "-t", str(total_duration_sec),
        "-c:a", "aac",
        out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg click track failed: {proc.stderr[-1500:]}")
    return out_path


def mix_audio_tracks(track_paths: list[str], out_path: str) -> str:
    """Mixes 2+ audio tracks (e.g. move clicks + narration) down to one."""
    tracks = [t for t in track_paths if t]
    if len(tracks) == 1:
        import shutil as _shutil

        _shutil.copy(tracks[0], out_path)
        return out_path
    cmd = ["ffmpeg", "-y"]
    for t in tracks:
        cmd += ["-i", t]
    cmd += [
        "-filter_complex", f"amix=inputs={len(tracks)}:duration=longest:normalize=0",
        "-c:a", "aac", out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg audio mix failed: {proc.stderr[-1500:]}")
    return out_path
