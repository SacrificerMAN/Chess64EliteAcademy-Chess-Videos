"""Patch 11 — chess.com-style capture + check sounds."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply() -> None:
    _patch_video_builder()
    _patch_pipeline()
    _patch_config()


def _patch_video_builder() -> None:
    p = ROOT / "app" / "render" / "video_builder.py"
    t = p.read_text()
    if "def build_typed_move_sounds" in t:
        print("video_builder already typed")
        return
    insert = '''
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
    paths = {
        "move": move_path,
        "capture": capture_path or move_path,
        "check": check_path or move_path,
    }
    partials: list[str] = []
    base = out_path + ".part"
    for kind, stamps in by_kind.items():
        if not stamps:
            continue
        part = f"{base}_{kind}.aac"
        build_move_click_track(stamps, total_duration_sec, part, paths.get(kind))
        partials.append(part)
    if not partials:
        return build_move_click_track([], total_duration_sec, out_path, None)
    if len(partials) == 1:
        import shutil
        shutil.copy2(partials[0], out_path)
        return out_path
    return mix_audio_tracks(partials, out_path)


'''
    if "def mix_audio_tracks" not in t:
        raise RuntimeError("mix_audio_tracks not found")
    p.write_text(
        t.replace(
            "def mix_audio_tracks(track_paths: list[str], out_path: str) -> str:",
            insert + "def mix_audio_tracks(track_paths: list[str], out_path: str) -> str:",
            1,
        )
    )
    print("patched video_builder typed sounds")


def _patch_pipeline() -> None:
    p = ROOT / "app" / "pipeline.py"
    t = p.read_text()
    if "build_typed_move_sounds" in t and "is_capture" in t:
        print("pipeline already typed")
        return
    t = t.replace(
        "from app.render.video_builder import TimedFrame, build_video, build_move_click_track, mix_audio_tracks",
        "from app.render.video_builder import TimedFrame, build_video, build_move_click_track, build_typed_move_sounds, mix_audio_tracks",
    )
    if "is_capture = board.is_capture" in t:
        p.write_text(t)
        print("pipeline import fixed")
        return
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
    if old not in t:
        print("pipeline loop already different")
        p.write_text(t)
        return
    p.write_text(t.replace(old, new, 1))
    print("patched pipeline capture/check")


def _patch_config() -> None:
    p = ROOT / "app" / "config.py"
    t = p.read_text()
    if "capture_sound_path" in t:
        print("config already capture paths")
        return
    print("config missing capture_sound_path")
