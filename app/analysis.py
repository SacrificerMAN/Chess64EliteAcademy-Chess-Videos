"""
Parses a PGN and runs Stockfish over each position to depth N.
Produces a list of per-move records used by both the renderer (best-move
arrows, last-move highlight) and the Shorts cutter (eval-swing detection).
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field

import chess
import chess.engine
import chess.pgn

from app.config import settings


@dataclass
class MoveRecord:
    ply: int
    san: str
    move_uci: str
    fen_before: str
    fen_after: str
    from_square: str
    to_square: str
    eval_cp: float | None  # centipawns, from white's POV; None if mate score unresolved
    mate_in: int | None
    best_move_uci: str | None  # engine's top suggestion in the *before* position


@dataclass
class GameData:
    white: str
    black: str
    result: str
    event: str
    eco: str
    platform: str
    moves: list[MoveRecord] = field(default_factory=list)
    truncated: bool = False


def _find_stockfish() -> str | None:
    return shutil.which("stockfish")


def parse_pgn(pgn_text: str) -> chess.pgn.Game:
    import io

    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise ValueError("Could not parse PGN — check the file/text and try again.")
    return game


def analyze_game(
    pgn_text: str,
    depth: int | None = None,
    max_moves: int | None = None,
    platform: str = "PGN",
) -> GameData:
    depth = depth or settings.default_depth
    max_moves = max_moves or settings.max_moves_for_bot

    game = parse_pgn(pgn_text)
    headers = game.headers
    data = GameData(
        white=headers.get("White", "White"),
        black=headers.get("Black", "Black"),
        result=headers.get("Result", "*"),
        event=headers.get("Event", ""),
        eco=headers.get("ECO", ""),
        platform=platform,
    )

    engine_path = _find_stockfish()
    engine = None
    if engine_path:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    try:
        board = game.board()
        ply = 0
        for move in game.mainline_moves():
            if ply >= max_moves:
                data.truncated = True
                break
            fen_before = board.fen()
            san = board.san(move)
            from_sq, to_sq = chess.square_name(move.from_square), chess.square_name(move.to_square)

            eval_cp, mate_in, best_move_uci = None, None, None
            if engine is not None:
                try:
                    info = engine.analyse(board, chess.engine.Limit(depth=depth))
                    score = info["score"].white()
                    if score.is_mate():
                        mate_in = score.mate()
                    else:
                        eval_cp = score.score()
                    pv = info.get("pv")
                    if pv:
                        best_move_uci = pv[0].uci()
                except Exception:
                    pass

            board.push(move)
            ply += 1
            data.moves.append(
                MoveRecord(
                    ply=ply,
                    san=san,
                    move_uci=move.uci(),
                    fen_before=fen_before,
                    fen_after=board.fen(),
                    from_square=from_sq,
                    to_square=to_sq,
                    eval_cp=eval_cp,
                    mate_in=mate_in,
                    best_move_uci=best_move_uci,
                )
            )
    finally:
        if engine is not None:
            engine.quit()

    return data


def eval_swings(data: GameData, min_swing_cp: float = 150.0) -> list[int]:
    """
    Return ply indices (into data.moves) where the evaluation swung sharply —
    used to pick "critical moments" for Shorts and viral hooks.
    """
    swings = []
    prev = 0.0
    for i, m in enumerate(data.moves):
        cur = m.eval_cp if m.eval_cp is not None else (1000 if (m.mate_in or 0) > 0 else -1000)
        if abs(cur - prev) >= min_swing_cp:
            swings.append(i)
        prev = cur
    return swings
