"""
Central, env-driven configuration for Chess64 Elite Academy.
Everything here is intentionally overridable via environment variables so the
same image runs unmodified on Railway.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _list_ints(raw: str) -> list[int]:
    return [int(x) for x in raw.split(",") if x.strip().isdigit()]


@dataclass
class Settings:
    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    allowed_user_ids: list[int] = field(
        default_factory=lambda: _list_ints(os.getenv("ALLOWED_USER_IDS", ""))
    )

    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

    # YouTube
    client_secrets_json: str = os.getenv("CLIENT_SECRETS_JSON", "")
    youtube_token_json: str = os.getenv("YOUTUBE_TOKEN_JSON", "")
    youtube_default_privacy: str = os.getenv("YOUTUBE_DEFAULT_PRIVACY", "private")
    youtube_category_id: str = os.getenv("YOUTUBE_CATEGORY_ID", "20")  # Gaming

    # Brand
    channel_name: str = os.getenv("CHANNEL_NAME", "Chess64 Elite Academy")
    channel_handle: str = os.getenv("CHANNEL_HANDLE", "@Chess64EliteAcademy")
    telegram_channel_url: str = os.getenv("TELEGRAM_CHANNEL_URL", "https://t.me/Messi9354")
    brand_hashtag: str = os.getenv("BRAND_HASHTAG", "#Chess64EliteAcademy")

    # Video look & speed
    board_size: int = int(os.getenv("BOARD_SIZE", "720"))
    board_theme: str = os.getenv("BOARD_THEME", "brown")  # brown|green|blue|purple
    default_duration_per_move: float = float(os.getenv("DEFAULT_DURATION_PER_MOVE", "4"))
    default_depth: int = int(os.getenv("DEFAULT_DEPTH", "10"))
    max_moves_for_bot: int = int(os.getenv("MAX_MOVES_FOR_BOT", "40"))
    ffmpeg_threads: int = int(os.getenv("FFMPEG_THREADS", "1"))

    # Web
    port: int = int(os.getenv("PORT", "8080"))

    # Paths
    workdir: str = os.getenv("CHESS64_WORKDIR", "/tmp/chess64_jobs")
    assets_dir: str = os.getenv(
        "CHESS64_ASSETS_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"),
    )

    @property
    def move_click_asset_path(self) -> str | None:
        """
        Chess.com-style move click. Prefers move_click.* then chess_move_self.mp3.
        Fallback: synthetic wood-knock.
        """
        audio_dir = os.path.join(self.assets_dir, "audio")
        for name in ("move_click", "chess_move_self"):
            for ext in ("mp3", "wav", "m4a", "ogg"):
                path = os.path.join(audio_dir, f"{name}.{ext}")
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

    NAVY_BG: str = "#0b1220"
    GOLD: str = "#d4af37"

    def theme_colors(self, theme: str | None = None) -> dict:
        return self.THEMES.get(theme or self.board_theme, self.THEMES["brown"])


settings = Settings()
os.makedirs(settings.workdir, exist_ok=True)
