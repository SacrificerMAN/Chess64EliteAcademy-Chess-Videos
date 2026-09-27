"""
Orchestrates one job end-to-end, matching the STATUS_LABELS steps:
  [1/5] Photos -> [2/5] Rendering long -> [3/5] Shorts ->
  [4/5] Thumbnails + SEO -> [5/5] Ready
"""
from __future__ import annotations

import logging
import os

from app.analysis import GameData, analyze_game
from app.config import settings
from app.gemini.client import generate_commentary, generate_seo_metadata
from app.commentary.tts import synthesize_commentary
from app.player_assets import PlayerAssets, resolve_player_assets
from app.render.board_renderer import RenderContext, intro_card, render_frame
from app.render.shorts import build_shorts
from app.render.thumbnails import make_thumbnails
from app.render.video_builder import TimedFrame, build_video, build_move_click_track, mix_audio_tracks
from app.storage import Job
from PIL import Image
import chess

logger = logging.getLogger("chess64.pipeline")

INTRO_HOLD_SEC = 2.5


def _resolve_assets_with_overrides(name: str, side: str, user_state: dict) -> PlayerAssets:
    manual_photo = user_state.get("manual_photos", {}).get(side)
    manual_flag = user_state.get("manual_flags", {}).get(side)
    if manual_photo and os.path.exists(manual_photo):
        img = Image.open(manual_photo).convert("RGBA")
        return PlayerAssets(name, img, manual_flag, "manual")
    assets = resolve_player_assets(name)
    if manual_flag:
        assets.country_code = manual_flag
    return assets


def run_job(job: Job, pgn_text: str, platform: str = "PGN") -> dict:
    from app.storage import user_state as get_user_state

    ustate = get_user_state(job.user_id)
    duration = ustate.get("duration", settings.default_duration_per_move)
    depth = ustate.get("depth", settings.default_depth)
    theme = ustate.get("theme", settings.board_theme)
    workdir = job.workdir

    # ---- [1/5] Photos ----
    job.set_step(1, "photos")
    game = analyze_game(pgn_text, depth=depth, max_moves=settings.max_moves_for_bot, platform=platform)
    white_assets = _resolve_assets_with_overrides(game.white, "white", ustate)
    black_assets = _resolve_assets_with_overrides(game.black, "black", ustate)

    ctx = RenderContext(
        theme=theme,
        white_assets=white_assets,
        black_assets=black_assets,
        white_name=game.white,
        black_name=game.black,
    )

    # ---- [2/5] Rendering long ----
    job.set_step(2, "rendering_long")
    commentary_lines = generate_commentary(game, short=False)
    commentary_by_ply = {c["ply"]: c["line"] for c in commentary_lines if c.get("line")}
    narration_path = None
    if commentary_lines:
        narration_path = os.path.join(workdir, "narration_long.mp3")
        narration_path = synthesize_commentary(commentary_lines, narration_path)

    frames: list[TimedFrame] = []
    intro_img = intro_card(ctx, f"{game.white} vs {game.black}", settings.brand_hashtag)
    intro_path = os.path.join(workdir, "frame_intro.png")
    intro_img.save(intro_path)
    frames.append(TimedFrame(intro_path, INTRO_HOLD_SEC))

    board = chess.Board()
    last_frame_for_thumb = intro_img
    move_timestamps: list[float] = []
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

    audio_path = click_track_path
    if narration_path:
        mixed_path = os.path.join(workdir, "audio_mixed.aac")
        audio_path = mix_audio_tracks([click_track_path, narration_path], mixed_path)

    long_video_path = os.path.join(workdir, "long.mp4")
    build_video(frames, long_video_path, audio_path=audio_path)

    # ---- [3/5] Shorts ----
    job.set_step(3, "rendering_shorts")
    shorts_dir = os.path.join(workdir, "shorts")
    os.makedirs(shorts_dir, exist_ok=True)
    shorts_paths = build_shorts(
        long_video_path, game, per_move_duration=duration,
        intro_offset_sec=INTRO_HOLD_SEC, output_dir=shorts_dir,
    )

    # ---- [4/5] Thumbnails + SEO ----
    job.set_step(4, "seo")
    thumb_paths = make_thumbnails(last_frame_for_thumb, f"{game.white} vs {game.black}",
                                   settings.brand_hashtag, workdir)
    seo = generate_seo_metadata(game)

    # ---- [5/5] Ready ----
    job.set_step(5, "ready")
    result = {
        "game": game,
        "long_video": long_video_path,
        "shorts": shorts_paths,
        "thumbnails": thumb_paths,
        "seo": seo,
        "truncated": game.truncated,
    }
    job.data.update(result)
    return result
