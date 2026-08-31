"""Add /setwhite /setblack and wire them into video render."""
from pathlib import Path

p = Path("chess_telegram_bot_v2.py")
if not p.exists():
    print("no bot")
    raise SystemExit(0)

t = p.read_text()

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
    try:
        await file.download_to_drive(custom_path=str(dest))
    except TypeError:
        await file.download_to_drive(str(dest))
    except Exception:
        data = await file.download_as_bytearray()
        dest.write_bytes(bytes(data))
    if not dest.exists() or dest.stat().st_size < 100:
        await update.message.reply_text("Photo download failed, try again.")
        return
    key = "custom_white_photo" if role == "white" else "custom_black_photo"
    context.user_data[key] = str(dest.resolve())
    context.user_data.pop("expect_photo", None)
    await update.message.reply_text(
        f"{role.upper()} photo saved ({dest.stat().st_size} bytes). Generate a game next."
    )


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
    print("handlers added")
else:
    print("handlers already present")

if "MANUAL WHITE photo" not in t:
    old = (
        "        wp, wf = await asyncio.to_thread(resolve_player_assets, white)\n"
        "        bp, bf = await asyncio.to_thread(resolve_player_assets, black)\n"
    )
    new = (
        "        wp, wf = await asyncio.to_thread(resolve_player_assets, white)\n"
        "        bp, bf = await asyncio.to_thread(resolve_player_assets, black)\n"
        "        cw = context.user_data.get(\"custom_white_photo\")\n"
        "        cb = context.user_data.get(\"custom_black_photo\")\n"
        "        if cw and Path(cw).exists() and Path(cw).stat().st_size > 200:\n"
        "            wp = cw\n"
        "            print(f\"  MANUAL WHITE photo: {cw}\")\n"
        "        if cb and Path(cb).exists() and Path(cb).stat().st_size > 200:\n"
        "            bp = cb\n"
        "            print(f\"  MANUAL BLACK photo: {cb}\")\n"
    )
    if old in t:
        t = t.replace(old, new, 1)
        print("override wired into build")
    else:
        print("WARN: resolve block not found for override")
else:
    print("override already wired")

p.write_text(t)
compile(t, "chess_telegram_bot_v2.py", "exec")
print("syntax OK")
