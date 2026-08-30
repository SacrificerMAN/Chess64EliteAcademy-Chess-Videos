"""Install Chess64 brand logo; SEO title/description/hashtags pipeline unchanged."""
from pathlib import Path
import base64

logo = Path("brand_logo.png")
if not logo.exists() or logo.stat().st_size < 100:
    for name in ("brand_logo.b64",):
        p = Path(name)
        if p.exists() and p.stat().st_size > 100:
            try:
                logo.write_bytes(base64.b64decode(p.read_text().strip()))
                print(f"logo from {name}: {logo.stat().st_size} bytes")
            except Exception as e:
                print("logo decode", e)
    parts = Path("brand_logo_parts")
    if (not logo.exists() or logo.stat().st_size < 100) and parts.exists():
        try:
            data = "".join(f.read_text().strip() for f in sorted(parts.glob("L*")))
            if data:
                logo.write_bytes(base64.b64decode(data))
                print(f"logo from parts: {logo.stat().st_size}")
        except Exception as e:
            print("parts fail", e)

agent = Path("chess_video_agent_v2.py")
if agent.exists():
    t = agent.read_text()
    t2 = t.replace('apply_brand_logo(out, corner="br"', 'apply_brand_logo(out, corner="tl"')
    t2 = t2.replace('apply_brand_logo(img.convert("RGB"), corner="br"', 'apply_brand_logo(img.convert("RGB"), corner="tl"')
    if t2 != t:
        agent.write_text(t2)
        print("logo corner -> top-left")
    print("brand logo patch done (metadata/SEO untouched)")
