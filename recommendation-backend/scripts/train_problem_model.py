"""Trains the editorial-problem classifier.

The idea in one line: we have 99 professionally-cut trailers and no list of
their faults, so instead of labelling faults we CREATE them -- take a
professional trailer, break one window of it in a specific, named way, and
label that window with the break. The model then learns what each defect does
to professionally-cut material.

Run:
    python scripts/train_problem_model.py

Writes artifacts/problem_model.joblib and prints honest cross-validated
accuracy plus a per-class breakdown, so the numbers can be quoted as measured
rather than claimed.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from app.services.problem_model import (  # noqa: E402
    MODEL_PATH,
    PROBLEM_CLASSES,
    WINDOW,
    feature_names,
    window_features,
    windows_for,
)

CORPUS = REPO / "storage" / "genre_corpus"
RNG = np.random.default_rng(20240829)  # fixed seed: the run is reproducible


def load_series(csv_path: Path) -> dict[str, np.ndarray] | None:
    """Read one trailer's per-scene signals out of the analysis CSV."""
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return None
    if len(rows) < WINDOW * 2:
        return None

    def col(name: str, default: float = 0.0) -> np.ndarray:
        out = []
        for r in rows:
            try:
                out.append(float(r.get(name, default) or default))
            except (TypeError, ValueError):
                out.append(default)
        return np.asarray(out, dtype=float)

    # Shot duration is not a column -- it is the length of each scene's own
    # timeframe, so derive it the same way the live service does.
    durations = []
    for r in rows:
        tf = str(r.get("time", ""))
        try:
            a, b = tf.split("-")

            def secs(t: str) -> float:
                m, s = t.split(":")
                return int(m) * 60 + float(s)

            durations.append(max(secs(b) - secs(a), 0.01))
        except Exception:
            durations.append(1.0)

    return {
        "shot_duration": np.asarray(durations, dtype=float),
        "ei": col("EI"),
        "audio_energy": col("A"),
        "motion": col("M"),
    }


# ── The degradations ──────────────────────────────────────────────────
# Each one is a specific editorial defect expressed as a transformation of the
# real signal series. They are applied to a window of a real trailer, so every
# training example is professional material with one known thing wrong.

def _corrupt(series: dict[str, np.ndarray], kind: str, lo: int, hi: int) -> dict[str, np.ndarray]:
    s = {k: v.copy() for k, v in series.items()}
    w = slice(lo, hi)

    if kind == "pacing_drag":
        s["shot_duration"][w] *= RNG.uniform(3.0, 6.0)

    elif kind == "over_cutting":
        s["shot_duration"][w] /= RNG.uniform(3.0, 6.0)

    elif kind == "rhythm_monotony":
        s["shot_duration"][w] = float(np.mean(s["shot_duration"][w]))

    elif kind == "energy_flatline":
        for k in ("ei", "audio_energy", "motion"):
            s[k][w] = float(np.mean(s[k][w]))

    elif kind == "dead_air":
        s["audio_energy"][w] *= RNG.uniform(0.0, 0.05)

    elif kind == "front_loaded":
        # Strongest material first, decaying: the section starts at its
        # ceiling instead of arriving there.
        for k in ("ei", "audio_energy"):
            s[k][w] = np.sort(s[k][w])[::-1]

    else:
        raise ValueError(f"unknown degradation {kind}")
    return s


def build_dataset() -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    csvs = sorted(CORPUS.glob("*/*/final_system_output.csv"))
    if not csvs:
        print(f"No corpus found under {CORPUS}", file=sys.stderr)
        sys.exit(1)

    X: list[np.ndarray] = []
    y: list[str] = []
    groups: list[str] = []
    used = 0
    defects = [c for c in PROBLEM_CLASSES if c != "clean"]

    for path in csvs:
        series = load_series(path)
        if series is None:
            continue
        used += 1
        n = len(series["shot_duration"])
        spans = windows_for(n)
        if len(spans) < 3:
            continue

        # Clean examples: the trailer as the professionals cut it.
        for lo, hi in spans:
            X.append(window_features(series, lo, hi))
            y.append("clean")
            groups.append(str(path.parent))

        # One corrupted example per defect per trailer, each in a randomly
        # chosen window, so a defect is never tied to one position.
        for kind in defects:
            lo, hi = spans[RNG.integers(0, len(spans))]
            X.append(window_features(_corrupt(series, kind, lo, hi), lo, hi))
            y.append(kind)
            groups.append(str(path.parent))

    return np.vstack(X), np.asarray(y), np.asarray(groups), used


def main() -> None:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report
    from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    import joblib

    print("=" * 74)
    print("TRAINING EDITORIAL-PROBLEM CLASSIFIER")
    print("=" * 74)

    X, y, groups, n_trailers = build_dataset()
    print(f"\ntrailers used : {n_trailers}")
    print(f"examples      : {len(y)}  ({X.shape[1]} features each)")
    counts = {c: int((y == c).sum()) for c in sorted(set(y))}
    print(f"class balance : {counts}")

    clf = RandomForestClassifier(
        n_estimators=300, max_depth=None, min_samples_leaf=2,
        class_weight="balanced", n_jobs=-1, random_state=0,
    )

    # Cross-validated predictions give an honest accuracy: every example is
    # scored by a model that never saw it.
    print("\ncross-validating (5-fold)...")
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0)
    validation_pipeline = make_pipeline(StandardScaler(), clf)
    pred = cross_val_predict(
        validation_pipeline,
        X,
        y,
        groups=groups,
        cv=cv,
        n_jobs=-1,
    )
    acc = float((pred == y).mean())

    print(f"\ncross-validated accuracy: {acc:.1%}  (chance = {1/len(set(y)):.1%})")
    print()
    print(classification_report(y, pred, digits=3, zero_division=0))

    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    clf.fit(Xs, y)
    names = feature_names()
    top = np.argsort(clf.feature_importances_)[::-1][:8]
    print("most informative features:")
    for j in top:
        print(f"  {names[j]:<24} {clf.feature_importances_[j]:.4f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "classifier": clf,
        "scaler": scaler,
        "feature_names": names,
        "trained_on": n_trailers,
        "cv_accuracy": round(acc, 4),
        "cv_strategy": "StratifiedGroupKFold grouped by trailer",
        "n_examples": int(len(y)),
    }, MODEL_PATH)
    print(f"\nsaved -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
