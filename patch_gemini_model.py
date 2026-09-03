"""Default Gemini model → gemini-3.1-flash-lite."""
from pathlib import Path
for name in ("chess_video_agent_v2.py", "chess_telegram_bot_v2.py"):
    p = Path(name)
    if not p.exists():
        continue
    t = p.read_text()
    for old in (
        "gemini-2.0-flash",
        "gemini-2.5-flash-lite",
        "gemini-1.5-flash",
        "gemini-2.5-flash",
    ):
        t = t.replace(
            f'os.environ.get("GEMINI_MODEL", "{old}")',
            'os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")',
        )
    p.write_text(t)
    print(name, "ok" if "gemini-3.1-flash-lite" in p.read_text() else "no change")
