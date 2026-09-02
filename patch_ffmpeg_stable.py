"""Fix MoviePy broken pipe: normalize frame sizes + safer write + no heavy vignette."""
from pathlib import Path
import re

p = Path("chess_video_agent_v2.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()

if "def _normalize_frames" not in t:
    norm = '''
def _normalize_frames(frames):
    if not frames:
        return frames
    import numpy as np
    from PIL import Image as _PImage
    th = max(f.shape[0] for f in frames)
    tw = max(f.shape[1] for f in frames)
    if tw % 2: tw += 1
    if th % 2: th += 1
    out = []
    for f in frames:
        if f.shape[0] == th and f.shape[1] == tw:
            out.append(f)
            continue
        im = _PImage.fromarray(f)
        canvas = _PImage.new("RGB", (tw, th), (8, 12, 22))
        canvas.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
        out.append(np.array(canvas))
    return out


'''
    if "def _pad_to_16x9" in t:
        t = t.replace("def _pad_to_16x9", norm + "def _pad_to_16x9", 1)
    elif "def render_frame" in t:
        t = t.replace("def render_frame", norm + "def render_frame", 1)
    print("normalize added")

for old in [
    "clip = ImageSequenceClip(frames, durations=durations)",
    "video = ImageSequenceClip(frames, durations=durations)",
]:
    idx = 0
    while True:
        i = t.find(old, idx)
        if i < 0:
            break
        prev = t[max(0, i - 80):i]
        if "_normalize_frames" not in prev:
            t = t[:i] + "frames = _normalize_frames(frames)\n    " + t[i:]
            print("wired normalize")
            idx = i + 60
        else:
            idx = i + 40

t2 = re.sub(
    r"    # broadcast_elite_bg: soft radial vignette\n    try:.*?except Exception:\n        pass\n",
    "    # vignette disabled\n",
    t,
    count=1,
    flags=re.DOTALL,
)
if t2 != t:
    t = t2
    print("vignette off")

if 'ffmpeg_params=["-pix_fmt", "yuv420p"' not in t:
    t = t.replace(
        'clip.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None)',
        'clip.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None, threads=1, preset="ultrafast", ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])',
    )
    print("write hardened")

p.write_text(t)
compile(t, "chess_video_agent_v2.py", "exec")
print("OK")
