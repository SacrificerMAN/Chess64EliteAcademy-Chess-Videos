Drop `Inter-Regular.ttf` and `Inter-Bold.ttf` (or any licensed brand fonts)
here. `app/utils.py:load_font()` falls back to PIL's built-in bitmap font if
these are absent, so the renderer works out of the box — but text will look
much better with real TTFs bundled into the Docker image.
