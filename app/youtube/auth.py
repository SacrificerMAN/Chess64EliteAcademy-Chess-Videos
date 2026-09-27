"""
Loads YouTube OAuth credentials from env-provided JSON strings (no file
uploads needed on Railway). Expects a previously-completed OAuth flow whose
token JSON (with a refresh_token) is stored in YOUTUBE_TOKEN_JSON.

Run `python -m app.youtube.auth` locally once to complete the interactive
OAuth flow and print a token JSON you can paste into Railway's env vars.
"""
from __future__ import annotations

import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_credentials() -> Credentials:
    if not settings.youtube_token_json:
        raise RuntimeError(
            "YOUTUBE_TOKEN_JSON is not set. Run `python -m app.youtube.auth` "
            "locally to complete OAuth once, then paste the resulting token "
            "JSON into your Railway env vars."
        )
    info = json.loads(settings.youtube_token_json)
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def _run_local_oauth_flow() -> None:
    """One-time interactive helper — not used in the Railway deployment."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not settings.client_secrets_json:
        raise RuntimeError("CLIENT_SECRETS_JSON is not set.")
    client_config = json.loads(settings.client_secrets_json)
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    print("Paste this into YOUTUBE_TOKEN_JSON:")
    print(creds.to_json())


if __name__ == "__main__":
    _run_local_oauth_flow()
