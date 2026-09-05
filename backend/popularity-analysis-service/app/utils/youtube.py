from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from app.core.exceptions import InvalidYouTubeUrlError

YOUTUBE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{6,20}$")


def extract_video_id(value: str) -> str:
    """Extract a YouTube video id from common URL formats or return a raw id."""
    value = value.strip()

    if YOUTUBE_ID_PATTERN.match(value) and "http" not in value:
        return value

    parsed = urlparse(value)
    host = parsed.netloc.lower().replace("www.", "")

    if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return video_id
        if parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2:
                return parts[1]

    if host == "youtu.be":
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return parts[0]

    raise InvalidYouTubeUrlError("Invalid YouTube URL or video id. Please provide a valid trailer link.")


def build_youtube_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def build_thumbnail_url(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
