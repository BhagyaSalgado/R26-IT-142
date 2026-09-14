from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import requests

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError
from app.utils.youtube import build_thumbnail_url, build_youtube_url, extract_video_id


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


class YouTubeService:
    """Fetches trailer metadata and statistics.

    If YOUTUBE_API_KEY is not configured, this service returns deterministic simulated
    data so the backend can be used immediately for frontend and integration testing.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_trailer_data(self, youtube_url_or_id: str) -> Dict[str, Any]:
        video_id = extract_video_id(str(youtube_url_or_id))
        if self.settings.youtube_api_key:
            return self._fetch_from_youtube_api(video_id)
        return self._simulate_trailer_data(video_id)

    def _fetch_from_youtube_api(self, video_id: str) -> Dict[str, Any]:
        endpoint = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": video_id,
            "key": self.settings.youtube_api_key,
        }
        try:
            response = requests.get(endpoint, params=params, timeout=self.settings.youtube_api_timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise ExternalServiceError(f"Failed to fetch YouTube data: {exc}") from exc

        items = payload.get("items", [])
        if not items:
            raise ExternalServiceError("No YouTube video found for the provided id.")

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}) or thumbnails.get("medium", {}) or thumbnails.get("default", {})
        ).get("url", build_thumbnail_url(video_id))

        return {
            "video_id": video_id,
            "youtube_url": build_youtube_url(video_id),
            "title": snippet.get("title", f"Movie Trailer {video_id}"),
            "channel_name": snippet.get("channelTitle", "Unknown Channel"),
            "published_at": snippet.get("publishedAt", _iso(_utc_now() - timedelta(days=30))),
            "thumbnail_url": thumbnail_url,
            "metrics": {
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "favorite_count": int(stats.get("favoriteCount", 0)),
                "source": "youtube_api",
            },
        }

    def _simulate_trailer_data(self, video_id: str) -> Dict[str, Any]:
        digest = hashlib.sha256(video_id.encode("utf-8")).hexdigest()
        seed_int = int(digest[:12], 16)

        view_count = 50_000 + seed_int % 8_000_000
        like_count = max(50, int(view_count * (0.015 + ((seed_int >> 8) % 550) / 10_000)))
        comment_count = max(10, int(view_count * (0.0008 + ((seed_int >> 16) % 90) / 100_000)))
        age_days = 7 + (seed_int % 365)
        published_at = _utc_now() - timedelta(days=age_days)

        return {
            "video_id": video_id,
            "youtube_url": build_youtube_url(video_id),
            "title": f"Simulated Movie Trailer {video_id}",
            "channel_name": "Simulated Studio",
            "published_at": _iso(published_at),
            "thumbnail_url": build_thumbnail_url(video_id),
            "metrics": {
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "favorite_count": 0,
                "source": "simulated",
            },
        }
