"""Telegram: clear webhook + drop pending so polling reconnects cleanly after redeploy."""
from pathlib import Path
p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()
if "delete_webhook" in t and "drop_pending_updates=True" in t:
    print("reconnect already patched")
    raise SystemExit(0)
old = "app.run_polling(allowed_updates=Update.ALL_TYPES)"
new = """async def _post_init(application):
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            print("Webhook cleared; polling ready")
        except Exception as e:
            print(f"delete_webhook note: {e}")
    app.post_init = _post_init
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)"""
if old in t:
    p.write_text(t.replace(old, new, 1))
    print("reconnect patch applied")
else:
    print("run_polling pattern not found")
