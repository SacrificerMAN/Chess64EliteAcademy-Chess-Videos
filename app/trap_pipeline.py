"""
Famous Traps pipeline — vertical educational Shorts style with voiceover.
Dark board, bright title, yellow arrows, English TTS narration + move sounds.
"""
from __future__ import annotations

import io
import logging
import os
import subprocess

import chess
import chess.pgn

from app.commentary.tts import synthesize_commentary
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
    mix_audio_tracks,
    probe_duration_sec,
)
from app.storage import Job

logger = logging.getLogger("chess64.trap_pipeline")

INTRO_HOLD_SEC = 2.2
DEFAULT_MOVE_SEC = 3.2

TRAP_SCRIPTS: dict[str, list[str]] = {
    "blackburne": [
        "A normal Italian opening. Knights and bishop developing on both sides.",
        "White's bishop comes to c4.",
        "Black offers a strange knight move to d4. It looks like an obvious blunder.",
        "If White grabs the free pawn on e5, Black's queen swings out to g5, attacking the knight and g2 at once.",
        "White grabs another pawn on f7, but the queen crashes straight through on g2.",
        "White's rook has to move.",
        "The queen scoops up the e4 pawn with check.",
        "White blocks with the bishop, but it's too late.",
        "The knight on d4 delivers checkmate on f3.",
        "The Blackburne Shilling Gambit claims another victim.",
    ],
    "fried liver": [
        "The Fried Liver Attack. One of the sharpest ways to punish the Two Knights Defense.",
        "White develops the bishop to c4, eyeing f7.",
        "Black develops the kingside knight.",
        "White jumps the knight to g5, putting immediate pressure on f7.",
        "Black strikes in the center with d5.",
        "White captures on d5.",
        "Black recaptures with the knight.",
        "And now the sacrifice — knight takes on f7, ripping open the black king.",
        "The king is forced to take, and White's queen enters with check.",
        "The Fried Liver is on. Black's king is stuck in the center.",
    ],
    "stafford": [
        "The Stafford Gambit. Black gives up a pawn for rapid development and traps.",
        "After the knight exchange, Black develops with tempo.",
        "White must be careful — one greedy move and the king is under fire.",
        "Black's pieces swarm the kingside.",
        "The trap snaps shut.",
    ],
    "legal": [
        "Legal's Mate. A classic trap that punishes early bishop pins.",
        "White develops naturally.",
        "Black pins the knight with the bishop.",
        "White offers the queen — and if Black takes, disaster follows.",
        "The king is trapped. Checkmate.",
    ],
    "scholar": [
        "Scholar's Mate. The classic four-move checkmate beginners fall for.",
        "White develops the bishop and queen early, targeting f7.",
        "If Black is careless, the queen crashes through on f7 for mate.",
    ],
    "englund": [
        "The Englund Gambit trap. Black offers a center pawn on move one.",
        "White takes, and Black develops with tempo against the queen.",
        "One greedy grab and the queen is lost or the king is mated.",
    ],
    "lasker": [
        "The Lasker Trap in the Albin Countergambit.",
        "Black's underpromotion creates a devastating fork.",
        "White's position collapses.",
    ],
}


def _script_for_trap(trap_name: str, n_moves: int) -> list[str]:
    key = (trap_name or "").lower()
    for frag, lines in TRAP_SCRIPTS.items():
        if frag in key:
            if len(lines) >= n_moves:
                return lines[: max(n_moves, 3)]
            return lines
    return [
        f"This is the {trap_name or 'famous'} trap.",
        "Watch how one inaccurate move leads to disaster.",
        "Development looks normal at first.",
        "But the trap is already set.",
        "And just like that, the game is over.",
    ]


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
    print(f"[trap-sound] VERSION=trap-v2-voice events={len(sound_events)}")
    build_typed_move_sounds(
        sound_events,
        total_duration,
        click_track,
        move_path=settings.move_click_asset_path,
        capture_path=settings.capture_sound_path,
        check_path=settings.check_sound_path,
    )

    script_lines = _script_for_trap(display_name, len(moves))
    tts_lines = [{"ply": i, "line": line} for i, line in enumerate(script_lines)]
    tts_path = os.path.join(workdir, "trap_narration.mp3")
    narration = synthesize_commentary(tts_lines, tts_path)

    final_audio = click_track
    if narration:
        narr_dur = probe_duration_sec(narration) or 0.0
        print(f"[trap-tts] narration={narration} dur={narr_dur:.1f}s video={total_duration:.1f}s")
        mixed = os.path.join(workdir, "trap_mixed.aac")
        soft_narr = os.path.join(workdir, "trap_narr_soft.aac")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", narration,
                "-filter:a", f"volume=0.85,apad=whole_dur={total_duration}",
                "-t", str(total_duration), "-c:a", "aac", soft_narr,
            ],
            capture_output=True, text=True,
        )
        if os.path.isfile(soft_narr) and os.path.getsize(soft_narr) > 500:
            mix_audio_tracks([click_track, soft_narr], mixed)
            if os.path.isfile(mixed) and os.path.getsize(mixed) > 500:
                final_audio = mixed
                print("[trap-tts] mixed narration + clicks")
            else:
                print("[trap-tts] mix failed; clicks only")
        else:
            print("[trap-tts] soft narr failed; clicks only")
    else:
        print("[trap-tts] no narration; clicks only")

    video_path = os.path.join(workdir, "trap.mp4")
    build_video(frames, video_path, audio_path=final_audio, fps=30)

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
