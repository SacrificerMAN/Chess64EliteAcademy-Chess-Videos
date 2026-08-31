"""Add /setwhite /setblack manual photos. Does NOT touch help text strings."""
from pathlib import Path

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    print("no bot")
    raise SystemExit(0)

t = p.read_text()
if "cmd_setwhite" in t:
    print("manual photos already present")
    raise SystemExit(0)

manual_code = '''

async def cmd_setwhite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    context.user_data["expect_photo"] = "white"
    await update.message.reply_text("Send WHITE player photo now (as image).")


async def cmd_setblack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    context.user_data["expect_photo"] = "black"
    await update.message.reply_text("Send BLACK player photo now (as image).")


async def cmd_clearphotos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    for k in ("custom_white_photo", "custom_black_photo"):
        path = context.user_data.pop(k, None)
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass
    context.user_data.pop("expect_photo", None)
    await update.message.reply_text("Custom photos cleared.")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update.effective_user.id):
        return
    role = context.user_data.get("expect_photo")
    if role not in ("white", "black"):
        return
    photo = update.message.photo
    if not photo:
        return
    file = await photo[-1].get_file()
    photos_dir = JOBS_DIR / "custom_photos" / str(update.effective_user.id)
    photos_dir.mkdir(parents=True, exist_ok=True)
    dest = photos_dir / f"{role}.jpg"
    await file.download_to_drive(custom_path=str(dest))
    key = "custom_white_photo" if role == "white" else "custom_black_photo"
    context.user_data[key] = str(dest)
    context.user_data.pop("expect_photo", None)
    await update.message.reply_text(f"{role.upper()} photo saved.")


'''

t = t.replace("\ndef main():", manual_code + "\ndef main():", 1)
t = t.replace(
    'app.add_handler(CommandHandler("cancel", cancel))',
    'app.add_handler(CommandHandler("cancel", cancel))\n'
    '    app.add_handler(CommandHandler("setwhite", cmd_setwhite))\n'
    '    app.add_handler(CommandHandler("setblack", cmd_setblack))\n'
    '    app.add_handler(CommandHandler("clearphotos", cmd_clearphotos))\n'
    '    app.add_handler(MessageHandler(filters.PHOTO, on_photo))',
    1,
)
old = (
    "        wp, wf = await asyncio.to_thread(resolve_player_assets, white)\n"
    "        bp, bf = await asyncio.to_thread(resolve_player_assets, black)\n"
)
new = old + (
    "        cw = context.user_data.get(\"custom_white_photo\")\n"
    "        cb = context.user_data.get(\"custom_black_photo\")\n"
    "        if cw and Path(cw).exists():\n"
    "            wp = cw\n"
    "        if cb and Path(cb).exists():\n"
    "            bp = cb\n"
)
if old in t and "custom_white_photo" not in t:
    t = t.replace(old, new, 1)

p.write_text(t)
try:
    compile(t, "chess_telegram_bot_v2.py", "exec")
    print("manual photos added; syntax OK")
except SyntaxError as e:
    print(f"ERROR after patch: {e}")
    raise
