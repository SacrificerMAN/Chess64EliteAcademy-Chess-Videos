"""Force /setwhiteflag /setblackflag + help text + render override."""
from pathlib import Path
import re

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()

if "_flag_path_for_code" not in t:
    helper = '''
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
        url = f"https://flagcdn.com/w80/{code}.png"
        req = urllib.request.Request(url, headers={"User-Agent": "Chess64/2.3"})
        with urllib.request.urlopen(req, timeout=10) as r:
            dest.write_bytes(r.read())
        if dest.exists() and dest.stat().st_size > 50:
            return dest
    except Exception as e:
        print(f"flag download fail {code}: {e}")
    return None


'''
    if "async def cmd_setwhite" in t:
        t = t.replace("async def cmd_setwhite", helper + "async def cmd_setwhite", 1)
    elif "\ndef main():" in t:
        t = t.replace("\ndef main():", "\n" + helper + "\ndef main():", 1)
    else:
        t = helper + t
    print("helper inserted")

if "cmd_setwhiteflag" not in t:
    cmds = '''
async def cmd_setwhiteflag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    code = (context.args[0] if context.args else "").strip().upper()
    if len(code) != 2:
        await update.message.reply_text("Usage: /setwhiteflag IR  (examples: IR US IN NO RU CN FR DE PL CA)")
        return
    path = _flag_path_for_code(code)
    if not path:
        await update.message.reply_text(f"Could not load flag for {code}.")
        return
    context.user_data["custom_white_flag"] = str(path.resolve())
    await update.message.reply_text(f"WHITE flag set: {code}")


async def cmd_setblackflag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    code = (context.args[0] if context.args else "").strip().upper()
    if len(code) != 2:
        await update.message.reply_text("Usage: /setblackflag US  (examples: IR US IN NO RU CN FR DE PL CA)")
        return
    path = _flag_path_for_code(code)
    if not path:
        await update.message.reply_text(f"Could not load flag for {code}.")
        return
    context.user_data["custom_black_flag"] = str(path.resolve())
    await update.message.reply_text(f"BLACK flag set: {code}")


'''
    if "async def cmd_clearphotos" in t:
        t = t.replace("async def cmd_clearphotos", cmds + "async def cmd_clearphotos", 1)
    elif "\ndef main():" in t:
        t = t.replace("\ndef main():", cmds + "\ndef main():", 1)
    print("flag commands inserted")

t = t.replace(
    'for k in ("custom_white_photo", "custom_black_photo"):',
    'for k in ("custom_white_photo", "custom_black_photo", "custom_white_flag", "custom_black_flag"):',
)

if 'get("custom_white_flag")' not in t:
    block = (
        '        cwf = context.user_data.get("custom_white_flag")\n'
        '        cbf = context.user_data.get("custom_black_flag")\n'
        '        if cwf and Path(cwf).exists():\n'
        '            wf = cwf\n'
        '            print(f"  MANUAL WHITE flag: {cwf}")\n'
        '        if cbf and Path(cbf).exists():\n'
        '            bf = cbf\n'
        '            print(f"  MANUAL BLACK flag: {cbf}")\n'
    )
    for m in [
        '            print(f"  MANUAL BLACK photo: {cb}")\n',
        '            bp = cb\n',
    ]:
        if m in t:
            t = t.replace(m, m + block, 1)
            print("flag override injected")
            break

if 'CommandHandler("setwhiteflag"' not in t:
    for needle in [
        'app.add_handler(CommandHandler("setblack", cmd_setblack))',
        'app.add_handler(CommandHandler("clearphotos", cmd_clearphotos))',
        'app.add_handler(CommandHandler("setwhite", cmd_setwhite))',
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
            print("handlers registered")
            break

if "/setwhiteflag" not in t:
    for old_help, new_help in [
        ("/clearphotos  remove custom faces", "/setwhiteflag IR   /setblackflag US\n/clearphotos  remove custom faces+flags"),
        ("/clearphotos remove custom faces", "/setwhiteflag IR   /setblackflag US\n/clearphotos remove custom faces+flags"),
    ]:
        if old_help in t:
            t = t.replace(old_help, new_help, 1)
            print("help line patched")
            break

if "/setwhiteflag" not in t:
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
        "/setwhiteflag IR   /setblackflag US\\n"
        "/clearphotos  remove custom faces+flags\\n\\n"
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
        print("start() rewritten with flags in help")

p.write_text(t)
compile(t, "chess_telegram_bot_v2.py", "exec")
print("OK setwhiteflag", "/setwhiteflag" in t, "handler", 'CommandHandler("setwhiteflag"' in t)
