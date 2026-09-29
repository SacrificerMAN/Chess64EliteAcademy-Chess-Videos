"""
Telegram bot implementing every command from the Chess64 Elite Academy spec.
Single polling instance (Railway).

Two video styles:
  - Pro studio (photos/flags/navy+gold) → /pgn, uploaded games
  - Famous Traps (dark vertical educational) → /trap, /trapofday, /traps
"""
from __future__ import annotations

import logging
import os
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.pipeline import run_job
from app.storage import Job, clear_manual_assets, new_job, user_state
from app.youtube.upload import upload_video

try:
    from app.trap_pipeline import run_trap_job
except ImportError:
    run_trap_job = None  # type: ignore

logger = logging.getLogger("chess64.bot")

TRAP_LIBRARY = {
    "scholars mate": ("Scholar's Mate", "1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7#"),
    "scholars_mate": ("Scholar's Mate", "1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7#"),
    "legal trap": ("Legal's Mate", "1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5 Bxd1 6. Bxf7+ Ke7 7. Nd5#"),
    "legals_mate": ("Legal's Mate", "1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5 Bxd1 6. Bxf7+ Ke7 7. Nd5#"),
    "fried liver": (
        "Fried Liver Attack",
        "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5 d5 5. exd5 Nxd5 6. Nxf7 Kxf7 7. Qf3+ Ke6 8. Nc3 Ncb4 9. Qe4 c6 10. a3 Na6 11. d4",
    ),
    "fried_liver": (
        "Fried Liver Attack",
        "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5 d5 5. exd5 Nxd5 6. Nxf7 Kxf7 7. Qf3+ Ke6 8. Nc3 Ncb4 9. Qe4 c6 10. a3 Na6 11. d4",
    ),
    "blackburne": (
        "Blackburne Shilling",
        "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nd4 4. Nxe5 Qg5 5. Nxf7 Qxg2 6. Rf1 Qxe4+ 7. Be2 Nf3#",
    ),
    "blackburne_shilling": (
        "Blackburne Shilling",
        "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nd4 4. Nxe5 Qg5 5. Nxf7 Qxg2 6. Rf1 Qxe4+ 7. Be2 Nf3#",
    ),
    "stafford": (
        "Stafford Gambit",
        "1. e4 e5 2. Nf3 Nf6 3. Nxe5 Nc6 4. Nxc6 dxc6 5. d3 Bc5 6. Bg5 Nxe4 7. Bxd8 Bxf2+ 8. Ke2 Bg4#",
    ),
    "englund": (
        "Englund Gambit Trap",
        "1. d4 e5 2. dxe5 Nc6 3. Nf3 Qe7 4. Bf4 Qb4+ 5. Bd2 Qxb2 6. Bc3 Bb4 7. Qd2 Bxc3 8. Qxc3 Qc1#",
    ),
    "lasker": (
        "Lasker Trap",
        "1. d4 d5 2. c4 e5 3. dxe5 d4 4. e3 Bb4+ 5. Bd2 dxe3 6. Bxb4 exf2+ 7. Ke2 fxg1=N+ 8. Rxg1 Bg4+",
    ),
    "fishing_pole": ("Fishing Pole", "1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6 4. O-O Ng4 5. h3 h5"),
}


def _resolve_trap(name: str):
    key = name.lower().strip().replace("-", "_")
    key_space = name.lower().strip()
    if key in TRAP_LIBRARY:
        return TRAP_LIBRARY[key]
    if key_space in TRAP_LIBRARY:
        return TRAP_LIBRARY[key_space]
    for k, v in TRAP_LIBRARY.items():
        if key in k or key_space in k or key in v[0].lower():
            return v
    traps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "traps")
    pgn_path = os.path.join(traps_dir, f"{key}.pgn")
    if os.path.isfile(pgn_path):
        return (key.replace("_", " ").title(), open(pgn_path, encoding="utf-8").read())
    return None


def _authorized(user_id: int) -> bool:
    if not settings.allowed_user_ids:
        return True
    return user_id in settings.allowed_user_ids


async def _guard(update: Update) -> bool:
    user = update.effective_user
    if not user or not _authorized(user.id):
        if update.message:
            await update.message.reply_text("You're not authorized to use this bot.")
        return False
    return True


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    await update.message.reply_text(
        f"Welcome to {settings.channel_name}!\n\n"
        "Send /help to see everything I can do.",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    await update.message.reply_text(
        "*Chess64 Elite Academy Bot*\n\n"
        "/silent <player or game hint> — fetch/build a silent board video\n"
        "/pgn — paste PGN or send .pgn file *(pro studio style)*\n"
        "/duration <sec> — move duration (default 4)\n"
        "/theme green|brown|blue|purple\n"
        "/setwhite /setblack — then send a photo for that side\n"
        "/setwhiteflag <CC> /setblackflag <CC> — e.g. IR, US, IN\n"
        "/clearphotos — clear manual photo/flag overrides\n"
        "/trapofday /trap <name> /traps /trend — *Famous Traps* style (dark vertical)\n\n"
        "After rendering, tap *Send on Telegram* or *Upload to YouTube*.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    st = user_state(update.effective_user.id)
    if not context.args:
        await update.message.reply_text(f"Current duration: {st['duration']}s/move. Usage: /duration 3|5|7")
        return
    try:
        val = float(context.args[0])
        if not (1 <= val <= 15):
            raise ValueError
        st["duration"] = val
        await update.message.reply_text(f"Duration set to {val}s/move.")
    except ValueError:
        await update.message.reply_text("Please give a number of seconds between 1 and 15.")


async def cmd_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    st = user_state(update.effective_user.id)
    if not context.args or context.args[0].lower() not in settings.THEMES:
        await update.message.reply_text("Usage: /theme green|brown|blue|purple")
        return
    st["theme"] = context.args[0].lower()
    await update.message.reply_text(f"Theme set to {st['theme']}.")


async def cmd_setwhite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    user_state(update.effective_user.id)["awaiting"] = "photo_white"
    await update.message.reply_text("Send a photo for White now.")


async def cmd_setblack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    user_state(update.effective_user.id)["awaiting"] = "photo_black"
    await update.message.reply_text("Send a photo for Black now.")


async def cmd_setwhiteflag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    await _set_flag(update, context, "white")


async def cmd_setblackflag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    await _set_flag(update, context, "black")


async def _set_flag(update: Update, context: ContextTypes.DEFAULT_TYPE, side: str) -> None:
    if not context.args or len(context.args[0]) != 2:
        await update.message.reply_text(f"Usage: /set{side}flag <CC> e.g. IR, US, IN")
        return
    st = user_state(update.effective_user.id)
    st["manual_flags"][side] = context.args[0].upper()
    await update.message.reply_text(f"{side.title()} flag set to {context.args[0].upper()}.")


async def cmd_clearphotos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    clear_manual_assets(update.effective_user.id)
    await update.message.reply_text("Manual photos/flags cleared. Auto-resolve is back on.")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    st = user_state(update.effective_user.id)
    awaiting = st.get("awaiting")
    if awaiting not in ("photo_white", "photo_black"):
        return
    side = "white" if awaiting == "photo_white" else "black"
    photo = update.message.photo[-1]
    file = await photo.get_file()
    os.makedirs(settings.workdir, exist_ok=True)
    dest = os.path.join(settings.workdir, f"manual_{update.effective_user.id}_{side}.jpg")
    await file.download_to_drive(dest)
    st["manual_photos"][side] = dest
    st["awaiting"] = None
    await update.message.reply_text(f"{side.title()} photo saved. It will override auto-resolve.")


async def cmd_traps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    seen = set()
    lines = ["*Famous Traps* (dark educational Shorts style):\n"]
    for k, v in TRAP_LIBRARY.items():
        name = v[0]
        if name in seen:
            continue
        seen.add(name)
        lines.append(f"• {name} — `/trap {k}`")
    lines.append("\nAlso: /trapofday")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_trapofday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    import random

    key, val = random.choice(list(TRAP_LIBRARY.items()))
    display, pgn = val
    await _start_trap_job(update, context, pgn, trap_name=display)


async def cmd_trap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await cmd_traps(update, context)
        return
    name = " ".join(context.args).lower()
    resolved = _resolve_trap(name)
    if resolved is None:
        await update.message.reply_text(f"Unknown trap '{name}'. Try /traps to see the list.")
        return
    display, pgn = resolved
    await _start_trap_job(update, context, pgn, trap_name=display)


async def cmd_trend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    await update.message.reply_text(
        "Trending traps: Fried Liver, Legal's Mate, Blackburne Shilling, Stafford.\n"
        "Use /trap <name> for *Famous Traps* style video.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_pgn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    user_state(update.effective_user.id)["awaiting"] = "pgn"
    await update.message.reply_text("Paste your PGN text now, or send a .pgn file.")


async def cmd_silent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /silent <player name, e.g. Magnus Carlsen>")
        return
    hint = " ".join(context.args)
    await update.message.reply_text(
        f"Looking for a recent notable game for '{hint}'...\n"
        "Send /pgn and paste a PGN to render a video."
    )


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".pgn"):
        return
    file = await doc.get_file()
    raw = await file.download_as_bytearray()
    pgn_text = raw.decode("utf-8", errors="ignore")
    await _start_job_from_pgn(update, context, pgn_text, platform="Uploaded PGN")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    st = user_state(update.effective_user.id)
    if st.get("awaiting") == "pgn":
        st["awaiting"] = None
        await _start_job_from_pgn(update, context, update.message.text, platform="Pasted PGN")


async def _start_trap_job(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    pgn_text: str,
    trap_name: str = "Famous Trap",
) -> None:
    if run_trap_job is None:
        await update.message.reply_text(
            "Famous Traps renderer not installed yet. Redeploy after famous-traps-v1."
        )
        return
    user_id = update.effective_user.id
    job = new_job(user_id)
    status_msg = await update.message.reply_text(
        f"*Famous Traps* style — rendering *{trap_name}*…",
        parse_mode=ParseMode.MARKDOWN,
    )
    try:
        import asyncio

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: run_trap_job(job, pgn_text, trap_name=trap_name)
        )
        seo = result["seo"]
        caption = (
            f"*{seo['title']}*\n\n"
            f"Style: Famous Traps (dark educational)\n"
            f"{settings.brand_hashtag}"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Send on Telegram", callback_data=f"send:{job.id}"),
                    InlineKeyboardButton("Upload to YouTube", callback_data=f"upload:{job.id}"),
                ]
            ]
        )
        await status_msg.edit_text(f"{trap_name} ready!")
        await update.message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    except Exception as exc:
        logger.error("Trap job %s failed: %s\n%s", job.id, exc, traceback.format_exc())
        await status_msg.edit_text(f"Trap render failed: {exc}")


async def _start_job_from_pgn(
    update: Update, context: ContextTypes.DEFAULT_TYPE, pgn_text: str, platform: str
) -> None:
    user_id = update.effective_user.id
    job = new_job(user_id)
    status_msg = await update.message.reply_text(job.STATUS_LABELS[1])

    async def report(step: int) -> None:
        try:
            await status_msg.edit_text(Job.STATUS_LABELS[step])
        except Exception:
            pass

    try:
        import asyncio

        loop = asyncio.get_event_loop()
        await report(1)
        result = await loop.run_in_executor(None, run_job, job, pgn_text, platform)
        await report(5)

        game = result["game"]
        seo = result["seo"]
        is_trunc = bool(result.get("truncated") or getattr(game, "truncated", False))
        truncated_note = "\nGame truncated to max move limit." if is_trunc else ""
        caption = (
            f"*{seo['title']}*\n{seo['title_hi']}\n\n"
            f"{game.white} vs {game.black} ({game.event or platform})"
            f"{truncated_note}\n\nSEO source: `{seo.get('source', 'gemini')}`"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Send on Telegram", callback_data=f"send:{job.id}"),
                    InlineKeyboardButton("Upload to YouTube", callback_data=f"upload:{job.id}"),
                ]
            ]
        )
        await update.message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    except Exception as exc:
        logger.error("Job %s failed: %s\n%s", job.id, exc, traceback.format_exc())
        await status_msg.edit_text(f"Something went wrong: {exc}")


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action, job_id = query.data.split(":", 1)
    from app.storage import get_job

    job = get_job(job_id)
    if not job or "long_video" not in job.data:
        await query.message.reply_text("This job has expired. Please regenerate.")
        return

    if action == "send":
        await query.message.reply_text("Sending long video + shorts on Telegram...")
        with open(job.data["long_video"], "rb") as f:
            await query.message.reply_video(f, caption=job.data["seo"]["title"])
        for short_path in job.data.get("shorts", []):
            if short_path == job.data["long_video"]:
                continue
            with open(short_path, "rb") as f:
                await query.message.reply_video(f)
        await query.message.reply_text(job.data["seo"]["description"])

    elif action == "upload":
        await query.message.reply_text("Uploading to YouTube...")
        try:
            seo = job.data["seo"]
            url = upload_video(
                job.data["long_video"],
                title=seo["title"],
                description=seo["description"],
                tags=seo["tags"],
                thumbnail_path=job.data.get("thumbnails", {}).get("wide"),
            )
            await query.message.reply_text(f"Uploaded: {url}")
        except Exception as exc:
            logger.error("YouTube upload failed: %s\n%s", exc, traceback.format_exc())
            await query.message.reply_text(f"YouTube upload failed: {exc}")


def build_application() -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("silent", cmd_silent))
    app.add_handler(CommandHandler("pgn", cmd_pgn))
    app.add_handler(CommandHandler("duration", cmd_duration))
    app.add_handler(CommandHandler("theme", cmd_theme))
    app.add_handler(CommandHandler("setwhite", cmd_setwhite))
    app.add_handler(CommandHandler("setblack", cmd_setblack))
    app.add_handler(CommandHandler("setwhiteflag", cmd_setwhiteflag))
    app.add_handler(CommandHandler("setblackflag", cmd_setblackflag))
    app.add_handler(CommandHandler("clearphotos", cmd_clearphotos))
    app.add_handler(CommandHandler("trapofday", cmd_trapofday))
    app.add_handler(CommandHandler("trapoftheday", cmd_trapofday))
    app.add_handler(CommandHandler("trap", cmd_trap))
    app.add_handler(CommandHandler("traps", cmd_traps))
    app.add_handler(CommandHandler("trend", cmd_trend))

    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_button))

    return app


def run_bot() -> None:
    logging.basicConfig(level=logging.INFO)
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    app = build_application()
    logger.info("Chess64 bot starting (polling)… famous-traps-v1 enabled")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
