"""Last-resort: ensure chess_telegram_bot_v2.py compiles; fix start() help if broken."""
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

t2 = t.replace(
    '"Custom PGN: send `.pgn` file or `/pgn` then paste\n',
    '"Custom PGN: send `.pgn` file or `/pgn` then paste\\n',
)
# also fix unescaped real newline after paste
t2 = t2.replace(
    '"Custom PGN: send `.pgn` file or `/pgn` then paste\n',
    '"Custom PGN: send `.pgn` file or `/pgn` then paste\\n',
)
if ok(t2):
    p.write_text(t2)
    print("fixed paste-newline")
    raise SystemExit(0)

safe = '''async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return
    await update.message.reply_text(
        "Chess Video Agent Bot\\n\\n"
        "Online: /silent NAME\\n"
        "Lichess: /lichess NAME\\n"
        "Offline: /offline NAME\\n"
        "PGN: send .pgn or /pgn\\n"
        "Photos: /setwhite then image, /setblack then image\\n"
        "/clearphotos /trapofday /traps /trend /duration 5 /theme green"
    )


'''
t3 = re.sub(
    r"async def start\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):.*?(?=\nasync def )",
    safe,
    t,
    count=1,
    flags=re.DOTALL,
)
if ok(t3):
    p.write_text(t3)
    print("start() rewritten — bot compiles")
else:
    t4 = re.sub(
        r"async def start\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):.*?(?=\nasync def )",
        safe,
        t2,
        count=1,
        flags=re.DOTALL,
    )
    if ok(t4):
        p.write_text(t4)
        print("start() rewritten on t2 — bot compiles")
    else:
        print("CRITICAL: could not fix bot syntax")
        raise SystemExit(1)
