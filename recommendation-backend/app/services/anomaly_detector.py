"""Real, unsupervised ML anomaly detection for trailer scenes.

Replaces the old approach of hand-picked univariate thresholds (e.g. "flag
if energy drop > 0.25", "flag if audio/visual gap > 0.45") with an
IsolationForest — a real, standard scikit-learn model — fit fresh on each
trailer's own real per-scene feature vectors. No labels are needed (it's
unsupervised), no synthetic data is used (every row is this trailer's own
real measured evidence), and no fixed magic-number cutoffs are hand-picked:
IsolationForest's `contamination="auto"` threshold is derived from the
model's own score distribution for this specific trailer, not a constant
tuned by a person.

This only decides WHICH scenes are anomalous. Turning "scene 7 is
anomalous" into readable English (what kind of anomaly, which genre-aware
fix to suggest) still needs some interpretation — see `explain_anomaly` —
but the decision of whether something is unusual enough to flag comes
entirely from the model.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MIN_SCENES_FOR_ML = 6  # below this, there isn't enough real data for a model to learn trailer-specific structure

# emotion_confidence is a classifier-reliability signal, not a creative/
# editorial dimension — a scene can't be "fixed" for having low emotion
# classifier confidence, so it's never selected as the *explaining* feature
# even though it still contributes to the model's overall anomaly score.
_NOT_EXPLAINABLE = {"emotion_confidence"}


def _combined_energy(ev: Any) -> float:
    """One "how much is going on" number for a scene: movement and sound averaged."""
    return (ev.motion + ev.audio_energy) / 2.0


def _build_feature_matrix(scene_rows: list[dict[str, Any]]) -> tuple[np.ndarray, list[str]]:
    """Turn the scene list into a table of numbers the model can read.

    One row per scene, ten columns per row. Seven columns are measurements of
    the scene itself; the last three describe how it *relates to its
    neighbours*, which is what lets the model notice a jarring cut rather than
    just an unusual scene in isolation.
    """
    n = len(scene_rows)
    feature_names = [
        # --- measured directly from this scene ---
        "ei",                 # overall emotional intensity, 0-1
        "audio_energy",       # how loud/full the sound is, 0-1
        "motion",             # how much movement on screen, 0-1
        "object_score",       # how much recognisable "stuff" is in frame, 0-1
        "emotion_confidence", # how sure the face model was, 0-1
        "shot_duration",      # how long the shot lasts, seconds
        "tempo_bpm",          # music speed, beats per minute
        # --- describing this scene relative to its neighbours ---
        "audio_motion_gap",   # sound and picture disagreeing (loud but still, or busy but silent)
        "energy_delta_prev",  # energy jump coming into this scene
        "energy_delta_next",  # energy jump leaving this scene
    ]
    rows: list[list[float]] = []
    for i, row in enumerate(scene_rows):
        ev = row["evidence"]
        curr_energy = _combined_energy(ev)
        # At the very first and very last scene there is no neighbour, so we
        # compare the scene to itself. That yields a delta of 0 — "no jump" —
        # which is the honest answer, rather than inventing a fake neighbour.
        prev_energy = _combined_energy(scene_rows[i - 1]["evidence"]) if i > 0 else curr_energy
        next_energy = _combined_energy(scene_rows[i + 1]["evidence"]) if i < n - 1 else curr_energy

        rows.append([
            ev.ei, ev.audio_energy, ev.motion, ev.object_score, ev.emotion_confidence,
            ev.shot_duration, ev.tempo_bpm, abs(ev.motion - ev.audio_energy),
            curr_energy - prev_energy, curr_energy - next_energy,
        ])
    return np.array(rows), feature_names


def detect_scene_anomalies(scene_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fit a real IsolationForest on this trailer's own real scene data.

    Returns one entry per scene with: is_anomaly, anomaly_score (0-1, higher
    = more unusual), and dominant_feature (which real measurement deviates
    most from this trailer's own mean, for routing to a problem category).
    Empty list if there isn't enough real data to model (< MIN_SCENES_FOR_ML).
    """
    n = len(scene_rows)
    if n < MIN_SCENES_FOR_ML:
        return []

    # STEP 1 — build the table of numbers (one row per scene).
    X, feature_names = _build_feature_matrix(scene_rows)

    # STEP 2 — put every column on the same scale.
    # Without this, tempo_bpm (values around 120) would drown out motion
    # (values around 0.4) simply because its numbers are bigger. Scaling
    # rewrites each column as "how many standard deviations from this
    # trailer's own average", so all ten features get an equal vote.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # STEP 3 — fit the model on THIS trailer only.
    # IsolationForest works by repeatedly splitting the data at random; points
    # that get isolated after only a few splits are the unusual ones. It needs
    # no labels — nobody tells it which scenes are bad — and it is refitted
    # from scratch for every trailer, so "unusual" always means unusual for
    # this specific film. random_state=42 just makes runs reproducible.
    model = IsolationForest(
        n_estimators=200, contamination="auto", random_state=42,
    )
    model.fit(X_scaled)
    raw_scores = model.decision_function(X_scaled)  # higher = more normal
    predictions = model.predict(X_scaled)  # -1 = anomaly, 1 = normal

    # STEP 4 — rescale the model's raw scores to a readable 0-1 range.
    # IsolationForest's own output is an arbitrary number that means nothing
    # to a reader. Stretching it between this trailer's own best and worst
    # score gives "0 = most normal scene here, 1 = most unusual scene here".
    # The max(..., 1e-6) guards against dividing by zero if every scene
    # happens to score identically.
    score_min, score_max = raw_scores.min(), raw_scores.max()
    score_range = max(score_max - score_min, 1e-6)

    # STEP 5 — package one result per scene, and work out WHY each is unusual.
    results: list[dict[str, Any]] = []
    for i in range(n):
        unusualness = float((score_max - raw_scores[i]) / score_range)
        # Which real feature deviates most from this trailer's own mean —
        # explains *why*, doesn't decide *whether* (that's the model above).
        # emotion_confidence is excluded from being the explanation (see
        # _NOT_EXPLAINABLE) even though it still shapes the anomaly score.
        signed_z = X_scaled[i]
        ranked = np.argsort(-np.abs(signed_z))
        dominant_idx = next(
            (int(idx) for idx in ranked if feature_names[idx] not in _NOT_EXPLAINABLE),
            int(ranked[0]),
        )
        results.append({
            "scene_idx": i,
            "is_anomaly": bool(predictions[i] == -1),
            "anomaly_score": round(unusualness, 4),
            "dominant_feature": feature_names[dominant_idx],
            "dominant_z": round(float(signed_z[dominant_idx]), 4),
            "feature_values": dict(zip(feature_names, X[i].tolist())),
        })
    return results
