"""Fetch YouTube portfolio metrics and write stats.json.

Run from the portfolio repository with:
    python scripts/update_stats.py

The script uses the YouTube Data API and YouTube Analytics API through the
local OAuth helper. Only aggregate public-facing values and review metadata
are written to the output JSON. OAuth credentials and token caches stay
outside this repository.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auth_youtube import get_services  # noqa: E402


OUTPUT_PATH = REPO_DIR / "stats.json"
LONG_FORM_LIMIT = 10
# The Data API does not expose a reliable isShorts field. These are the Shorts
# currently represented in index.html; the duration fallback catches future
# short uploads until this list is updated.
KNOWN_SHORT_IDS = {
    "lPDDWGlH_20",
    "-KA49fBcnqo",
    "sO11K5soRv0",
    "OYwfx5waJUk",
    "_YnQoPPabxQ",
}
SHORT_FALLBACK_SECONDS = 180


def parse_duration(value: str | None) -> int:
    match = re.fullmatch(
        r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?",
        value or "",
    )
    if not match:
        return 0
    return (
        int(match.group("hours") or 0) * 3600
        + int(match.group("minutes") or 0) * 60
        + int(match.group("seconds") or 0)
    )


def format_count(value: int | float) -> str:
    value = float(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{int(value):,}"


def api_date_window(days: int = 90) -> tuple[str, str]:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def response_rows(response: dict[str, Any]) -> list[list[Any]]:
    return response.get("rows", []) or []


def header_indices(response: dict[str, Any]) -> dict[str, int]:
    return {
        header["name"]: index
        for index, header in enumerate(response.get("columnHeaders", []))
    }


def cell(row: list[Any], indices: dict[str, int], name: str, default: Any = 0) -> Any:
    index = indices.get(name)
    return row[index] if index is not None and index < len(row) else default


def query_analytics(
    analytics: Any,
    start_date: str,
    end_date: str,
    metrics: str,
    dimensions: str | None = None,
    filters: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": metrics,
    }
    if dimensions:
        kwargs["dimensions"] = dimensions
    if filters:
        kwargs["filters"] = filters
    if sort:
        kwargs["sort"] = sort
    return analytics.reports().query(**kwargs).execute()


def get_channel_stats(youtube: Any) -> tuple[dict[str, Any], str]:
    response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
    items = response.get("items", [])
    if not items:
        raise RuntimeError("The authenticated Google account has no YouTube channel.")
    channel = items[0]
    return channel.get("statistics", {}), channel.get("snippet", {}).get("title", "")


def is_short(video_id: str, duration_seconds: int) -> bool:
    return video_id in KNOWN_SHORT_IDS or duration_seconds < SHORT_FALLBACK_SECONDS


def get_video_sets(
    youtube: Any, days: int = 90, latest_limit: int = LONG_FORM_LIMIT
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (latest long-form videos, recent long-form videos).

    The latest-ten median must not be limited to the 90-day window. The recent
    set is counted separately for the portfolio's 90-day upload metric.
    """
    channel_response = youtube.channels().list(part="contentDetails", mine=True).execute()
    items = channel_response.get("items", [])
    if not items:
        raise RuntimeError("Could not find the authenticated channel uploads playlist.")
    uploads_playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    latest_long_form: list[dict[str, Any]] = []
    recent_long_form: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        page = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        ids = [item["contentDetails"]["videoId"] for item in page.get("items", [])]
        if ids:
            details = youtube.videos().list(
                part="snippet,contentDetails,statistics", id=",".join(ids)
            ).execute()
            for item in details.get("items", []):
                snippet = item.get("snippet", {})
                published = snippet.get("publishedAt")
                if not published:
                    continue
                published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
                content = item.get("contentDetails", {})
                duration_seconds = parse_duration(content.get("duration"))
                if is_short(item["id"], duration_seconds):
                    continue
                record = {
                    "id": item["id"],
                    "title": snippet.get("title", ""),
                    "published_at": published,
                    "view_count": int(item.get("statistics", {}).get("viewCount", 0)),
                    "duration_seconds": duration_seconds,
                }
                if len(latest_long_form) < latest_limit:
                    latest_long_form.append(record)
                if published_at >= cutoff:
                    recent_long_form.append(record)

        # Uploads are newest-first. Once the page crossed the cutoff and the
        # latest-ten set is full, no later page can change either result.
        page_items = page.get("items", [])
        oldest = page_items[-1].get("snippet", {}).get("publishedAt") if page_items else None
        crossed_cutoff = oldest and datetime.fromisoformat(oldest.replace("Z", "+00:00")) < cutoff
        if len(latest_long_form) >= latest_limit and crossed_cutoff:
            break
        page_token = page.get("nextPageToken")
        if not page_token:
            break

    latest_long_form.sort(key=lambda item: item["published_at"], reverse=True)
    recent_long_form.sort(key=lambda item: item["published_at"], reverse=True)
    return latest_long_form[:latest_limit], recent_long_form


def normalise_age_label(value: Any) -> Any:
    if not value:
        return None
    label = str(value)
    match = re.fullmatch(r"age(\d+)-(\d+)", label)
    return f"{match.group(1)}-{match.group(2)}" if match else label


def main() -> None:
    print("Authenticating with YouTube...")
    youtube, analytics = get_services()
    stats, channel_title = get_channel_stats(youtube)
    start_date, end_date = api_date_window(90)

    print(f"Fetching channel analytics from {start_date} through {end_date}...")
    analytics_response = query_analytics(
        analytics,
        start_date,
        end_date,
        "views,subscribersGained,subscribersLost",
        dimensions="day",
        sort="day",
    )
    indices = header_indices(analytics_response)
    rows = response_rows(analytics_response)
    views_90 = sum(int(cell(row, indices, "views")) for row in rows)
    gained_90 = sum(int(cell(row, indices, "subscribersGained")) for row in rows)
    lost_90 = sum(int(cell(row, indices, "subscribersLost")) for row in rows)

    print("Fetching long-form uploads...")
    latest_ten, recent_long_form = get_video_sets(youtube, 90)
    view_values = [item["view_count"] for item in latest_ten]
    median_views = int(median(view_values)) if len(view_values) == LONG_FORM_LIMIT else 0

    core_audience = None
    try:
        demographics = query_analytics(
            analytics,
            start_date,
            end_date,
            "viewerPercentage",
            dimensions="ageGroup",
            sort="-viewerPercentage",
        )
        demographic_rows = response_rows(demographics)
        demographic_indices = header_indices(demographics)
        if demographic_rows:
            top_age = max(
                demographic_rows,
                key=lambda row: float(cell(row, demographic_indices, "viewerPercentage")),
            )
            core_audience = {
                "age_range": normalise_age_label(cell(top_age, demographic_indices, "ageGroup", None)),
                "viewer_percentage": round(
                    float(cell(top_age, demographic_indices, "viewerPercentage")), 2
                ),
            }
    except Exception as error:
        print(f"Audience demographics unavailable: {error}")

    subscribers = int(stats.get("subscriberCount", 0))
    lifetime_views = int(stats.get("viewCount", 0))
    lifetime_videos = int(stats.get("videoCount", 0))
    output = {
        "updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "YouTube Data API v3 + YouTube Analytics API",
        "channel": channel_title,
        "period": {"start": start_date, "end": end_date},
        "metrics": {
            "subscribers": subscribers,
            "subscribers_display": format_count(subscribers),
            "lifetime_views": lifetime_views,
            "lifetime_views_display": format_count(lifetime_views),
            "lifetime_videos": lifetime_videos,
            "views_last_90_days": views_90,
            "views_last_90_days_display": format_count(views_90),
            "net_subscribers_last_90_days": gained_90 - lost_90,
            "net_subscribers_last_90_days_display": format_count(gained_90 - lost_90),
            "median_long_form_views_last_10": median_views,
            "median_long_form_views_last_10_display": format_count(median_views),
            "long_form_uploads_last_90_days": len(recent_long_form),
            "core_audience": core_audience,
        },
        "manual": {
            "years_gaming_experience": 20,
            "games_covered": None,
        },
        "review": {
            "classification": "Known Shorts IDs are excluded; videos under 180 seconds are treated as Shorts as a fallback because the Data API has no reliable isShorts field.",
            "long_form_videos_used_for_median": latest_ten,
            "subscriber_totals": {"gained": gained_90, "lost": lost_90},
        },
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote reviewable stats: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
