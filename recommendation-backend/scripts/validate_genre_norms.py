"""Tests whether the learned genre norms actually carry information.

This is the make-or-break check for the whole norm-based approach. If the
genres do not measurably differ from each other, then "compare this trailer
to its genre norm" is meaningless and the method should be abandoned -- so it
is worth running before anything is built on top of the norms.

Two independent tests:

  1. SEPARATION. For each measurement and each point in the trailer, how far
     apart are two genres' averages, expressed in units of their own spread
     (a standardised mean difference / Cohen's d)? Around 0.8 is conventionally
     a "large" effect. This says WHERE the genres differ.

  2. CLASSIFICATION. Train a real classifier on the trailer profiles and see
     whether it can predict the genre of trailers it has never seen, scored by
     cross-validation. This is the honest test: if genre is not recoverable
     from these features, accuracy collapses to chance.

Test 2 doubles as a genuine trained model with a reportable accuracy figure.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.services.genre_norm import CURVE_DIMS, DEFAULT_BINS, trailer_profile

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "storage" / "genre_corpus"
MIN_PER_GENRE = 10   # below this a cross-validated score is too noisy to trust


def load_profiles() -> tuple[np.ndarray, list[str], list[str]]:
    """Flatten every corpus trailer into one feature vector + its genre label."""
    rows = list(csv.DictReader((CORPUS / "corpus_manifest.csv").open(newline="", encoding="utf-8")))
    X, y, films = [], [], []
    for r in rows:
        csv_path = CORPUS / r["corpus_dir"] / "final_system_output.csv"
        if not csv_path.exists():
            continue
        prof = trailer_profile(csv_path, DEFAULT_BINS)
        if prof is None:
            continue
        # One long vector: every dimension's curve laid end to end, plus the
        # whole-trailer scalars (duration, climax position, escalation, shots).
        vec = np.concatenate([prof[d] for d in CURVE_DIMS] + [prof["_scalar"]])
        X.append(vec)
        y.append(r["genre"])
        films.append(r["film"])
    return np.array(X), y, films


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Difference between two groups' means, in units of their pooled spread."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0
    pooled = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2) / (na + nb - 2))
    return float((a.mean() - b.mean()) / pooled) if pooled > 1e-9 else 0.0


def main() -> None:
    X, y, films = load_profiles()
    counts = Counter(y)
    print("=" * 74)
    print(f"VALIDATING GENRE NORMS  —  {len(X)} trailers")
    print("=" * 74)
    print("per genre:", dict(counts))

    usable = [g for g, n in counts.items() if n >= MIN_PER_GENRE]
    if len(usable) < 2:
        print(f"\nNeed >= 2 genres with >= {MIN_PER_GENRE} trailers to test. Waiting on more data.")
        return
    print(f"testing genres with >= {MIN_PER_GENRE} trailers: {usable}\n")

    mask = [i for i, g in enumerate(y) if g in usable]
    Xu = X[mask]
    yu = [y[i] for i in mask]

    # ---- TEST 1: where do the genres actually differ? -------------------
    print("-" * 74)
    print("TEST 1 — SEPARATION  (Cohen's d; |d|>0.8 = large, >0.5 = medium)")
    print("-" * 74)
    n_bins = DEFAULT_BINS
    for gi in range(len(usable)):
        for gj in range(gi + 1, len(usable)):
            ga, gb = usable[gi], usable[gj]
            A = Xu[[i for i, g in enumerate(yu) if g == ga]]
            B = Xu[[i for i, g in enumerate(yu) if g == gb]]
            print(f"\n  {ga} vs {gb}:")
            for di, dim in enumerate(CURVE_DIMS):
                seg = slice(di * n_bins, (di + 1) * n_bins)
                ds = np.array([cohens_d(A[:, seg][:, b], B[:, seg][:, b]) for b in range(n_bins)])
                strongest = int(np.argmax(np.abs(ds)))
                big = int((np.abs(ds) > 0.8).sum())
                print(f"    {dim:14s} strongest d={ds[strongest]:+5.2f} at {strongest/n_bins:.0%} through"
                      f"   ({big}/{n_bins} points show a large difference)")

    # ---- TEST 2: can a model actually tell them apart? ------------------
    print("\n" + "-" * 74)
    print("TEST 2 — CLASSIFICATION  (5-fold cross-validation on unseen trailers)")
    print("-" * 74)
    chance = max(Counter(yu).values()) / len(yu)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        "always-guess-majority (baseline)": DummyClassifier(strategy="most_frequent"),
        "LogisticRegression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.5)),
        "RandomForest": RandomForestClassifier(n_estimators=400, random_state=42),
    }
    results = {}
    for name, model in models.items():
        scores = cross_val_score(model, Xu, yu, cv=cv, scoring="accuracy")
        results[name] = scores.mean()
        print(f"  {name:34s} {scores.mean():.1%}  (+/- {scores.std():.1%})")

    best = max(v for k, v in results.items() if "baseline" not in k)
    print(f"\n  chance level (always guess the biggest genre): {chance:.1%}")
    print(f"  best model:                                     {best:.1%}")

    print("\n" + "=" * 74)
    if best >= chance + 0.20:
        print("VERDICT: genres ARE clearly distinguishable from trailer structure alone.")
        print("         The norm-based approach is sound — deviations from a genre")
        print("         norm mean something, because the genres genuinely differ.")
    elif best >= chance + 0.10:
        print("VERDICT: genres are WEAKLY distinguishable. The approach can work but")
        print("         the signal is modest — report this honestly and prefer more")
        print("         trailers per genre before relying on it.")
    else:
        print("VERDICT: genres are NOT distinguishable from these features. The")
        print("         norm-based premise does NOT hold — do not build on it.")
    print("=" * 74)


if __name__ == "__main__":
    main()
