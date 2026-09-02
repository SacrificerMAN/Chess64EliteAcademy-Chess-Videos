"""Faster Telegram renders: shorter moves, shallower SF, fewer moves, 720 board."""
from pathlib import Path
bot = Path("chess_telegram_bot_v2.py")
if bot.exists():
    t = bot.read_text()
    t = t.replace("DEFAULT_DURATION = 7.0", "DEFAULT_DURATION = 4.0")
    t = t.replace("DEFAULT_DURATION = 5.0", "DEFAULT_DURATION = 4.0")
    t = t.replace("DEFAULT_DEPTH = 12", "DEFAULT_DEPTH = 10")
    t = t.replace("DEFAULT_DEPTH = 16", "DEFAULT_DEPTH = 10")
    t = t.replace("MAX_MOVES_FOR_BOT = 60", "MAX_MOVES_FOR_BOT = 40")
    bot.write_text(t)
    print("bot speed defaults")
agent = Path("chess_video_agent_v2.py")
if agent.exists():
    t = agent.read_text()
    t = t.replace("BOARD_SIZE = 820", "BOARD_SIZE = 720")
    agent.write_text(t)
    print("board 720")
