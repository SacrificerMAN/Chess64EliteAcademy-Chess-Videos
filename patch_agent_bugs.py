"""Patch known bugs in chess_video_agent_v2.py at Docker build time."""
from pathlib import Path

p = Path("chess_video_agent_v2.py")
if not p.exists():
    print("agent missing, skip")
    raise SystemExit(0)

t = p.read_text()
changed = False

old = """    commentary_lines: Optional[List[str]] = None,
    voice: str = "en-US-ChristopherNeural",
) -> str:
    \"\"\"
    Board video + move sounds + spoken commentary (Gemini lines or SAN fallback).
    \"\"\"
"""
new = """    commentary_lines: Optional[List[str]] = None,
    voice: str = "en-US-ChristopherNeural",
    watermark: Optional[str] = None,
    intro_card: bool = True,
    viral_hook: Optional[str] = None,
    clock_text: Optional[str] = None,
    opening_text: Optional[str] = None,
    elo_badge: Optional[str] = None,
) -> str:
    \"\"\"
    Board video + move sounds + spoken commentary (Gemini lines or SAN fallback).
    \"\"\"
"""
if "watermark: Optional[str] = None,\n    intro_card: bool = True," not in t and old in t:
    t = t.replace(old, new, 1)
    changed = True
    print("patched create_commentary_video signature")
elif "watermark: Optional[str] = None,\n    intro_card: bool = True," in t:
    print("commentary watermark already patched")
else:
    print("WARN: commentary signature pattern not found")

for bad, good in [
    ('"gemini-2.5-flash-lite"', '"gemini-2.0-flash"'),
    ("'gemini-2.5-flash-lite'", "'gemini-2.0-flash'"),
]:
    if bad in t:
        t = t.replace(bad, good)
        changed = True
        print(f"gemini model {bad} -> {good}")

if changed:
    p.write_text(t)
    print("agent bugs patched OK")
else:
    print("no agent changes")
