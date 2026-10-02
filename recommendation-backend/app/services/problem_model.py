"""A trained model that names editorial problems in a trailer.

Why this exists
---------------
Every earlier detector in this project answered the question "which number in
this trailer is unusual?" and then wrote a sentence containing that number.
That produces findings phrased as comparisons -- "this shot is 2.3x the
trailer's median" -- which describe a measurement, not a problem an editor
can act on, and read the same on every film.

This module answers a different question: "which known editorial defect does
this stretch of the trailer look like?" The answer is a named class with a
confidence, produced by a supervised model, and the class is what drives the
recommendation. The numbers become supporting evidence rather than the point.

How it is supervised without a labelled dataset
-----------------------------------------------
No corpus exists of real trailers annotated by editors with their faults, and
one cannot be built before this project is due. So the labels come from
deliberate corruption: take the 99 professional trailers, apply a specific,
well-understood editorial defect to a window of each, and label that window
with the defect applied. The model learns to tell each defect apart from
professionally-cut material.

This is honest supervision, and it is NOT the circularity that made the old
recommendation_model.joblib worthless. That model was trained on labels
produced by the same heuristic it was meant to replace, so it could only ever
reproduce the heuristic. Here the labels come from real signal
transformations applied to real professional footage -- the model learns what
professionally-cut trailers look like, and what each specific defect does to
them.

Its limitation, stated plainly: it recognises the defects in PROBLEM_CLASSES.
A real problem that resembles none of them will not be found, and a class
prediction is a statement about resemblance, not proof of a fault.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "problem_model.joblib"

# How many consecutive scenes make up one judged window, and how far the
# window moves each step. Six scenes is long enough for a rhythm to exist and
# short enough that the timeframe it reports is still actionable.
WINDOW = 6
STRIDE = 3

# The defects the model is trained to recognise. Each is a real, named thing
# an editor would recognise and could act on -- not a metric going out of
# range. "clean" is the negative class: professionally-cut material.
PROBLEM_CLASSES = (
    "clean",
    "pacing_drag",       # shots held far longer than the cut can carry
    "over_cutting",      # cut so fast nothing registers
    "rhythm_monotony",   # every shot the same length; no rhythmic shape
    "energy_flatline",   # the section stops rising or falling; nothing develops
    "dead_air",          # the mix drops out under picture that needs it
    "front_loaded",      # peaks early then decays, spending the climax too soon
)

# What each class means, and what to do about it. This is per PROBLEM, not per
# metric and not per genre -- seven entries total, each an editorial action.
# The model decides which one applies; this only says what the class means.
PROBLEM_LANGUAGE: dict[str, dict[str, str]] = {
    "pacing_drag": {
        "label": "Pacing drag",
        "problem": "This stretch holds its shots far longer than the surrounding cut can carry, and the sequence stops moving.",
        "fix": "Lift the two or three longest holds here and let the sequence run at the rhythm the rest of the trailer establishes. If a hold is deliberate, give it a reason on screen — a reveal, a reaction, a line landing.",
    },
    "over_cutting": {
        "label": "Over-cutting",
        "problem": "Shots here change faster than the eye can read them, so individual images stop registering.",
        "fix": "Hold the strongest two or three frames in this run long enough to be seen and drop the rest — a montage reads by its best images, not its count.",
    },
    "rhythm_monotony": {
        "label": "Rhythmic monotony",
        "problem": "Every shot in this stretch runs to almost the same length, so the cutting has no rhythmic shape.",
        "fix": "Vary the shot lengths — let a couple breathe and clip the others tight. A trailer's pace is felt through contrast between shots, not through their average.",
    },
    "energy_flatline": {
        "label": "Energy flatline",
        "problem": "The section neither builds nor releases — its intensity, audio and movement all hold level, so nothing develops across it.",
        "fix": "Give this stretch a direction: either build it toward the next beat or deliberately drop it so the following section can lift. A flat middle is where an audience disengages.",
    },
    "dead_air": {
        "label": "Dead air under picture",
        "problem": "The mix falls away here while the picture continues, leaving the images unsupported.",
        "fix": "Carry the score or a sound bed through this stretch. If the silence is deliberate, make it land on a cut so it reads as a held beat rather than a dropout.",
    },
    "front_loaded": {
        "label": "Front-loaded intensity",
        "problem": "This stretch peaks early and decays, spending its strongest material before the section has built to it.",
        "fix": "Move the strongest beat later and lead in with the quieter material, so the section arrives somewhere instead of starting at its ceiling.",
    },
}

# The per-scene signals read out of the emotion-analysis output. These are the
# only inputs; nothing here reads the video again.
_SIGNALS = ("shot_duration", "ei", "audio_energy", "motion")


@dataclass
class ProblemPrediction:
    """One window the model has judged."""
    start_idx: int
    end_idx: int
    problem: str
    confidence: float
    class_probabilities: dict[str, float]
    drivers: dict[str, float]


def _series(scene_rows: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    """Pull the per-scene signal series out of the analysis rows."""
    out: dict[str, np.ndarray] = {}
    for name in _SIGNALS:
        vals = []
        for row in scene_rows:
            ev = row.get("evidence")
            v = getattr(ev, name, None) if ev is not None else None
            vals.append(float(v) if isinstance(v, (int, float)) else 0.0)
        out[name] = np.asarray(vals, dtype=float)
    return out


def _slope(values: np.ndarray) -> float:
    """Trend across the window, scaled so it is comparable between signals."""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    scale = float(np.mean(np.abs(values))) or 1.0
    return float(np.polyfit(x, values, 1)[0] / scale)


def window_features(series: dict[str, np.ndarray], lo: int, hi: int) -> np.ndarray:
    """Describe one window by its SHAPE, not by its absolute levels.

    Every feature is either dimensionless (a coefficient of variation, a
    ratio, a normalised slope) or expressed relative to the same trailer, so
    a quiet film and a loud one with the same defect land in the same place.
    That is what lets the model learn the defect rather than the film.
    """
    feats: list[float] = []
    n = len(next(iter(series.values())))

    for name in _SIGNALS:
        v = series[name]
        w = v[lo:hi]
        trailer_mean = float(np.mean(v)) or 1e-6
        w_mean = float(np.mean(w))
        w_std = float(np.std(w))

        feats.extend([
            w_mean / trailer_mean,               # level, relative to this trailer
            w_std / (abs(w_mean) or 1e-6),       # variation within the window
            _slope(w),                           # is it going anywhere
            float(np.max(w)) / (abs(w_mean) or 1e-6),   # peakiness
            float(np.min(w)) / (abs(w_mean) or 1e-6),   # troughs
        ])

        # Where the window's own peak sits: early-peaking is what separates
        # front-loading from a section that builds.
        if len(w) > 1 and float(np.ptp(w)) > 1e-9:
            feats.append(float(np.argmax(w)) / (len(w) - 1))
        else:
            feats.append(0.5)

    # Consecutive-shot length ratios: the direct signature of monotony
    # (all ratios ~1) versus a shaped cut (ratios spread).
    sd = series["shot_duration"][lo:hi]
    if len(sd) > 1:
        ratios = sd[1:] / np.maximum(sd[:-1], 1e-6)
        feats.extend([float(np.mean(ratios)), float(np.std(ratios))])
    else:
        feats.extend([1.0, 0.0])

    # Position of the window in the trailer. A flatline in the middle and one
    # at the very end are not equally wrong.
    feats.append((lo + hi) / 2.0 / max(n, 1))
    return np.asarray(feats, dtype=float)


def feature_names() -> list[str]:
    names: list[str] = []
    for s in _SIGNALS:
        names += [f"{s}_level", f"{s}_cv", f"{s}_slope", f"{s}_peak",
                  f"{s}_trough", f"{s}_peak_pos"]
    names += ["shot_ratio_mean", "shot_ratio_std", "window_position"]
    return names


def windows_for(n_scenes: int) -> list[tuple[int, int]]:
    """Window bounds covering a trailer of this length."""
    if n_scenes < WINDOW:
        return [(0, n_scenes)] if n_scenes >= 3 else []
    spans = [(lo, lo + WINDOW) for lo in range(0, n_scenes - WINDOW + 1, STRIDE)]
    if spans and spans[-1][1] < n_scenes:
        spans.append((n_scenes - WINDOW, n_scenes))
    return spans


_cache: dict[str, Any] = {}


def load_model() -> Any | None:
    """The trained bundle, or None when it has not been trained yet."""
    if "bundle" in _cache:
        return _cache["bundle"]
    bundle = None
    if MODEL_PATH.exists():
        try:
            import joblib
            bundle = joblib.load(MODEL_PATH)
        except Exception as exc:
            logger.warning("Could not load problem model: %s", exc)
    else:
        logger.info("No problem model at %s — run scripts/train_problem_model.py.", MODEL_PATH)
    _cache["bundle"] = bundle
    return bundle


def _merge_overlapping(preds: list[ProblemPrediction]) -> list[ProblemPrediction]:
    """Collapse overlapping windows that report the same problem.

    Windows slide by STRIDE, so one long defective stretch is caught by
    several of them and would otherwise be reported three or four times. The
    merged finding spans the whole stretch, which is the honest timeframe --
    the fault is the run, not one window's slice of it -- and keeps the
    highest confidence seen across the run.
    """
    if not preds:
        return preds
    by_class: dict[str, list[ProblemPrediction]] = {}
    for p in preds:
        by_class.setdefault(p.problem, []).append(p)

    merged: list[ProblemPrediction] = []
    for group in by_class.values():
        group.sort(key=lambda p: p.start_idx)
        run = [group[0]]
        for p in group[1:]:
            if p.start_idx <= run[-1].end_idx + 1:  # overlapping or adjacent
                run.append(p)
                continue
            merged.append(_collapse(run))
            run = [p]
        merged.append(_collapse(run))
    merged.sort(key=lambda p: p.start_idx)
    return merged


def _collapse(run: list[ProblemPrediction]) -> ProblemPrediction:
    if len(run) == 1:
        return run[0]
    peak = max(run, key=lambda p: p.confidence)
    return ProblemPrediction(
        start_idx=min(p.start_idx for p in run),
        end_idx=max(p.end_idx for p in run),
        problem=peak.problem,
        confidence=peak.confidence,
        class_probabilities=peak.class_probabilities,
        drivers=peak.drivers,
    )


def predict_problems(
    scene_rows: list[dict[str, Any]], min_confidence: float = 0.55
) -> tuple[list[ProblemPrediction], dict[str, Any]]:
    """Name the editorial problems this trailer's own signals show.

    Returns (predictions, meta). Windows the model calls "clean" are dropped:
    a trailer with nothing wrong should produce nothing, which the earlier
    outlier-based detectors could never do because something is always the
    most unusual thing in any trailer.
    """
    bundle = load_model()
    if bundle is None:
        return [], {"model_available": False,
                    "note": "Problem model not trained yet — run scripts/train_problem_model.py."}

    clf = bundle["classifier"]
    scaler = bundle.get("scaler")
    classes = list(clf.classes_)
    series = _series(scene_rows)
    spans = windows_for(len(scene_rows))
    if not spans:
        return [], {"model_available": True, "note": "Trailer too short to judge."}

    X = np.vstack([window_features(series, lo, hi) for lo, hi in spans])
    if scaler is not None:
        X = scaler.transform(X)
    probs = clf.predict_proba(X)

    importances = getattr(clf, "feature_importances_", None)
    names = feature_names()

    predictions: list[ProblemPrediction] = []
    for (lo, hi), row in zip(spans, probs):
        best = int(np.argmax(row))
        label = classes[best]
        conf = float(row[best])
        if label == "clean" or conf < min_confidence:
            continue
        # Which measured features carried the most weight for this call --
        # reported so the finding can show what the model actually keyed on.
        drivers: dict[str, float] = {}
        if importances is not None:
            top = np.argsort(importances)[::-1][:3]
            drivers = {names[j]: round(float(importances[j]), 4) for j in top}
        predictions.append(ProblemPrediction(
            start_idx=lo, end_idx=hi - 1, problem=label, confidence=round(conf, 4),
            class_probabilities={c: round(float(p), 4) for c, p in zip(classes, row)},
            drivers=drivers,
        ))

    predictions = _merge_overlapping(predictions)

    meta = {
        "model_available": True,
        "windows_judged": len(spans),
        "problems_found": len(predictions),
        "trained_on": bundle.get("trained_on"),
        "cv_accuracy": bundle.get("cv_accuracy"),
        "classes": classes,
    }
    return predictions, meta
