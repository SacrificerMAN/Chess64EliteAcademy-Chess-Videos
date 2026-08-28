#!/usr/bin/env bash
cd "$(dirname "$0")"
export STOCKFISH_PATH="${STOCKFISH_PATH:-$(command -v stockfish || echo /usr/local/bin/stockfish)}"
export PYTHONUNBUFFERED=1
pip install -q -r requirements_chess_agent_v2.txt
python -m uvicorn webapp.app:app --host 0.0.0.0 --port "${PORT:-8080}" --reload
