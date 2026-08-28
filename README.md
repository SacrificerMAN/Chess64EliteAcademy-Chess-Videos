# Chess64 Video Tool

Generate Long + Shorts + Reels from local PGN, file upload, or built-in traps.

## Local
```bash
export STOCKFISH_PATH=/path/to/stockfish
./run_web_local.sh
# http://127.0.0.1:8080
```

## Railway
1. Push this repo to GitHub
2. Railway → New Project → Deploy from GitHub
3. Open the generated domain

## Features
- Local PGN paste / .pgn upload
- Trap library + Trap of the Day
- Long video, Shorts, Reels 9:16
- Thumbnails + YouTube metadata
- Optional Telegram bot: `python chess_telegram_bot_v2.py`
