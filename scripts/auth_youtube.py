"""Local YouTube OAuth helper for the portfolio stats updater.

Secrets and refresh tokens stay outside this repository. The helper reuses the
same read-only scopes as the YouTube Dashboard app and can use its existing
OAuth client configuration from the Windows app-data directory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
DEFAULT_APP_DATA_CONFIG = (
    Path(os.environ["APPDATA"])
    / "com.nilvarcus.youtube-dashboard"
    / "youtube-oauth-client.json"
    if os.environ.get("APPDATA")
    else None
)
DEFAULT_TOKEN_PATH = (
    Path(os.environ["LOCALAPPDATA"])
    / "nilvarcus-portfolio"
    / "youtube-stats-token.json"
    if os.environ.get("LOCALAPPDATA")
    else Path.home() / ".nilvarcus-portfolio" / "youtube-stats-token.json"
)


def _client_config_path() -> Path:
    configured = os.environ.get("YOUTUBE_OAUTH_CLIENT_FILE")
    if configured:
        return Path(configured).expanduser()
    if DEFAULT_APP_DATA_CONFIG and DEFAULT_APP_DATA_CONFIG.exists():
        return DEFAULT_APP_DATA_CONFIG
    raise FileNotFoundError(
        "No OAuth client JSON found. Set YOUTUBE_OAUTH_CLIENT_FILE to the "
        "Google Desktop OAuth JSON path."
    )


def _token_path() -> Path:
    return Path(os.environ.get("YOUTUBE_STATS_TOKEN_FILE", DEFAULT_TOKEN_PATH)).expanduser()


def _normalise_client_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Accept both Google downloaded JSON and the dashboard's stored format."""
    if "installed" in raw or "web" in raw:
        return raw
    return {
        "installed": {
            "client_id": raw["client_id"],
            "client_secret": raw.get("client_secret", ""),
            "auth_uri": raw.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": raw.get("token_uri", "https://oauth2.googleapis.com/token"),
            "redirect_uris": ["http://localhost"],
        }
    }


def _load_credentials() -> Credentials | None:
    path = _token_path()
    if not path.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(path), SCOPES)
    except (ValueError, OSError, json.JSONDecodeError):
        return None


def get_credentials() -> Credentials:
    credentials = _load_credentials()
    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        client_path = _client_config_path()
        config = _normalise_client_config(
            json.loads(client_path.read_text(encoding="utf-8"))
        )
        flow = InstalledAppFlow.from_client_config(config, SCOPES)
        credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    token_path = _token_path()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def get_services() -> tuple[Any, Any]:
    """Return authenticated YouTube Data API and Analytics API services."""
    credentials = get_credentials()
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    analytics = build(
        "youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False
    )
    return youtube, analytics
