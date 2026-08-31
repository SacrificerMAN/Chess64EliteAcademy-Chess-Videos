"""Telegram: verify token, clear webhook, solid post_init, clean polling."""
from pathlib import Path

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()
if "Telegram OK:" in t and ".post_init(_post_init)" in t:
    print("reconnect fully patched")
    raise SystemExit(0)

has_photos = "cmd_setwhite" in t
photo_handlers = ""
if has_photos:
    photo_handlers = (
        '    app.add_handler(CommandHandler("setwhite", cmd_setwhite))\n'
        '    app.add_handler(CommandHandler("setblack", cmd_setblack))\n'
        '    app.add_handler(CommandHandler("clearphotos", cmd_clearphotos))\n'
        '    app.add_handler(MessageHandler(filters.PHOTO, on_photo))\n'
    )

new_main = '''def main():
    if not TOKEN:
        print("Set TELEGRAM_BOT_TOKEN environment variable")
        raise SystemExit(1)
    if ":" not in TOKEN or len(TOKEN) < 30:
        print(f"TELEGRAM_BOT_TOKEN looks invalid (len={len(TOKEN)})")
        raise SystemExit(1)

    print("Bot starting (polling)…")
    print(f"YouTube privacy default: {YOUTUBE_PRIVACY}")
    print(f"Token prefix: {TOKEN[:12]}… ({len(TOKEN)} chars)")

    async def _post_init(application):
        try:
            me = await application.bot.get_me()
            print(f"Telegram OK: @{me.username} id={me.id}")
        except Exception as e:
            print(f"getMe FAILED (check TELEGRAM_BOT_TOKEN): {e}")
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            print("Webhook cleared; polling ready")
        except Exception as e:
            print(f"delete_webhook note: {e}")

    app = Application.builder().token(TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("silent", cmd_silent))
    app.add_handler(CommandHandler("lichess", cmd_lichess))
    app.add_handler(CommandHandler("offline", cmd_offline))
    app.add_handler(CommandHandler("pgn", cmd_pgn))
    app.add_handler(CommandHandler("duration", set_duration))
    app.add_handler(CommandHandler("theme", set_theme))
    app.add_handler(CommandHandler("cancel", cancel))
''' + photo_handlers + '''    app.add_handler(CommandHandler("trapofday", cmd_trapofday))
    app.add_handler(CommandHandler("trapoftheday", cmd_trapofday))
    app.add_handler(CommandHandler("trap", cmd_trap))
    app.add_handler(CommandHandler("traps", cmd_traps))
    app.add_handler(CommandHandler("trend", cmd_trend))
    app.add_handler(CallbackQueryHandler(on_job_button, pattern=r"^(tg|reels|ytpriv|ytpub|ytunlist):"))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        print(f"FATAL bot polling stopped: {e}")
        raise


if __name__ == "__main__":
    main()
'''

start = t.find("def main():")
if start < 0:
    print("no main")
else:
    p.write_text(t[:start] + new_main)
    print("main replaced for reconnect")
