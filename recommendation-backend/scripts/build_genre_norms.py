"""Builds a per-genre norm from the processed corpus and writes one
inspectable JSON per genre to artifacts/genre_norms/.

Run after process_genre_corpus.py. Reports honestly when a genre has too few
trailers to define a norm rather than emitting one that looks authoritative
and is really just three films averaged together.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.genre_norm import MIN_TRAILERS_FOR_NORM, build_norm

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "storage" / "genre_corpus"
CORPUS_MANIFEST = CORPUS / "corpus_manifest.csv"
NORMS_DIR = REPO_ROOT / "artifacts" / "genre_norms"


def main(bins: int) -> None:
    if not CORPUS_MANIFEST.exists():
        print(f"ERROR: no corpus manifest at {CORPUS_MANIFEST}. Run process_genre_corpus.py first.")
        sys.exit(1)

    with CORPUS_MANIFEST.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    by_genre: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_genre[r["genre"]].append(r)

    NORMS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 74)
    print(f"BUILDING GENRE NORMS from {len(rows)} processed trailers ({bins} bins)")
    print("=" * 74)

    for genre, entries in sorted(by_genre.items()):
        csvs, films = [], []
        for e in entries:
            p = CORPUS / e["corpus_dir"] / "final_system_output.csv"
            if p.exists():
                csvs.append(p)
                films.append(e["film"])

        norm = build_norm(genre, csvs, films, bins=bins)
        if norm is None:
            print(f"\n{genre}: no usable trailers — skipped")
            continue

        out = NORMS_DIR / f"{genre.lower()}.json"
        out.write_text(json.dumps(norm.to_json(), indent=2), encoding="utf-8")

        flag = "OK" if norm.reliable else f"THIN — under {MIN_TRAILERS_FOR_NORM}, treat as provisional"
        print(f"\n{genre}: {norm.n_trailers} trailers  [{flag}]")
        print(f"  -> {out.relative_to(REPO_ROOT)}")
        sd = norm.curves["shot_duration"]["mean"]
        print(f"  shot length across the trailer (s): "
              f"start {sd[0]:.2f} | mid {sd[len(sd)//2]:.2f} | end {sd[-1]:.2f}")
        for name in ("total_duration", "climax_position", "escalation_gradient"):
            s = norm.scalars.get(name, {})
            print(f"  {name:22s} mean {s.get('mean', 0):8.3f}  sd {s.get('std', 0):.3f}")

    print("\n" + "=" * 74)
    print(f"Wrote norms for {len(list(NORMS_DIR.glob('*.json')))} genre(s) -> {NORMS_DIR.relative_to(REPO_ROOT)}")
    print("=" * 74)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bins", type=int, default=20, help="Normalised-time bins per trailer.")
    args = p.parse_args()
    main(args.bins)
