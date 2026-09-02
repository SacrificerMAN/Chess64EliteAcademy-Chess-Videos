"""Very visible look upgrade: 16:9 studio frame, brown default in bot, gold accents."""
from pathlib import Path

agent = Path("chess_video_agent_v2.py")
if agent.exists():
    t = agent.read_text()
    if "studio_16x9_pad" not in t and "_pad_to_16x9" not in t:
        pad_fn = '''
def _pad_to_16x9(img: Image.Image, bg=(8, 12, 22)) -> Image.Image:
    """studio_16x9_pad — cinematic letterbox with navy sides, not pure black."""
    w, h = img.size
    target_w = int(h * 16 / 9)
    target_h = h
    if target_w < w:
        target_w = w
        target_h = int(w * 9 / 16)
    out = Image.new("RGB", (target_w, target_h), bg)
    x = (target_w - w) // 2
    y = (target_h - h) // 2
    if img.mode == "RGBA":
        out.paste(img, (x, y), img)
    else:
        out.paste(img.convert("RGB"), (x, y))
    try:
        from PIL import ImageDraw
        d = ImageDraw.Draw(out)
        d.rectangle([0, 0, target_w - 1, 3], fill=(201, 162, 39))
        d.rectangle([0, target_h - 4, target_w - 1, target_h - 1], fill=(201, 162, 39))
    except Exception:
        pass
    return out


'''
        if "def render_frame(" in t:
            t = t.replace("def render_frame(", pad_fn + "def render_frame(", 1)
            t = t.replace(
                'frames.append(np.array(img.convert("RGB")))',
                'frames.append(np.array(_pad_to_16x9(img.convert("RGB"))))',
            )
            t = t.replace(
                "frames.append(np.array(img))",
                'frames.append(np.array(_pad_to_16x9(img if img.mode=="RGB" else img.convert("RGB"))))',
            )
            t = t.replace(
                'frames.append(np.array(intro.convert("RGB")))',
                'frames.append(np.array(_pad_to_16x9(intro.convert("RGB"))))',
            )
            print("16:9 pad wired")
        agent.write_text(t)

    t = agent.read_text()
    if 'DEFAULT_THEME = "green"' in t:
        t = t.replace('DEFAULT_THEME = "green"', 'DEFAULT_THEME = "brown"', 1)
        agent.write_text(t)
        print("agent theme brown")

    t = agent.read_text()
    if '"square light lastmove": "#cdd26a"' in t:
        t = t.replace('"square light lastmove": "#cdd26a"', '"square light lastmove": "#f0e68c"')
        t = t.replace('"square dark lastmove": "#aaa23b"', '"square dark lastmove": "#c4a035"')
        agent.write_text(t)
        print("lastmove brighter")

bot = Path("chess_telegram_bot_v2.py")
if bot.exists():
    t = bot.read_text()
    if 'DEFAULT_THEME = "green"' in t:
        t = t.replace('DEFAULT_THEME = "green"', 'DEFAULT_THEME = "brown"', 1)
        print("bot DEFAULT_THEME brown")
    t = t.replace("/theme green", "/theme brown")
    bot.write_text(t)

print("done")
for f in ["chess_video_agent_v2.py", "chess_telegram_bot_v2.py"]:
    if Path(f).exists():
        compile(Path(f).read_text(), f, "exec")
        print("syntax", f, "OK")
