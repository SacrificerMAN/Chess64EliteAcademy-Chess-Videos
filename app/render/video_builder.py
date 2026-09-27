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
    click_asset_path: str | None = None,
) -> str:
    """
    Builds one audio track spanning the whole video with a "move" sound at
    each timestamp.

    If `click_asset_path` points to a real audio file (e.g. a royalty-free
    or licensed "chess move" sound you've added under assets/audio/), that
    file is used verbatim, reused at every move timestamp. We deliberately
    do NOT fetch or bundle Chess.com's own sound — it's their proprietary
    asset. Without a supplied asset, a synthesized two-layer "wood knock"
    (low sine thump + filtered noise tick, both with a fast decay envelope)
    is generated instead — built from scratch, not sampled from anywhere.
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

    n = len(move_timestamps_sec)
    delays_ms = [max(0, int(ts * 1000)) for ts in move_timestamps_sec]

    if click_asset_path and os.path.isfile(click_asset_path):
        # Read the asset once, split into N copies, delay each to its
        # timestamp, then mix — avoids opening the file N separate times.
        split_labels = "".join(f"[s{i}]" for i in range(n))
        delay_parts = [
            f"[s{i}]adelay={d}|{d}[c{i}]" for i, d in enumerate(delays_ms)
        ]
        mix_inputs = "".join(f"[c{i}]" for i in range(n))
        filter_complex = (
            f"[0:a]asplit={n}{split_labels};"
            + ";".join(delay_parts)
            + f";{mix_inputs}amix=inputs={n}:duration=longest:normalize=0,"
            f"apad=whole_dur={total_duration_sec}[mixed]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", click_asset_path,
            "-filter_complex", filter_complex,
            "-map", "[mixed]", "-t", str(total_duration_sec), "-c:a", "aac", out_path,
        ]
    else:
        # Synthesized "wood knock": low-frequency thump + short filtered
        # noise burst, both with a fast decay so it reads as percussive
        # rather than tonal.
        inputs: list[str] = []
        filter_parts: list[str] = []
        for i, d in enumerate(delays_ms):
            inputs += ["-f", "lavfi", "-i", "sine=frequency=180:duration=0.05"]
            inputs += ["-f", "lavfi", "-i", "anoisesrc=color=white:duration=0.035:sample_rate=44100"]
            thump_idx, tick_idx = 2 * i, 2 * i + 1
            filter_parts.append(
                f"[{thump_idx}:a]volume=0.8,afade=t=out:st=0:d=0.05,adelay={d}|{d}[thump{i}]"
            )
            filter_parts.append(
                f"[{tick_idx}:a]highpass=f=1200,lowpass=f=5000,volume=0.5,"
                f"afade=t=out:st=0:d=0.03,adelay={d}|{d}[tick{i}]"
            )
        mix_inputs = "".join(f"[thump{i}][tick{i}]" for i in range(n))
        filter_complex = ";".join(filter_parts) + (
            f";{mix_inputs}amix=inputs={2 * n}:duration=longest:normalize=0,"
            f"alimiter=limit=0.9,apad=whole_dur={total_duration_sec}[mixed]"
        )
        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "[mixed]", "-t", str(total_duration_sec), "-c:a", "aac", out_path,
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
