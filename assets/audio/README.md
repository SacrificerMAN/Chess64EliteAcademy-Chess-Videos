Chess move sounds (Chess.com-style pack used by the pipeline):

- move_click.mp3       — primary move click (required for real clicks)
- chess_move_self.mp3  — same as above (fallback name)
- chess_capture.mp3    — capture (available for future use)
- chess_move_check.mp3 — check (available for future use)

If none of move_click / chess_move_self exist, a synthetic wood-knock is used.

`.mp3.b64` files are decoded on Docker build / start via decode_sounds.py.
