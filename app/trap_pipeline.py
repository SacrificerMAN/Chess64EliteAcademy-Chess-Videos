"""
Famous Traps pipeline — vertical educational Shorts style.
Used by /trap, /trapofday, /traps. Does NOT use player photos/flags.
"""
from __future__ import annotations

import io
import logging
import os

import chess
import chess.pgn

from app.config import settings
from app.render.trap_renderer import (
    TrapRenderContext,
    format_san_label,
    render_trap_frame,
    trap_intro_card,
)
from app.render.video_builder import (
    TimedFrame,
    build_typed_move_sounds,
    build_video,
)
from app.storage import Job

logger = logging.getLogger("chess64.trap_pipeline")

INTRO_HOLD_SEC = 1.8
DEFAULT_MOVE_SEC = 2.8


def _parse_pgn_moves(pgn_text: str) -> tuple[list[tuple[chess.Move, str]], str]:
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        board = chess.Board()
        moves: list[tuple[chess.Move, str]] = []
        tokens = pgn_text.replace("\n", " ").split()
        for tok in tokens:
            tok = tok.strip()
            if not tok or tok[0].isdigit() or tok in ("*", "1-0", "0-1", "1/2-1/2"):
                continue
            tok = tok.rstrip("?!+#")
            try:
                move = board.parse_san(tok)
                san = board.san(move)
                moves.append((move, san))
                board.push(move)
            except Exception:
                continue
        return moves, "Famous Trap"

    title = (
        game.headers.get("Opening")
        or game.headers.get("Event")
        or "Famous Trap"
    )
    board = game.board()
    moves = []
    node = game
    while node.variations:
        node = node.variation(0)
        if node.move is None:
            break
        san = board.san(node.move)
        moves.append((node.move, san))
        board.push(node.move)
    return moves, title


def run_trap_job(
    job: Job,
    pgn_text: str,
    trap_name: str = "",
    series_title: str = "Famous Traps",
    duration: float | None = None,
) -> dict:
    workdir = job.workdir
    os.makedirs(workdir, exist_ok=True)
    move_sec = duration if duration and duration > 0 else DEFAULT_MOVE_SEC

    job.set_step(1, "photos")
    moves, pgn_title = _parse_pgn_moves(pgn_text)
    if not moves:
        raise ValueError("No legal moves found in trap PGN.")

    display_name = trap_name or pgn_title
    ctx = TrapRenderContext(series_title=series_title, trap_name=display_name)

    job.set_step(2, "rendering_long")
    frames: list[TimedFrame] = []
    sound_events: list[tuple[float, str]] = []

    intro = trap_intro_card(ctx)
    intro_path = os.path.join(workdir, "trap_intro.png")
    intro.save(intro_path)
    frames.append(TimedFrame(intro_path, INTRO_HOLD_SEC))

    board = chess.Board()
    t_cursor = INTRO_HOLD_SEC

    for i, (move, san) in enumerate(moves):
        is_capture = board.is_capture(move)
        label = format_san_label(i, san)
        board.push(move)
        is_check = board.is_check()
        frame_img = render_trap_frame(ctx, board, last_move=move, move_label=label)
        frame_path = os.path.join(workdir, f"trap_frame_{i:04d}.png")
        frame_img.save(frame_path)
        frames.append(TimedFrame(frame_path, move_sec))

        if is_capture:
            kind = "capture"
        elif is_check:
            kind = "check"
        else:
            kind = "move"
        sound_events.append((t_cursor, kind))
        print(f"[trap-sound] ply={i} kind={kind} san={san}")
        t_cursor += move_sec

    total_duration = t_cursor
    click_track = os.path.join(workdir, "trap_clicks.aac")
    print(f"[trap-sound] VERSION=trap-v1 events={len(sound_events)}")
    build_typed_move_sounds(
        sound_events,
        total_duration,
        click_track,
        move_path=settings.move_click_asset_path,
        capture_path=settings.capture_sound_path,
        check_path=settings.check_sound_path,
    )

    video_path = os.path.join(workdir, "trap.mp4")
    build_video(frames, video_path, audio_path=click_track, fps=30)

    title = f"{display_name} | Famous Chess Trap"
    description = (
        f"{display_name} — Famous Traps series by {settings.channel_name}.\n"
        f"{settings.brand_hashtag}\n"
        f"{settings.channel_handle}"
    )
    tags = ["chess", "chess trap", "famous traps", "chess shorts", display_name.lower()]

    job.set_step(5, "ready")

    class _G:
        white = "White"
        black = "Black"
        event = display_name
        truncated = False

    result = {
        "game": _G(),
        "long_video": video_path,
        "shorts": [video_path],
        "thumbnails": {},
        "seo": {
            "title": title,
            "title_hi": title,
            "description": description,
            "tags": tags,
            "source": "trap",
        },
        "truncated": False,
        "workdir": workdir,
        "trap_name": display_name,
        "style": "famous_traps",
    }
    job.data.update({k: v for k, v in result.items() if k != "game"})
    job.data["white"] = "White"
    job.data["black"] = "Black"
    return result
