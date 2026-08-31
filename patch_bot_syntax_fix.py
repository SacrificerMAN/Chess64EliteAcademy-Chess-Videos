"""Ensure chess_telegram_bot_v2.py compiles."""
from pathlib import Path
import re

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    raise SystemExit(0)

t = p.read_text()

def ok(src: str) -> bool:
    try:
        compile(src, str(p), "exec")
        return True
    except SyntaxError as e:
        print(f"syntax error: {e}")
        return False

if ok(t):
    print("bot already compiles")
    raise SystemExit(0)

for a, b in [
    ("then paste\nPhotos:", "then paste\\nPhotos:"),
    ("then paste\n\n", "then paste\\n\\n"),
    ("then paste\n", "then paste\\n"),
]:
    if a in t:
        t = t.replace(a, b)
        print(f"replaced paste-break")

if ok(t):
    p.write_text(t)
    print("fixed — bot compiles")
    raise SystemExit(0)

safe_fn = (
    "async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):\n"
    "    if not _allowed(update.effective_user.id):\n"
    '        await update.message.reply_text("Access denied.")\n'
    "        return\n"
    "    await update.message.reply_text(\n"
    '        "Chess Video Agent Bot\\n\\n"\n'
    '        "Online: /silent NAME\\n"\n'
    '        "Lichess: /lichess NAME\\n"\n'
    '        "Offline: /offline NAME\\n"\n'
    '        "PGN: send .pgn or /pgn\\n"\n'
    '        "Photos: /setwhite then image, /setblack then image\\n"\n'
    '        "/clearphotos /trapofday /traps /trend /duration 5 /theme green",\n'
    "    )\n\n\n"
)

m = re.search(
    r"async def start\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):",
    t,
)
m2 = re.search(r"\nasync def help_cmd\(", t)
if m and m2 and m.start() < m2.start():
    t = t[: m.start()] + safe_fn + t[m2.start() + 1 :]
    if ok(t):
        p.write_text(t)
        print("start() replaced — bot compiles")
        raise SystemExit(0)

print("CRITICAL: could not fix bot syntax")
p.write_text(t)
raise SystemExit(1)
