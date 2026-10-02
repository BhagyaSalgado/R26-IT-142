"""Trailer Baseline Builder — Component 3.

Works out the "normal" for one trailer: across all of its scenes, what is the
average shot length, the average energy, how much they vary, and so on.

Why per-trailer rather than universal numbers: trailers legitimately differ. A
2-second shot is fast in a drama and unremarkable in an action film. Comparing
every trailer to one fixed table of "correct" values would flag whole genres as
broken. So every figure here is computed from this trailer's own scenes.

The limitation worth knowing: this makes the system self-referential. It can
say "this scene is unlike the rest of this trailer", but it cannot say "this
trailer is unlike a good trailer" -- if the whole film is cut badly, its own
average is badly cut too, and nothing stands out. That gap is exactly what
genre_norm.py adds, by supplying an outside reference to compare against.
"""
from __future__ import annotations

import math
from typing import Any

from app.schemas.recommendation_schema import DistributionStats, TrailerBaseline


def _compute_stats(values: list[float]) -> DistributionStats:
    """Summarise a list of numbers: its centre, its spread, and its extremes.

    Both mean and median are kept because they answer different questions.
    The mean is pulled around by one extreme value; the median is not. If a
    trailer holds a single 15-second title card, the mean shot length jumps
    while the median stays honest about the typical shot. Having both lets
    later code notice that gap instead of being fooled by it.
    """
    if not values:
        return DistributionStats()

    n = len(values)
    sorted_v = sorted(values)
    mean_v = sum(values) / n

    # Median = the middle value once sorted. With an even count there is no
    # single middle, so average the two either side of centre.
    if n % 2 == 1:
        median_v = sorted_v[n // 2]
    else:
        median_v = (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2.0

    # Quartiles: q1 is the value a quarter of the way through the sorted list,
    # q3 three quarters. The gap between them (iqr) covers the middle 50% of
    # scenes and is a spread measure that extremes cannot distort.
    def _percentile(sv: list[float], p: float) -> float:
        k = (len(sv) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sv[int(k)]
        return sv[f] * (c - k) + sv[c] * (k - f)

    q1 = _percentile(sorted_v, 0.25)
    q3 = _percentile(sorted_v, 0.75)
    iqr = q3 - q1

    # Standard deviation
    variance = sum((x - mean_v) ** 2 for x in values) / max(n - 1, 1)
    std_v = math.sqrt(variance)

    return DistributionStats(
        median=round(median_v, 4),
        mean=round(mean_v, 4),
        std=round(std_v, 4),
        q1=round(q1, 4),
        q3=round(q3, 4),
        iqr=round(iqr, 4),
        min_val=round(sorted_v[0], 4),
        max_val=round(sorted_v[-1], 4),
        values=[round(v, 4) for v in values],
    )


def _z_score(value: float, stats: DistributionStats) -> float:
    """Compute z-score relative to the trailer's own distribution."""
    if stats.std < 1e-6:
        return 0.0
    return (value - stats.mean) / stats.std


def _iqr_outlier_score(value: float, stats: DistributionStats, factor: float = 1.5) -> float:
    """How far outside the IQR fence a value is. 0 = within fence."""
    if stats.iqr < 1e-6:
        return 0.0
    lower = stats.q1 - factor * stats.iqr
    upper = stats.q3 + factor * stats.iqr
    if value < lower:
        return (lower - value) / stats.iqr
    if value > upper:
        return (value - upper) / stats.iqr
    return 0.0


def build_trailer_baseline(scene_rows: list[dict[str, Any]]) -> TrailerBaseline:
    """Build a statistical baseline from all scenes in this trailer.

    This baseline is used by the anomaly detector to find scenes that
    deviate significantly from the trailer's own patterns.
    """
    if not scene_rows:
        return TrailerBaseline()

    n = len(scene_rows)

    # Extract per-scene values
    durations: list[float] = []
    motions: list[float] = []
    energies: list[float] = []
    tempos: list[float] = []
    eis: list[float] = []
    pacing_curve: list[float] = []

    scene_type_weighted: dict[str, float] = {}
    audio_mood_counts: dict[str, int] = {}
    face_emotion_counts: dict[str, int] = {}

    for row in scene_rows:
        evidence = row["evidence"]
        durations.append(evidence.shot_duration)
        motions.append(evidence.motion)
        energies.append(evidence.audio_energy)
        tempos.append(evidence.tempo_bpm)
        eis.append(evidence.ei)

        # Combined energy for pacing curve (motion + audio + EI, equally weighted)
        combined = (evidence.motion + evidence.audio_energy + evidence.ei) / 3.0
        pacing_curve.append(round(combined, 4))

        # Confidence-weighted scene type distribution
        st = evidence.scene_type
        conf = getattr(evidence, "scene_type_confidence", 1.0) or 1.0
        scene_type_weighted[st] = scene_type_weighted.get(st, 0.0) + conf

        # Audio mood distribution
        mood = evidence.audio_mood
        audio_mood_counts[mood] = audio_mood_counts.get(mood, 0) + 1

        # Face emotion distribution
        emo = evidence.visual_emotion
        face_emotion_counts[emo] = face_emotion_counts.get(emo, 0) + 1

    # Normalize scene type distribution
    total_conf = sum(scene_type_weighted.values()) or 1.0
    scene_type_dist = {k: round(v / total_conf, 4) for k, v in scene_type_weighted.items()}

    # Normalize mood/emotion distributions
    audio_mood_dist = {k: round(v / n, 4) for k, v in audio_mood_counts.items()}
    face_emotion_dist = {k: round(v / n, 4) for k, v in face_emotion_counts.items()}

    # Escalation gradient: correlation between position and combined energy
    # Positive = trailer builds intensity over time
    escalation = _compute_escalation_gradient(pacing_curve)

    total_duration = sum(durations)

    return TrailerBaseline(
        total_scenes=n,
        total_duration=round(total_duration, 2),
        shot_duration=_compute_stats(durations),
        motion=_compute_stats(motions),
        audio_energy=_compute_stats(energies),
        tempo=_compute_stats(tempos),
        ei=_compute_stats(eis),
        scene_type_distribution=scene_type_dist,
        audio_mood_distribution=audio_mood_dist,
        face_emotion_distribution=face_emotion_dist,
        escalation_gradient=round(escalation, 4),
        pacing_curve=pacing_curve,
    )


def _compute_escalation_gradient(values: list[float]) -> float:
    """Compute a simple linear correlation between position index and value.

    Returns a value in [-1, 1]. Positive means the trailer builds intensity.
    """
    n = len(values)
    if n < 3:
        return 0.0

    # Simple Pearson correlation between index and value
    positions = list(range(n))
    mean_x = (n - 1) / 2.0
    mean_y = sum(values) / n

    cov_xy = sum((i - mean_x) * (v - mean_y) for i, v in zip(positions, values))
    var_x = sum((i - mean_x) ** 2 for i in positions)
    var_y = sum((v - mean_y) ** 2 for v in values)

    denom = math.sqrt(var_x * var_y)
    if denom < 1e-8:
        return 0.0

    return cov_xy / denom


def is_statistical_outlier(
    value: float,
    stats: DistributionStats,
    iqr_factor: float = 2.0,
    z_threshold: float = 2.0,
) -> tuple[bool, float]:
    """Check if a value is an outlier relative to the trailer's distribution.

    Returns (is_outlier, outlier_score).
    outlier_score > 0 means it's outside the fence.
    Uses BOTH IQR and z-score — flags only if at least one method flags it.
    """
    iqr_score = _iqr_outlier_score(value, stats, factor=iqr_factor)
    z = abs(_z_score(value, stats))

    is_out = iqr_score > 0 or z > z_threshold
    score = max(iqr_score, z / z_threshold if z_threshold > 0 else 0.0)

    return is_out, round(score, 4)
