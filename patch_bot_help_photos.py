"""Force /start help to list /setwhite /setblack /clearphotos."""
from pathlib import Path
import re

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()
if "/setwhite  then send WHITE" in t:
    print("help already lists photos")
    raise SystemExit(0)

safe = '''async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return
    text = (
        "Chess Video Agent Bot\\n\\n"
        "Online Chess.com:\\n/silent Magnus Carlsen\\n\\n"
        "Online Lichess:\\n/lichess Magnus Carlsen\\n\\n"
        "Offline / FIDE-style:\\n/offline Magnus Carlsen\\n\\n"
        "Custom PGN: send .pgn file or /pgn then paste\\n\\n"
        "Photos (manual):\\n"
        "/setwhite  then send WHITE image\\n"
        "/setblack  then send BLACK image\\n"
        "/clearphotos  remove custom faces\\n\\n"
        "After video is ready you choose:\\n"
        "- Send on Telegram -> manual YouTube upload\\n"
        "- Upload to YouTube -> direct API\\n\\n"
        "/trapofday /trap stafford /traps /trend\\n"
        "/duration 5 /theme green /help"
    )
    await update.message.reply_text(text)


'''
m = re.search(r"async def start\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):", t)
m2 = re.search(r"\nasync def help_cmd\(", t)
if m and m2 and m.start() < m2.start():
    t = t[: m.start()] + safe + t[m2.start() + 1 :]
    p.write_text(t)
    compile(t, str(p), "exec")
    print("start help updated with photo commands")
else:
    print("could not find start/help markers")
