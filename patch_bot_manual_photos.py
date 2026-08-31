"""Add /setwhite /setblack; never break help string syntax."""
from pathlib import Path

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    print("no bot")
    raise SystemExit(0)

t = p.read_text()

# Fix broken help from older patch (real newline inside string)
if 'then paste\nPhotos' not in t and 'then paste\nPhotos' in t.replace('\\n', ''):
    pass
t = t.replace(
    '"Custom PGN: send `.pgn` file or `/pgn` then paste\nPhotos:',
    '"Custom PGN: send `.pgn` file or `/pgn` then paste\\nPhotos:',
)

if "cmd_setwhite" not in t:
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
    print("manual photo handlers added")
else:
    print("manual photos already present")

p.write_text(t)
try:
    compile(t, "chess_telegram_bot_v2.py", "exec")
    print("bot syntax OK after manual photos patch")
except SyntaxError as e:
    print(f"warning after patch: {e}")
