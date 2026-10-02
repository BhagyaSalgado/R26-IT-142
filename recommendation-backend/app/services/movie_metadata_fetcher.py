"""Fetches real movie metadata (plot, cast, director, ratings) from OMDb.

The LMTD-9 genre model was trained on exactly this kind of metadata — it
does not look at the trailer's video/audio at all, so this is the only way
to feed it real input. Requires OMDB_API_KEY in .env (free key from
http://www.omdbapi.com/apikey.aspx). Returns None on any failure (missing
key, movie not found, network error) so callers can fall back honestly
instead of guessing.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Words that commonly sit right before/after "trailer"/"teaser" in a
# marketing filename but are never part of the actual movie title.
_MARKETING_WORDS = {
    "official", "international", "main", "final", "full", "new", "first",
    "exclusive", "red", "band", "extended", "special", "look", "clip",
    "hd", "4k", "movie", "film", "in", "theaters", "release", "us",
}
_TRAILER_SPLIT = re.compile(r"\btrailer\b|\bteaser\b", re.IGNORECASE)
_YEAR_TOKEN = re.compile(r"^(19|20)\d{2}$")
_WORD_TOKEN = re.compile(r"[\w:'&-]+")


def _clean_title(raw_title: str) -> str:
    """Extract a likely real movie title from a noisy trailer filename/title.

    Real trailer titles look like "The Conjuring Official Main Trailer HD"
    or "Top Gun: Maverick - Official Trailer 2022 - Paramount Pictures".
    Cuts at the first "trailer"/"teaser" word, then strips trailing
    marketing words and a trailing year token from what's left.
    """
    match = _TRAILER_SPLIT.search(raw_title)
    prefix = raw_title[: match.start()] if match else raw_title

    words = _WORD_TOKEN.findall(prefix)
    while words and (words[-1].lower() in _MARKETING_WORDS or _YEAR_TOKEN.match(words[-1])):
        words.pop()

    cleaned = " ".join(words).strip(" -:_")
    return cleaned or raw_title.strip()


def _title_candidates(cleaned_title: str) -> list[str]:
    """Progressively shorter prefixes of the cleaned title, longest first.

    Real trailer filenames have noise the marketing-word list can't fully
    anticipate (typos like "Wolrdwide", cast names prefixed before the
    title, studio names). Rather than enumerate every pattern, retry OMDb
    with fewer trailing words until something matches — movie titles are
    usually short, so this converges quickly without needing to know what
    the specific noise was.
    """
    words = [w for w in cleaned_title.split() if w not in ("-", ":")]
    seen: set[str] = set()
    candidates: list[str] = []
    for n in range(len(words), 0, -1):
        candidate = " ".join(words[:n])
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)
    return candidates[:6]


def _omdb_get(settings: Any, params: dict[str, str]) -> dict[str, Any] | None:
    try:
        response = httpx.get(
            settings.omdb_base_url,
            params={"apikey": settings.omdb_api_key, **params},
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("OMDb request failed for %s: %s", params, exc)
        return None


@lru_cache(maxsize=256)
def fetch_movie_metadata(trailer_title: str) -> dict[str, Any] | None:
    """Look up real movie metadata by (cleaned) trailer title via OMDb.

    Returns a dict with title/director/actors/plot/imdb_rating/metascore/
    runtime_minutes, or None if unavailable (no API key, not found, error).
    Cached per title for the life of the process to avoid repeat lookups.
    """
    settings = get_settings()
    if not settings.omdb_api_key:
        logger.info("OMDB_API_KEY not configured — real genre metadata unavailable.")
        return None

    query_title = _clean_title(trailer_title)
    if not query_title:
        return None

    payload: dict[str, Any] | None = None
    matched_candidate = None
    for candidate in _title_candidates(query_title):
        # Exact-title lookup first (cheap, precise); fall back to fuzzy
        # search + fetch-by-imdbID for this candidate before shortening it.
        attempt = _omdb_get(settings, {"t": candidate, "plot": "full"})
        if not attempt or attempt.get("Response") != "True":
            search_payload = _omdb_get(settings, {"s": candidate})
            results = (search_payload or {}).get("Search") if isinstance(search_payload, dict) else None
            if isinstance(results, list) and results:
                imdb_id = results[0].get("imdbID")
                if imdb_id:
                    attempt = _omdb_get(settings, {"i": imdb_id, "plot": "full"})

        if attempt and attempt.get("Response") == "True":
            payload = attempt
            matched_candidate = candidate
            break

    if not isinstance(payload, dict):
        logger.info("OMDb found no match for '%s' (queried as '%s').", trailer_title, query_title)
        return None
    if matched_candidate != query_title:
        logger.info("OMDb matched '%s' via shortened query '%s' (from '%s').", payload.get("Title"), matched_candidate, query_title)

    def _num(value: Any, default: float) -> float:
        try:
            text = str(value).split("/")[0].replace(",", "").strip()
            return float(text)
        except (TypeError, ValueError):
            return default

    runtime_text = str(payload.get("Runtime") or "").replace(" min", "").strip()
    try:
        runtime_minutes = float(runtime_text)
    except ValueError:
        runtime_minutes = 120.0

    genres = [g.strip() for g in str(payload.get("Genre") or "").split(",") if g.strip()]

    return {
        "title": payload.get("Title") or query_title,
        "director": payload.get("Director") or "",
        "actors": payload.get("Actors") or "",
        "plot": payload.get("Plot") or "",
        "genres": genres,  # real, human-curated IMDb genre tags — ground truth, not a prediction
        "imdb_rating": _num(payload.get("imdbRating"), 6.0),
        "metascore": _num(payload.get("Metascore"), 55.0),
        "runtime_minutes": runtime_minutes,
        "imdb_id": payload.get("imdbID"),
        "released": payload.get("Released") or "",  # real theatrical release date, e.g. "21 Jul 2023"
    }
