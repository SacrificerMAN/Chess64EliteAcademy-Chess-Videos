"""Install brand_logo.png and overlay it on every video frame. SEO/title/hashtags unchanged."""
from pathlib import Path
import base64

logo = Path("brand_logo.png")
parts_dir = Path("brand_logo_parts")
if not logo.exists() and parts_dir.exists():
    data = "".join((parts_dir / f).read_text() for f in sorted(parts_dir.glob("L*")))
    logo.write_bytes(base64.b64decode(data))
    print(f"assembled brand_logo.png ({logo.stat().st_size} bytes)")
elif logo.exists():
    print(f"brand_logo.png present ({logo.stat().st_size} bytes)")
else:
    print("WARN: no brand logo")

agent = Path("chess_video_agent_v2.py")
if not agent.exists():
    raise SystemExit(0)
t = agent.read_text()
if "def apply_brand_logo" in t:
    print("brand overlay already in agent")
    raise SystemExit(0)

fn = '''
def apply_brand_logo(img: "Image.Image", corner: str = "br", max_h: int = 72) -> "Image.Image":
    """Paste Chess64 Elite Academy logo on frame."""
    from PIL import Image as PILImage
    logo_path = SCRIPT_DIR / "brand_logo.png"
    if not logo_path.exists():
        return img
    try:
        base = img.convert("RGBA")
        logo = PILImage.open(logo_path).convert("RGBA")
        h = max_h
        w = int(logo.width * (h / max(logo.height, 1)))
        logo = logo.resize((max(w, 1), max(h, 1)), PILImage.Resampling.LANCZOS)
        alpha = logo.split()[-1].point(lambda p: int(p * 0.85))
        logo.putalpha(alpha)
        margin = 10
        if corner == "br":
            x, y = base.width - logo.width - margin, base.height - logo.height - margin
        elif corner == "bl":
            x, y = margin, base.height - logo.height - margin
        elif corner == "tl":
            x, y = margin, margin
        else:
            x, y = base.width - logo.width - margin, margin
        base.alpha_composite(logo, (x, y))
        return base.convert("RGB")
    except Exception as e:
        print(f"brand logo skip: {e}")
        return img

'''
anchor = 'def apply_watermark(img: "Image.Image", text: str = "@YourChannel") -> "Image.Image":'
if anchor not in t:
    print("no apply_watermark")
    raise SystemExit(0)
t = t.replace(anchor, fn + "\n" + anchor, 1)
old = '''    draw.text((x, y), text, font=f, fill=(255, 255, 255, 160))
    return PILImage.alpha_composite(base, overlay).convert("RGB")
'''
new = '''    draw.text((x, y), text, font=f, fill=(255, 255, 255, 160))
    out = PILImage.alpha_composite(base, overlay).convert("RGB")
    return apply_brand_logo(out, corner="br", max_h=max(56, base.height // 14))
'''
if old in t:
    t = t.replace(old, new, 1)
old_if = '''    if watermark:
        img = apply_watermark(img.convert("RGB"), watermark)
    else:
        img = img.convert("RGB")
'''
new_if = '''    if watermark:
        img = apply_watermark(img.convert("RGB"), watermark)
    else:
        img = apply_brand_logo(img.convert("RGB"), corner="br")
'''
if old_if in t:
    t = t.replace(old_if, new_if)
agent.write_text(t)
print("brand logo overlay patched into agent")
