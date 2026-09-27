from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Runtime settings for Chess64 Elite Academy pipeline."""

    port: int = int(os.environ.get("PORT", "8080"))
    workdir: str = os.environ.get("CHESS64_WORKDIR", "/tmp/chess64_jobs")
    telegram_bot_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    allowed_user_ids: str = os.environ.get("ALLOWED_USER_IDS", "").strip()
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
    default_duration_per_move: float = float(os.environ.get("DEFAULT_DURATION", "4"))
    default_theme: str = os.environ.get("DEFAULT_THEME", "brown")
    default_depth: int = int(os.environ.get("DEFAULT_DEPTH", "10"))
    max_moves_for_bot: int = int(os.environ.get("MAX_MOVES_FOR_BOT", "40"))
    youtube_privacy: str = os.environ.get("YOUTUBE_PRIVACY", "private")
    stockfish_path: str = os.environ.get("STOCKFISH_PATH", "stockfish")

    assets_dir: str = field(
        default_factory=lambda: os.environ.get(
            "CHESS64_ASSETS",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"),
        )
    )

    @property
    def move_click_asset_path(self) -> str | None:
        """
        Chess.com-style move click. Prefers assets/audio/move_click.* then
        chess_move_self.mp3 (same pack as before). Fallback: synthetic knock.
        """
        audio_dir = os.path.join(self.assets_dir, "audio")
        candidates = []
        for name in ("move_click", "chess_move_self"):
            for ext in ("mp3", "wav", "m4a", "ogg"):
                candidates.append(os.path.join(audio_dir, f"{name}.{ext}"))
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    THEMES: dict = field(
        default_factory=lambda: {
            "brown": {"light": "#eed7ba", "dark": "#8a5a3b", "highlight": "#d4af37"},
            "green": {"light": "#eeeed2", "dark": "#769656", "highlight": "#f7ec6d"},
            "blue": {"light": "#dee3e6", "dark": "#4b6b9a", "highlight": "#e0c341"},
            "purple": {"light": "#e8e0f5", "dark": "#6c4b9a", "highlight": "#d9b23a"},
        }
    )


def get_settings() -> Settings:
    return Settings()
