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
    """Build one audio track with a click at each timestamp."""
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

    if click_asset_path and os.path.isfile(click_asset_path) and os.path.getsize(click_asset_path) >= 500:
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
        # Soft wood knock for normal moves
        inputs: list[str] = []
        filter_parts: list[str] = []
        for i, d in enumerate(delays_ms):
            inputs += ["-f", "lavfi", "-i", "sine=frequency=180:duration=0.05"]
            inputs += ["-f", "lavfi", "-i", "anoisesrc=color=white:duration=0.035:sample_rate=44100"]
            thump_idx, tick_idx = 2 * i, 2 * i + 1
            filter_parts.append(
                f"[{thump_idx}:a]volume=0.55,afade=t=out:st=0:d=0.05,adelay={d}|{d}[thump{i}]"
            )
            filter_parts.append(
                f"[{tick_idx}:a]highpass=f=1200,lowpass=f=5000,volume=0.35,"
                f"afade=t=out:st=0:d=0.03,adelay={d}|{d}[tick{i}]"
            )
        mix_inputs = "".join(f"[thump{i}][tick{i}]" for i in range(n))
        filter_complex = ";".join(filter_parts) + (
            f";{mix_inputs}amix=inputs={2 * n}:duration=longest:normalize=0,"
            f"alimiter=limit=0.85,apad=whole_dur={total_duration_sec}[mixed]"
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


def _build_synth_kind(
    timestamps_sec: list[float],
    total_duration_sec: float,
    out_path: str,
    kind: str = "capture",
) -> str:
    """Loud capture thud or bright check ping when asset missing."""
    delays_ms = [max(0, int(ts * 1000)) for ts in timestamps_sec]
    n = len(delays_ms)
    if not n:
        return build_move_click_track([], total_duration_sec, out_path, None)

    inputs: list[str] = []
    filter_parts: list[str] = []

    if kind == "check":
        for i, d in enumerate(delays_ms):
            inputs += ["-f", "lavfi", "-i", "sine=frequency=880:duration=0.06"]
            inputs += ["-f", "lavfi", "-i", "sine=frequency=1320:duration=0.05"]
            a, b = 2 * i, 2 * i + 1
            filter_parts.append(
                f"[{a}:a]volume=1.2,afade=t=out:st=0:d=0.06,adelay={d}|{d}[a{i}]"
            )
            filter_parts.append(
                f"[{b}:a]volume=0.9,afade=t=out:st=0:d=0.05,adelay={d+40}|{d+40}[b{i}]"
            )
        mix_inputs = "".join(f"[a{i}][b{i}]" for i in range(n))
        n_in = 2 * n
    else:
        # capture: deep thud + sharp noise slap
        for i, d in enumerate(delays_ms):
            inputs += ["-f", "lavfi", "-i", "sine=frequency=70:duration=0.12"]
            inputs += ["-f", "lavfi", "-i", "sine=frequency=140:duration=0.08"]
            inputs += ["-f", "lavfi", "-i", "anoisesrc=color=white:duration=0.06:sample_rate=44100"]
            a, b, c = 3 * i, 3 * i + 1, 3 * i + 2
            filter_parts.append(
                f"[{a}:a]volume=1.6,afade=t=out:st=0:d=0.12,adelay={d}|{d}[a{i}]"
            )
            filter_parts.append(
                f"[{b}:a]volume=1.2,afade=t=out:st=0:d=0.08,adelay={d}|{d}[b{i}]"
            )
            filter_parts.append(
                f"[{c}:a]highpass=f=1000,lowpass=f=8000,volume=1.1,"
                f"afade=t=out:st=0:d=0.05,adelay={d}|{d}[c{i}]"
            )
        mix_inputs = "".join(f"[a{i}][b{i}][c{i}]" for i in range(n))
        n_in = 3 * n

    filter_complex = ";".join(filter_parts) + (
        f";{mix_inputs}amix=inputs={n_in}:duration=longest:normalize=0,"
        f"alimiter=limit=0.98,apad=whole_dur={total_duration_sec}[mixed]"
    )
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[mixed]", "-t", str(total_duration_sec), "-c:a", "aac", out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg {kind} synth failed: {proc.stderr[-1500:]}")
    return out_path


def build_typed_move_sounds(
    events: list[tuple[float, str]],
    total_duration_sec: float,
    out_path: str,
    move_path: str | None = None,
    capture_path: str | None = None,
    check_path: str | None = None,
) -> str:
    """events: (timestamp_sec, kind) with kind in move|capture|check.

    CRITICAL: capture sound plays ONLY for kind=='capture'.
    Move and capture assets must be different files.
    """
    if not events:
        return build_move_click_track([], total_duration_sec, out_path, None)

    by_kind: dict[str, list[float]] = {"move": [], "capture": [], "check": []}
    for ts, kind in events:
        k = kind if kind in by_kind else "move"
        by_kind[k].append(ts)

    def _ok(path: str | None) -> str | None:
        if path and os.path.isfile(path) and os.path.getsize(path) >= 500:
            return path
        return None

    move_p = _ok(move_path)
    cap_p = _ok(capture_path)
    chk_p = _ok(check_path)

    # Never let capture asset leak into move track
    if move_p and cap_p and os.path.abspath(move_p) == os.path.abspath(cap_p):
        print("[sound] WARN: move_path == capture_path; ignoring capture asset for safety")
        cap_p = None

    print(
        f"[sound] events move={len(by_kind['move'])} "
        f"capture={len(by_kind['capture'])} check={len(by_kind['check'])}"
    )
    print(f"[sound] paths move={move_p} capture={cap_p} check={chk_p}")

    partials: list[str] = []
    base = out_path + ".part"

    if by_kind["move"]:
        part = f"{base}_move.aac"
        # ALWAYS soft click for normal moves — never the capture asset
        build_move_click_track(by_kind["move"], total_duration_sec, part, move_p)
        partials.append(part)
        print(f"[sound] built MOVE track ({len(by_kind['move'])} clicks)")

    if by_kind["capture"]:
        part = f"{base}_capture.aac"
        if cap_p:
            print(f"[sound] CAPTURE using asset {cap_p} size={os.path.getsize(cap_p)}")
            build_move_click_track(by_kind["capture"], total_duration_sec, part, cap_p)
            # Boost so it stands out vs soft move click
            boosted = part + ".boost.aac"
            bp = subprocess.run(
                ["ffmpeg", "-y", "-i", part, "-filter:a", "volume=2.0", "-c:a", "aac", boosted],
                capture_output=True, text=True,
            )
            if bp.returncode == 0 and os.path.isfile(boosted):
                import shutil
                shutil.move(boosted, part)
                print("[sound] CAPTURE volume boosted 2.0x")
        else:
            print("[sound] CAPTURE using loud synth (no valid asset)")
            _build_synth_kind(by_kind["capture"], total_duration_sec, part, kind="capture")
        partials.append(part)
        print(f"[sound] built CAPTURE track ({len(by_kind['capture'])} hits)")

    if by_kind["check"]:
        part = f"{base}_check.aac"
        if chk_p:
            build_move_click_track(by_kind["check"], total_duration_sec, part, chk_p)
        else:
            _build_synth_kind(by_kind["check"], total_duration_sec, part, kind="check")
        partials.append(part)
        print(f"[sound] built CHECK track ({len(by_kind['check'])} hits)")

    if not partials:
        return build_move_click_track([], total_duration_sec, out_path, None)
    if len(partials) == 1:
        import shutil
        shutil.copy2(partials[0], out_path)
        return out_path
    return mix_audio_tracks(partials, out_path)


def mix_audio_tracks(track_paths: list[str], out_path: str) -> str:
    """Mixes 2+ audio tracks (e.g. move clicks + narration) down to one."""
    tracks = [t for t in track_paths if t and os.path.isfile(t)]
    if not tracks:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "1", "-c:a", "aac", out_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        return out_path
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
        # Soft-fail: use first track only
        print(f"[sound] mix failed, using first track only: {proc.stderr[-500:]}")
        import shutil as _shutil
        _shutil.copy(tracks[0], out_path)
        return out_path
    return out_path
