"""Broadcast-elite look: larger board, glass player cards, gradient bg, stronger frame."""
from pathlib import Path
import re

p = Path("chess_video_agent_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()
n = 0

if "BOARD_SIZE = 720" in t:
    t = t.replace("BOARD_SIZE = 720", "BOARD_SIZE = 820", 1)
    n += 1
    print("BOARD_SIZE 820")

if "FPS = 2" in t and "FPS = 3" not in t:
    t = t.replace("FPS = 2", "FPS = 3", 1)
    n += 1
    print("FPS 3")

if "broadcast_elite_bg" not in t:
    needle = 'canvas = Image.new("RGBA", (total_w, total_h), (10, 14, 26, 255))  # elite navy'
    if needle not in t:
        needle = 'canvas = Image.new("RGBA", (total_w, total_h), (12, 16, 28, 255))  # pro studio navy'
    if needle not in t:
        m = re.search(r'canvas = Image\.new\("RGBA", \(total_w, total_h\), \([^)]+\)\)', t)
        if m:
            needle = m.group(0)
    if needle in t:
        inject = needle + '''
    # broadcast_elite_bg: soft radial vignette
    try:
        import math
        px = canvas.load()
        cx, cy = total_w // 2, total_h // 2
        max_r = math.hypot(cx, cy) or 1
        for yy in range(0, total_h, 2):
            for xx in range(0, total_w, 2):
                r = math.hypot(xx - cx, yy - cy) / max_r
                shade = int(8 + 18 * (r ** 1.4))
                c0 = px[xx, yy]
                px[xx, yy] = (
                    max(0, c0[0] - shade),
                    max(0, c0[1] - shade),
                    max(0, c0[2] - shade),
                    c0[3] if len(c0) > 3 else 255,
                )
                if xx + 1 < total_w:
                    px[xx + 1, yy] = px[xx, yy]
                if yy + 1 < total_h:
                    px[xx, yy + 1] = px[xx, yy]
                    if xx + 1 < total_w:
                        px[xx + 1, yy + 1] = px[xx, yy]
    except Exception:
        pass
'''
        t = t.replace(needle, inject, 1)
        n += 1
        print("vignette bg")

if "gold frame" in t or "elite gold" in t:
    t2 = t.replace("outline=(212, 175, 55, 220), width=3)", "outline=(230, 190, 70, 255), width=4)")
    t2 = t2.replace("outline=(180, 140, 40, 120), width=1)", "outline=(212, 175, 55, 160), width=2)")
    if t2 != t:
        t = t2
        n += 1
        print("gold frame stronger")

if "fill=(18, 24, 40, 255)" in t:
    t = t.replace("fill=(18, 24, 40, 255)", "fill=(14, 20, 36, 245)", 2)
    n += 1
    print("glass bars")

if 'DEFAULT_THEME = "green"' in t:
    t = t.replace('DEFAULT_THEME = "green"', 'DEFAULT_THEME = "brown"', 1)
    n += 1
    print("default brown")

p.write_text(t)
compile(t, "x", "exec")
print(f"OK patches={n}")
