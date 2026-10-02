"""Learns the magnitude-band cutoffs that finding_language.py uses to decide
whether a deviation is "marginal", "clear", or "extreme", instead of the
hand-picked constants (0.75 / 0.45) that used to sit there.

The problem this solves
------------------------
finding_language.compose() words a finding differently depending on how
unusual it is — a 0-1 "unusualness" score coming straight out of
anomaly_detector.py's IsolationForest. That score is min-max rescaled PER
TRAILER (0 = this trailer's most normal scene, 1 = this trailer's most
unusual scene), so it says nothing on its own about whether 0.75 is actually
rare. The old cutoffs were just numbers someone picked; nothing tied them to
what real professionally-cut trailers look like.

The approach
------------
Run the exact same anomaly detector used at request time
(app/services/anomaly_detector.py) over every trailer in the real corpus
(storage/genre_corpus, 99 professionally-cut trailers), and collect every
real scene's unusualness score. Because these are professionally-edited
films, that pooled distribution IS the real-world baseline for "how unusual
does a professionally-cut scene normally get" — so the cutoffs for "clear"
and "extreme" are read off real percentiles of it, not guessed.

Run:
    python scripts/build_magnitude_bands.py

Writes artifacts/magnitude_bands.json and prints the resulting thresholds
plus how many real trailers/scenes they were learned from.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from app.schemas.recommendation_schema import RecommendationRequest  # noqa: E402
from app.services.anomaly_detector import MIN_SCENES_FOR_ML, detect_scene_anomalies  # noqa: E402
from app.services.recommendation_service import _build_scene_rows  # noqa: E402

CORPUS = REPO / "storage" / "genre_corpus"
OUT_PATH = REPO / "artifacts" / "magnitude_bands.json"

# Where "clear" and "extreme" sit in the REAL distribution of unusualness
# scores drawn from professionally-cut material. Chosen as: the top ~10% of
# how unusual a professionally-cut scene gets is "extreme"; the next slice
# down (~35%-90%) is "clear"; everything below that is "marginal". These
# percentiles are a judgment call about how much of real professional cutting
# counts as "notably unusual" -- but the NUMBER each one resolves to is
# measured, not invented.
EXTREME_PERCENTILE = 90.0
CLEAR_PERCENTILE = 65.0


def load_scene_rows(csv_path: Path) -> list[dict] | None:
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return None
    if len(rows) < MIN_SCENES_FOR_ML:
        return None
    req = RecommendationRequest(final_system_output=rows)
    return _build_scene_rows(req)


def main() -> None:
    csvs = sorted(CORPUS.glob("*/*/final_system_output.csv"))
    if not csvs:
        print(f"No corpus found under {CORPUS}", file=sys.stderr)
        sys.exit(1)

    print("=" * 74)
    print(f"LEARNING MAGNITUDE BANDS from {len(csvs)} real professional trailers")
    print("=" * 74)

    all_scores: list[float] = []
    used = 0
    for path in csvs:
        scene_rows = load_scene_rows(path)
        if scene_rows is None:
            continue
        results = detect_scene_anomalies(scene_rows)
        if not results:
            continue
        used += 1
        all_scores.extend(r["anomaly_score"] for r in results)

    if not all_scores:
        print("No usable scenes found — nothing to learn from.", file=sys.stderr)
        sys.exit(1)

    scores = np.asarray(all_scores, dtype=float)
    extreme_cut = float(np.percentile(scores, EXTREME_PERCENTILE))
    clear_cut = float(np.percentile(scores, CLEAR_PERCENTILE))

    print(f"\ntrailers used : {used} / {len(csvs)}")
    print(f"real scenes   : {len(scores)}")
    print(f"\nunusualness distribution across real professional cutting:")
    for p in (50, 65, 75, 90, 95, 99):
        print(f"  p{p:<3d} = {np.percentile(scores, p):.4f}")
    print(f"\nlearned cutoffs:")
    print(f"  extreme (p{EXTREME_PERCENTILE:.0f}) = {extreme_cut:.4f}")
    print(f"  clear   (p{CLEAR_PERCENTILE:.0f}) = {clear_cut:.4f}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "extreme": round(extreme_cut, 4),
        "clear": round(clear_cut, 4),
        "marginal": 0.0,
        "trained_on_trailers": used,
        "trained_on_scenes": len(scores),
        "extreme_percentile": EXTREME_PERCENTILE,
        "clear_percentile": CLEAR_PERCENTILE,
    }, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
