"""Patch 11 — chess.com-style capture + check sounds (distinct from move)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TYPED = r'''
def build_typed_move_sounds(
    events: list[tuple[float, str]],
    total_duration_sec: float,
    out_path: str,
    move_path: str | None = None,
    capture_path: str | None = None,
    check_path: str | None = None,
) -> str:
    """events: (timestamp_sec, kind) with kind in move|capture|check."""
    if not events:
        return build_move_click_track([], total_duration_sec, out_path, None)

    by_kind: dict[str, list[float]] = {"move": [], "capture": [], "check": []}
    for ts, kind in events:
        k = kind if kind in by_kind else "move"
        by_kind[k].append(ts)

    def _ok(path: str | None) -> str | None:
        return path if path and os.path.isfile(path) else None

    move_p = _ok(move_path)
    cap_p = _ok(capture_path)
    chk_p = _ok(check_path)

    partials: list[str] = []
    base = out_path + ".part"

    if by_kind["move"]:
        part = f"{base}_move.aac"
        build_move_click_track(by_kind["move"], total_duration_sec, part, move_p)
        partials.append(part)

    if by_kind["capture"]:
        part = f"{base}_capture.aac"
        if cap_p:
            build_move_click_track(by_kind["capture"], total_duration_sec, part, cap_p)
        else:
            _build_synth_kind(by_kind["capture"], total_duration_sec, part, kind="capture")
        partials.append(part)

    if by_kind["check"]:
        part = f"{base}_check.aac"
        if chk_p:
            build_move_click_track(by_kind["check"], total_duration_sec, part, chk_p)
        else:
            _build_synth_kind(by_kind["check"], total_duration_sec, part, kind="check")
        partials.append(part)

    if not partials:
        return build_move_click_track([], total_duration_sec, out_path, None)
    if len(partials) == 1:
        import shutil
        shutil.copy2(partials[0], out_path)
        return out_path
    return mix_audio_tracks(partials, out_path)


def _build_synth_kind(
    timestamps_sec: list[float],
    total_duration_sec: float,
    out_path: str,
    kind: str = "capture",
) -> str:
    """Synthetic capture (deep) or check (bright) when mp3 assets missing."""
    delays_ms = [max(0, int(ts * 1000)) for ts in timestamps_sec]
    n = len(delays_ms)
    if kind == "check":
        freq, vol_thump, vol_tick = 520, 0.55, 0.85
    else:
        freq, vol_thump, vol_tick = 95, 1.0, 0.7
    inputs: list[str] = []
    filter_parts: list[str] = []
    for i, d in enumerate(delays_ms):
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration=0.08"]
        inputs += ["-f", "lavfi", "-i", "anoisesrc=color=white:duration=0.05:sample_rate=44100"]
        thump_idx, tick_idx = 2 * i, 2 * i + 1
        filter_parts.append(
            f"[{thump_idx}:a]volume={vol_thump},afade=t=out:st=0:d=0.08,adelay={d}|{d}[thump{i}]"
        )
        filter_parts.append(
            f"[{tick_idx}:a]highpass=f=800,lowpass=f=6000,volume={vol_tick},"
            f"afade=t=out:st=0:d=0.04,adelay={d}|{d}[tick{i}]"
        )
    mix_inputs = "".join(f"[thump{i}][tick{i}]" for i in range(n))
    filter_complex = ";".join(filter_parts) + (
        f";{mix_inputs}amix=inputs={2 * n}:duration=longest:normalize=0,"
        f"alimiter=limit=0.95,apad=whole_dur={total_duration_sec}[mixed]"
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


'''


def apply() -> None:
    p = ROOT / "app" / "render" / "video_builder.py"
    t = p.read_text()
    if "_build_synth_kind" not in t:
        if "def build_typed_move_sounds" in t:
            start = t.index("def build_typed_move_sounds")
            end = t.index("def mix_audio_tracks")
            t = t[:start] + TYPED + t[end:]
        else:
            t = t.replace(
                "def mix_audio_tracks(track_paths: list[str], out_path: str) -> str:",
                TYPED + "def mix_audio_tracks(track_paths: list[str], out_path: str) -> str:",
                1,
            )
        p.write_text(t)
        print("video_builder: capture/check synth wired")
    else:
        print("video_builder already has synth kinds")

    pp = ROOT / "app" / "pipeline.py"
    pt = pp.read_text()
    if "is_capture = board.is_capture" in pt:
        print("pipeline already detects captures")
        return
    pt = pt.replace(
        "from app.render.video_builder import TimedFrame, build_video, build_move_click_track, mix_audio_tracks",
        "from app.render.video_builder import TimedFrame, build_video, build_move_click_track, build_typed_move_sounds, mix_audio_tracks",
    )
    old = """    move_timestamps: list[float] = []
    t_cursor = INTRO_HOLD_SEC
    for i, m in enumerate(game.moves):
        move = chess.Move.from_uci(m.move_uci)
        best_move = chess.Move.from_uci(m.best_move_uci) if m.best_move_uci else None
        frame_img = render_frame(ctx, board, last_move=move, best_move=best_move, eval_cp=m.eval_cp)
        board.push(move)
        frame_path = os.path.join(workdir, f"frame_{i:04d}.png")
        frame_img.save(frame_path)
        frames.append(TimedFrame(frame_path, duration))
        move_timestamps.append(t_cursor)  # click plays the instant this move's frame appears
        t_cursor += duration
        last_frame_for_thumb = frame_img

    total_duration = t_cursor
    click_track_path = os.path.join(workdir, "clicks.aac")
    build_move_click_track(move_timestamps, total_duration, click_track_path,
                            click_asset_path=settings.move_click_asset_path)
"""
    new = """    sound_events: list[tuple[float, str]] = []
    t_cursor = INTRO_HOLD_SEC
    for i, m in enumerate(game.moves):
        move = chess.Move.from_uci(m.move_uci)
        best_move = chess.Move.from_uci(m.best_move_uci) if m.best_move_uci else None
        is_capture = board.is_capture(move)
        frame_img = render_frame(ctx, board, last_move=move, best_move=best_move, eval_cp=m.eval_cp)
        board.push(move)
        is_check = board.is_check()
        frame_path = os.path.join(workdir, f"frame_{i:04d}.png")
        frame_img.save(frame_path)
        frames.append(TimedFrame(frame_path, duration))
        if is_check:
            kind = "check"
        elif is_capture:
            kind = "capture"
        else:
            kind = "move"
        sound_events.append((t_cursor, kind))
        t_cursor += duration
        last_frame_for_thumb = frame_img

    total_duration = t_cursor
    click_track_path = os.path.join(workdir, "clicks.aac")
    build_typed_move_sounds(
        sound_events,
        total_duration,
        click_track_path,
        move_path=settings.move_click_asset_path,
        capture_path=getattr(settings, "capture_sound_path", None),
        check_path=getattr(settings, "check_sound_path", None),
    )
"""
    if old in pt:
        pt = pt.replace(old, new, 1)
        print("pipeline capture/check loop applied")
    else:
        print("pipeline loop pattern not found")
    pp.write_text(pt)
