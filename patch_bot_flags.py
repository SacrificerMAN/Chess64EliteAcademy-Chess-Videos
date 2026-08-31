"""Add /setwhiteflag /setblackflag ISO codes + wire into video render."""
from pathlib import Path

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()
if "cmd_setwhiteflag" in t and "MANUAL WHITE flag" in t:
    print("flags already present")
    raise SystemExit(0)

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

flag_cmds = '''
async def cmd_setwhiteflag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    code = (context.args[0] if context.args else "").strip().upper()
    if len(code) != 2:
        await update.message.reply_text("Usage: /setwhiteflag IR\\nExamples: IR US IN NO RU CN FR DE PL CA")
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
        await update.message.reply_text("Usage: /setblackflag US\\nExamples: IR US IN NO RU CN FR DE PL CA")
        return
    path = _flag_path_for_code(code)
    if not path:
        await update.message.reply_text(f"Could not load flag for {code}.")
        return
    context.user_data["custom_black_flag"] = str(path.resolve())
    await update.message.reply_text(f"BLACK flag set: {code}")


'''

if "_flag_path_for_code" not in t:
    if "async def cmd_setwhite" in t:
        t = t.replace("async def cmd_setwhite", helper + "async def cmd_setwhite", 1)
    else:
        t = t.replace("\\ndef main():", helper + "\\ndef main():", 1)

if "cmd_setwhiteflag" not in t:
    if "async def cmd_clearphotos" in t:
        t = t.replace("async def cmd_clearphotos", flag_cmds + "async def cmd_clearphotos", 1)
    elif "\\ndef main():" in t:
        t = t.replace("\\ndef main():", flag_cmds + "\\ndef main():", 1)

t = t.replace(
    'for k in ("custom_white_photo", "custom_black_photo"):',
    'for k in ("custom_white_photo", "custom_black_photo", "custom_white_flag", "custom_black_flag"):',
)

if "MANUAL WHITE flag" not in t:
    old = (
        "        if cb and Path(cb).exists() and Path(cb).stat().st_size > 200:\\n"
        "            bp = cb\\n"
        '            print(f"  MANUAL BLACK photo: {cb}")\\n'
    )
    # try without double escapes - actual file newlines
    old = (
        "        if cb and Path(cb).exists() and Path(cb).stat().st_size > 200:\n"
        "            bp = cb\n"
        '            print(f"  MANUAL BLACK photo: {cb}")\n'
    )
    new = old + (
        '        cwf = context.user_data.get("custom_white_flag")\n'
        '        cbf = context.user_data.get("custom_black_flag")\n'
        "        if cwf and Path(cwf).exists():\n"
        "            wf = cwf\n"
        '            print(f"  MANUAL WHITE flag: {cwf}")\n'
        "        if cbf and Path(cbf).exists():\n"
        "            bf = cbf\n"
        '            print(f"  MANUAL BLACK flag: {cbf}")\n'
    )
    if old in t:
        t = t.replace(old, new, 1)
        print("flag override wired")
    else:
        print("WARN: photo override block not found")

if 'CommandHandler("setwhiteflag"' not in t:
    for needle in [
        'app.add_handler(CommandHandler("setblack", cmd_setblack))',
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
            print("handlers registered")
            break

if "/setwhiteflag" not in t:
    t = t.replace(
        "/clearphotos  remove custom faces",
        "/setwhiteflag IR  /setblackflag US\\n/clearphotos  remove custom faces+flags",
        1,
    )

p.write_text(t)
compile(t, "chess_telegram_bot_v2.py", "exec")
print("flags patch OK")
