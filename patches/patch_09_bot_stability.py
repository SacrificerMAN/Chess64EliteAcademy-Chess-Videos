"""Patch 09 — bot manual photos/flags/help/syntax/stability.

Confirms every documented command is actually registered on the Application,
and that ALLOWED_USER_IDS parsed cleanly, before the bot starts polling.
A missing handler here means a typed command silently does nothing for
users — worth failing the deploy over.
"""
from __future__ import annotations

REQUIRED_COMMANDS = {
    "start", "help", "silent", "pgn", "duration", "theme",
    "setwhite", "setblack", "setwhiteflag", "setblackflag",
    "clearphotos", "trapofday", "trap", "traps", "trend",
}


def apply() -> None:
    from app.config import settings

    if settings.telegram_bot_token:
        from app.telegram_bot import build_application

        app = build_application()
        registered = set()
        for handlers in app.handlers.values():
            for h in handlers:
                cmds = getattr(h, "commands", None)
                if cmds:
                    registered.update(cmds)
        missing = REQUIRED_COMMANDS - registered
        assert not missing, f"Missing bot command handlers: {sorted(missing)}"
    else:
        import logging

        logging.getLogger("chess64.patches").warning(
            "TELEGRAM_BOT_TOKEN not set — skipping bot handler check."
        )

    for uid in settings.allowed_user_ids:
        assert isinstance(uid, int), f"ALLOWED_USER_IDS entry not an int: {uid!r}"
