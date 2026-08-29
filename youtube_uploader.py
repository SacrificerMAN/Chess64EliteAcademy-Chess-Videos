#!/usr/bin/env python3
"""YouTube Data API v3 uploader for Chess Video Agent."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent

def _cred_path(env_key: str, default_name: str) -> Path:
    raw = (os.environ.get(env_key) or "").strip()
    default = SCRIPT_DIR / default_name
    if not raw:
        return default
    if raw.startswith("GOCSPX-") or (not raw.endswith(".json") and "/" not in raw and "\\" not in raw):
        return default
    cand = Path(raw)
    if cand.exists():
        return cand
    return default

CLIENT_SECRETS = _cred_path("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
TOKEN_PATH = _cred_path("YOUTUBE_TOKEN", "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def get_youtube_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS.exists():
                raise FileNotFoundError(
                    f"Missing {CLIENT_SECRETS}\n"
                    "Download OAuth Desktop client JSON from Google Cloud Console "
                    "and save as client_secrets.json. On Railway set CLIENT_SECRETS_B64 "
                    "to base64 of that file, and YOUTUBE_TOKEN_B64 from token.json after local auth."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            try:
                creds = flow.run_local_server(port=0)
            except Exception:
                creds = flow.run_console()
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def add_to_playlist(youtube, video_id: str, playlist_id: str) -> None:
    if not playlist_id or not video_id:
        return
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: Optional[list] = None,
    privacy: str = "private",
    category_id: str = "20",
    playlist_id: Optional[str] = None,
    publish_at: Optional[str] = None,
) -> dict:
    from googleapiclient.http import MediaFileUpload

    youtube = get_youtube_service()
    body = {
        "snippet": {
            "title": (title or "Chess video")[:100],
            "description": (description or "")[:5000],
            "tags": (tags or ["chess"])[:30],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy if privacy in ("private", "unlisted", "public") else "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    if publish_at and privacy == "private":
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at

    media = MediaFileUpload(video_path, chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  upload {int(status.progress() * 100)}%")
    video_id = response.get("id")
    if playlist_id and video_id:
        try:
            add_to_playlist(youtube, video_id, playlist_id)
        except Exception as e:
            print(f"  playlist add failed: {e}")
    return {"id": video_id, "url": f"https://youtu.be/{video_id}" if video_id else None}
