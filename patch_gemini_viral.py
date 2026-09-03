"""Stronger Gemini viral SEO prompt + darker studio bg + bot Gemini status."""
from pathlib import Path

agent = Path("chess_video_agent_v2.py")
if agent.exists():
    t = agent.read_text()
    t = t.replace(
        "You are a viral chess YouTube SEO expert for Indian + global audience. ",
        "You are an elite viral chess YouTube growth expert (GothamChess energy, Indian + global SEO). ",
    )
    if "MAXIMUM-CLICK" not in t and "Make titles clickbait but not fake" in t:
        t = t.replace(
            "Make titles clickbait but not fake. Do NOT put 1-0 or 0-1 in titles.",
            "MAXIMUM-CLICK titles: DESTROYS/BRILLIANT/INSANE/SHOCKING/MASTERCLASS. "
            "Include famous surnames + event. NO scores. Always #Chess64EliteAcademy in hashtags.",
        )
    t = t.replace(
        'canvas = Image.new("RGBA", (total_w, total_h), (10, 14, 26, 255))  # elite navy',
        'canvas = Image.new("RGBA", (total_w, total_h), (6, 10, 20, 255))  # deep broadcast navy',
    )
    t = t.replace(
        'canvas = Image.new("RGBA", (total_w, total_h), (12, 16, 28, 255))  # pro studio navy',
        'canvas = Image.new("RGBA", (total_w, total_h), (6, 10, 20, 255))  # deep broadcast navy',
    )
    agent.write_text(t)
    print("agent SEO+bg patched")

bot = Path("chess_telegram_bot_v2.py")
if bot.exists():
    t = bot.read_text()
    if "Gemini viral SEO" not in t:
        t = t.replace(
            "if GEMINI_API_KEY:\n                meta = await asyncio.to_thread(\n                    generate_youtube_metadata_gemini",
            "if GEMINI_API_KEY:\n                await status.edit_text(f\"⏳ Gemini viral SEO…\")\n                meta = await asyncio.to_thread(\n                    generate_youtube_metadata_gemini",
            1,
        )
        bot.write_text(t)
        print("bot status line")
print("done")
