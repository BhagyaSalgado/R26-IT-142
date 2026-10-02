"""Downloads real professional trailers, grouped by genre, to build the
per-genre norm corpus.

Everything it writes stays inside recommendation-backend:
  storage/incoming_trailers/<genre>/<slug>.mp4
  storage/incoming_trailers/manifest.csv   (film, genre, file, duration)

Nothing is written to Movie_Trailer-main.

Why a search query instead of hardcoded video IDs: IDs rot when uploads are
removed or re-posted, and an ID list can't be reviewed for correctness at a
glance. The duration filter below is what actually protects corpus quality --
a search can return a full film, a fan edit, or a 15-second teaser, none of
which belong in a norm built from theatrical trailers.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path

OUT_ROOT = Path(__file__).resolve().parent.parent / "storage" / "incoming_trailers"
MANIFEST = OUT_ROOT / "manifest.csv"

# A real theatrical trailer is ~1:30-2:30. Bounds are deliberately generous at
# the top for extended/red-band cuts, but tight enough to exclude full films.
MIN_DURATION_SEC = 45
MAX_DURATION_SEC = 360

FILMS: dict[str, list[str]] = {
    "Action": [
        "Mad Max Fury Road", "John Wick", "John Wick Chapter 2", "The Dark Knight",
        "Mission Impossible Fallout", "Top Gun Maverick", "Casino Royale", "Skyfall",
        "The Bourne Ultimatum", "Terminator 2 Judgment Day", "The Matrix", "Gladiator",
        "Extraction", "The Raid Redemption", "Baby Driver", "Edge of Tomorrow",
        "Kingsman The Secret Service", "Atomic Blonde", "Nobody 2021", "Sicario",
        "Heat 1995", "Speed 1994", "Point Break 1991", "Die Hard", "The Equalizer",
    ],
    "Horror": [
        "The Conjuring", "Annabelle Creation", "Hereditary", "Get Out", "It 2017",
        "The Babadook", "A Quiet Place", "Sinister", "Insidious", "The Witch 2015",
        "Midsommar", "Us 2019", "The Ring 2002", "Halloween 2018", "Smile 2022",
        "Talk to Me 2023", "The Exorcist", "Paranormal Activity", "Saw 2004",
        "The Descent", "It Follows", "Lights Out 2016", "Dont Breathe", "The Nun",
        "Evil Dead 2013",
    ],
    "Comedy": [
        "Superbad", "The Hangover", "Bridesmaids", "Anchorman", "Step Brothers",
        "Tropic Thunder", "21 Jump Street", "Game Night", "The Grand Budapest Hotel",
        "Booksmart", "Knives Out", "Ghostbusters 1984", "Airplane 1980",
        "Dumb and Dumber", "Zoolander", "School of Rock", "Pineapple Express",
        "The Nice Guys", "Hot Fuzz", "Shaun of the Dead", "Borat", "Mean Girls",
        "Napoleon Dynamite", "Little Miss Sunshine", "The Big Lebowski",
    ],
    "Romance": [
        "The Notebook", "Past Lives 2023", "La La Land", "Pride and Prejudice 2005",
        "Notting Hill", "Love Actually", "Titanic", "Before Sunrise",
        "Call Me By Your Name", "The Fault in Our Stars", "Crazy Rich Asians",
        "To All the Boys Ive Loved Before", "Me Before You", "A Star Is Born 2018",
        "Silver Linings Playbook", "Eternal Sunshine of the Spotless Mind",
        "500 Days of Summer", "About Time 2013", "The Big Sick", "Brooklyn 2015",
        "Carol 2015", "Atonement", "One Day 2011", "Sleepless in Seattle",
        "Youve Got Mail",
    ],
}


def _ffmpeg_dir() -> str:
    """Directory holding an ffmpeg binary yt-dlp will actually find.

    imageio-ffmpeg ships the binary under a versioned name
    (ffmpeg-win-x86_64-v7.1.exe), but yt-dlp resolves it by basename and only
    accepts exactly `ffmpeg`/`ffmpeg.exe` -- so provision a correctly-named
    copy once, inside this repo, rather than requiring a system-wide install.
    """
    import shutil

    import imageio_ffmpeg

    bin_dir = Path(__file__).resolve().parent.parent / "storage" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "ffmpeg.exe"
    if not target.exists():
        shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), target)
    return str(bin_dir)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()


def load_done() -> set[str]:
    if not MANIFEST.exists():
        return set()
    with MANIFEST.open(newline="", encoding="utf-8") as fh:
        return {row["film"] for row in csv.DictReader(fh)}


def append_manifest(row: dict) -> None:
    exists = MANIFEST.exists()
    with MANIFEST.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["film", "genre", "file", "duration_sec", "source_title"])
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def download(genres: list[str], per_genre: int) -> None:
    import yt_dlp

    done = load_done()
    print(f"{len(done)} film(s) already in the manifest; those are skipped.\n")

    for genre in genres:
        films = FILMS[genre][:per_genre]
        genre_dir = OUT_ROOT / genre.lower()
        genre_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 74)
        print(f"{genre}  ({len(films)} target films)")
        print("=" * 74)

        for i, film in enumerate(films, 1):
            if film in done:
                print(f"  [{i:02d}/{len(films)}] SKIP (already have)  {film}")
                continue

            slug = slugify(film)
            outtmpl = str(genre_dir / f"{slug}.%(ext)s")
            opts = {
                "outtmpl": outtmpl,
                # YouTube serves video and audio as separate DASH streams, so the
                # first choice merges them (needs ffmpeg). The pipeline measures
                # audio energy and tempo, so an audio-less download is useless --
                # the fallbacks still guarantee an audio track.
                # H.264 first so the new corpus matches the codec of the existing
                # trailers -- compression differences can nudge optical-flow motion
                # values, and a norm should not encode a codec artefact. AV1 is a
                # verified-working fallback (OpenCV decodes it here).
                "format": (
                    "bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]/"
                    "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
                    "bestvideo[height<=720]+bestaudio/"
                    "best[ext=mp4]/best"
                ),
                "merge_output_format": "mp4",
                "ffmpeg_location": _ffmpeg_dir(),
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "noplaylist": True,
                # Reject anything outside theatrical-trailer length.
                "match_filter": yt_dlp.utils.match_filter_func(
                    f"duration > {MIN_DURATION_SEC} & duration < {MAX_DURATION_SEC}"
                ),
            }

            query = f"ytsearch3:{film} official trailer"
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(query, download=True)
                    entries = [e for e in (info or {}).get("entries", []) if e]
                    if not entries:
                        print(f"  [{i:02d}/{len(films)}] NO MATCH          {film}")
                        continue
                    entry = entries[0]
                    produced = next(genre_dir.glob(f"{slug}.*"), None)
                    if produced is None:
                        print(f"  [{i:02d}/{len(films)}] NO FILE           {film}")
                        continue
                    append_manifest({
                        "film": film,
                        "genre": genre,
                        "file": str(produced.relative_to(OUT_ROOT)).replace("\\", "/"),
                        "duration_sec": entry.get("duration", ""),
                        "source_title": entry.get("title", ""),
                    })
                    dur = entry.get("duration") or 0
                    print(f"  [{i:02d}/{len(films)}] OK  {dur:>4}s  {film}")
            except Exception as exc:
                print(f"  [{i:02d}/{len(films)}] FAILED  {film}  ({type(exc).__name__}: {str(exc)[:90]})")

        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genres", nargs="*", default=list(FILMS), help="Genres to collect (default: all four).")
    parser.add_argument("--per-genre", type=int, default=25, help="How many films per genre.")
    args = parser.parse_args()

    unknown = [g for g in args.genres if g not in FILMS]
    if unknown:
        print(f"Unknown genre(s): {unknown}. Available: {list(FILMS)}")
        sys.exit(1)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    download(args.genres, args.per_genre)
