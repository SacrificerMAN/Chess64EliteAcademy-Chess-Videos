"""ALWAYS rewrite /start help + ensure photo/flag commands & handlers exist."""
from pathlib import Path
import re

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()

if "_flag_path_for_code" not in t:
    t = '''
def _flag_path_for_code(code: str):
    code = (code or "").strip().lower()
    if len(code) != 2 or not code.isalpha():
        return None
    flags_dir = SCRIPT_DIR / "flags"
    flags_dir.mkdir(exist_ok=True)
    dest = flags_dir / f"{code}.png"
    if dest.exists() and dest.stat().st_size > 50:
        return dest
    try:
        import urllib.request
        req = urllib.request.Request(
            f"https://flagcdn.com/w80/{code}.png",
            headers={"User-Agent": "Chess64/2.3"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            dest.write_bytes(r.read())
        if dest.exists() and dest.stat().st_size > 50:
            return dest
    except Exception as e:
        print(f"flag download fail {code}: {e}")
    return None

''' + t

if "async def cmd_setwhiteflag" not in t:
    cmds = '''
async def cmd_setwhiteflag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    code = (context.args[0] if context.args else "").strip().upper()
    if len(code) != 2:
        await update.message.reply_text("Usage: /setwhiteflag IR")
        return
    path = _flag_path_for_code(code)
    if not path:
        await update.message.reply_text(f"Could not load flag {code}")
        return
    context.user_data["custom_white_flag"] = str(path.resolve())
    await update.message.reply_text(f"WHITE flag set: {code}")

async def cmd_setblackflag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    code = (context.args[0] if context.args else "").strip().upper()
    if len(code) != 2:
        await update.message.reply_text("Usage: /setblackflag US")
        return
    path = _flag_path_for_code(code)
    if not path:
        await update.message.reply_text(f"Could not load flag {code}")
        return
    context.user_data["custom_black_flag"] = str(path.resolve())
    await update.message.reply_text(f"BLACK flag set: {code}")

'''
    if "async def cmd_clearphotos" in t:
        t = t.replace("async def cmd_clearphotos", cmds + "async def cmd_clearphotos", 1)
    else:
        t = t.replace("\ndef main():", cmds + "\ndef main():", 1)

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
        "Photos + Flags (manual):\\n"
        "/setwhite  then send WHITE image\\n"
        "/setblack  then send BLACK image\\n"
        "/setwhiteflag IR\\n"
        "/setblackflag US\\n"
        "/clearphotos  clear faces+flags\\n\\n"
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
    print("start() ALWAYS rewritten with flags")
else:
    print("WARN: start/help markers missing")

if 'CommandHandler("setwhiteflag"' not in t:
    for needle in [
        'app.add_handler(CommandHandler("setblack", cmd_setblack))',
        'app.add_handler(CommandHandler("setwhite", cmd_setwhite))',
        'app.add_handler(CommandHandler("clearphotos", cmd_clearphotos))',
        'app.add_handler(CommandHandler("cancel", cancel))',
    ]:
        if needle in t:
            t = t.replace(
                needle,
                needle
                + '\n    app.add_handler(CommandHandler("setwhiteflag", cmd_setwhiteflag))'
                + '\n    app.add_handler(CommandHandler("setblackflag", cmd_setblackflag))',
                1,
            )
            print("flag handlers registered")
            break
else:
    print("flag handlers already in main")

if 'get("custom_white_flag")' not in t:
    block = (
        '        cwf = context.user_data.get("custom_white_flag")\n'
        '        cbf = context.user_data.get("custom_black_flag")\n'
        '        if cwf and Path(cwf).exists():\n'
        '            wf = cwf\n'
        '        if cbf and Path(cbf).exists():\n'
        '            bf = cbf\n'
    )
    for mkr in [
        '            print(f"  MANUAL BLACK photo: {cb}")\n',
        '            bp = cb\n',
        '        bp, bf = await asyncio.to_thread(resolve_player_assets, black)\n',
    ]:
        if mkr in t:
            t = t.replace(mkr, mkr + block, 1)
            print("flag override in build")
            break

p.write_text(t)
compile(t, "chess_telegram_bot_v2.py", "exec")
assert "/setwhiteflag" in t
print("FINAL_UI_OK")
