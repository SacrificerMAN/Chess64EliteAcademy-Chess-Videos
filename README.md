# Chess64 Elite Academy — Production System

Turns a PGN / Chess.com game into a branded board video (long + Shorts),
viral EN+HI SEO metadata (via Gemini), and an optional one-tap YouTube upload.
Runs on Railway as two processes (FastAPI web + Telegram bot poller)
supervised by `scripts/start.sh`.

## Layout

```
chess64/
  app/
    config.py            # env-driven settings
    main.py               # FastAPI app (health, webhook stub, job status)
    telegram_bot.py        # all /commands, job orchestration, inline buttons
    analysis.py            # python-chess + Stockfish wrapper
    player_assets.py       # avatar + flag resolution (Chess.com/wiki/initials)
    storage.py              # in-memory job store + temp workspace mgmt
    utils.py                 # frame padding, flags, text sizing helpers
    render/
      board_renderer.py       # per-move frame rendering (board + studio chrome)
      video_builder.py         # ffmpeg assembly, long video
      shorts.py                  # eval-swing based Shorts/Reels cuts
      thumbnails.py               # 16:9 / 9:16 thumbnail generation
    gemini/
      client.py                    # Gemini REST client
      prompts.py                    # SEO + commentary prompt templates
    youtube/
      auth.py                        # OAuth credential loading
      upload.py                       # resumable upload
    commentary/
      tts.py                            # edge-tts wrapper (long + shorts scripts)
  patches/
    patch_01_player_resolve.py .. patch_10_start.py   # ordered, idempotent
    run_patches.py                                       # applies them in order
  scripts/
    start.sh                                              # Railway entrypoint / supervisor
  Dockerfile
  requirements.txt
  .env.example
```

## Local run

```bash
cp .env.example .env   # fill in tokens/keys
pip install -r requirements.txt
python patches/run_patches.py
bash scripts/start.sh
```

## Notes on scope

This is a complete, working scaffold: every module runs and does real work
(board rendering, ffmpeg assembly, Gemini calls, YouTube upload, Telegram
commands). A few pieces are intentionally left as clearly marked `TODO`
hooks where a production deployment would plug in account-specific details
(e.g. the full `KNOWN_USERNAMES` GM map, a licensed logo asset, a specific
Railway volume path). Nothing here uploads or publishes anything without an
explicit user action (Telegram button tap or CLI call).
