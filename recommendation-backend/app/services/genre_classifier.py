"""Genre Classifier — Component 2 (Rewritten).

Data-driven trailer genre classification that aggregates evidence from
all scenes, weighted by scene-type confidence.  Zero title-keyword matching.

The classifier uses:
  1. Scene-type distribution from the ML classifier (weighted by confidence)
  2. Audio mood distribution
  3. Face emotion distribution
  4. Motion and audio energy profiles
  5. Tempo profile

It does NOT:
  - Match keywords in the trailer title
  - Use hardcoded rules like "if weapon → Action"
  - Force every trailer into one category
"""
from __future__ import annotations

import math
from typing import Any

from app.schemas.recommendation_schema import GenreReport


# ── Genre mapping tables ───────────────────────────────────────────────────
#
# These define which scene-level signals are *evidence* for each genre.
# They are NOT rules — they are aggregation weights used to compute
# a probability distribution across genres.  The final genre is determined
# by the trailer-wide aggregated distribution, not any single scene.

# How much each ML scene_type contributes to each genre probability
_SCENE_TYPE_GENRE_WEIGHTS: dict[str, dict[str, float]] = {
    # scene_type → {genre: weight}
    # Action: rewarded heavily for raw kinetic scenes; slight Adventure & Thriller cross.
    "Action":    {"Action": 0.55, "Adventure": 0.15, "Thriller": 0.05},
    # Comedy: dominant happy-tone signal; tiny Romance cross.
    "Comedy":    {"Comedy": 0.55, "Romance": 0.05},
    # Romance: strong romantic scene signal; moderate Drama cross.
    "Romance":   {"Romance": 0.50, "Drama": 0.10},
    # Drama: core drama signal; small Romance & Mystery cross.
    "Drama":     {"Drama": 0.40, "Romance": 0.08, "Mystery": 0.05},
    # Dialogue: primarily Drama/Comedy/Romance; minor Mystery cross.
    "Dialogue":  {"Drama": 0.22, "Comedy": 0.10, "Romance": 0.10, "Mystery": 0.05},
    # Thriller: now contributes strongly to Horror (not just Thriller itself),
    # so a trailer full of Thriller scenes can tip into Horror when paired with fear.
    "Thriller":  {"Thriller": 0.35, "Horror": 0.25, "Action": 0.08},
    # Suspense: the second-strongest Horror signal after the dedicated Horror scene type.
    "Suspense":  {"Horror": 0.35, "Thriller": 0.25, "Mystery": 0.10},
    # Emotional: Drama/Romance.
    "Emotional": {"Drama": 0.30, "Romance": 0.25},
    # Adventure: kinetic but world-exploration flavour.
    "Adventure": {"Adventure": 0.50, "Action": 0.15},
    # Horror: strongest single Horror signal; small Thriller residual.
    "Horror":    {"Horror": 0.65, "Thriller": 0.10},
}

# How audio mood contributes (smaller weight — supporting signal)
_AUDIO_MOOD_GENRE_WEIGHTS: dict[str, dict[str, float]] = {
    # intense: high-energy → Action/Thriller
    "intense":   {"Action": 0.18, "Thriller": 0.08},
    # emotional: slow/melodic → Drama/Romance
    "emotional": {"Drama": 0.15, "Romance": 0.12},
    # calm: quiet atmosphere → Romance/Drama
    "calm":      {"Romance": 0.12, "Drama": 0.10},
    # suspense: ambiguous between Horror and Thriller — the dedicated
    # scene_type signal (Horror vs Thriller vs Suspense) is what should
    # decide between them; this supporting signal only leans Horror slightly.
    "suspense":  {"Horror": 0.16, "Thriller": 0.14, "Mystery": 0.08},
    # happy: upbeat → Comedy/Romance
    "happy":     {"Comedy": 0.15, "Romance": 0.08},
    # sad: melancholic → Drama/Romance
    "sad":       {"Drama": 0.15, "Romance": 0.05},
    # fear: rare audio tag, leans Horror but not overwhelmingly — a
    # Thriller trailer with mostly Thriller-typed scenes can still show fear.
    "fear":      {"Horror": 0.20, "Thriller": 0.10},
}

# How face emotion contributes (smallest weight — weakest signal)
_FACE_EMOTION_GENRE_WEIGHTS: dict[str, dict[str, float]] = {
    # happy: primary Comedy signal; moderate Romance cross.
    "happy":    {"Comedy": 0.12, "Romance": 0.06},
    # sad: Drama/Romance.
    "sad":      {"Drama": 0.12, "Romance": 0.04},
    # fear: the strongest face-emotion signal for Horror, but Thriller
    # protagonists show fear too — keep enough Thriller weight that a
    # scene_type-majority-Thriller trailer isn't tipped into Horror by
    # facial expression alone.
    "fear":     {"Horror": 0.14, "Thriller": 0.08},
    # angry: Action/Thriller conflict signal.
    "angry":    {"Action": 0.10, "Thriller": 0.06},
    # surprise: Horror shock-scare signal (jump-scare faces) + mild Comedy/Thriller.
    "surprise": {"Horror": 0.10, "Thriller": 0.06, "Comedy": 0.04},
    # disgust: supports Horror (body horror) and Drama.
    "disgust":  {"Horror": 0.08, "Drama": 0.05},
    "neutral":  {},  # No signal
}

ALL_GENRES = ["Action", "Adventure", "Comedy", "Drama", "Romance", "Thriller", "Horror",
              "Sci-Fi", "Fantasy", "Mystery", "Animation", "Family", "Documentary"]


def _softmax(scores: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    """Numerically stable softmax to convert raw scores to probabilities."""
    if not scores:
        return {}
    max_s = max(scores.values())
    exp_scores = {k: math.exp((v - max_s) / max(temperature, 0.01)) for k, v in scores.items()}
    total = sum(exp_scores.values()) or 1.0
    return {k: round(v / total, 4) for k, v in exp_scores.items()}


def build_genre_report(scene_rows: list[dict[str, Any]], trailer_title: str = "") -> GenreReport:
    """Build a data-driven genre classification from all scene evidence.

    Returns genre probabilities, primary/secondary genres, and confidence.
    """
    n = max(len(scene_rows), 1)
    raw_scores: dict[str, float] = {g: 0.0 for g in ALL_GENRES}

    # Small base prior so no genre is exactly zero
    for g in raw_scores:
        raw_scores[g] = 0.01

    # Per-scene genre curve for the response
    curve: list[dict[str, float]] = []

    total_motion = 0.0
    total_energy = 0.0
    total_tempo = 0.0
    total_confidence_sum = 0.0

    for i, row in enumerate(scene_rows):
        evidence = row["evidence"]
        scene_id = row.get("scene", i + 1)
        pos_pct = round(i / n, 3)

        st = (evidence.scene_type or "Drama")
        st_conf = getattr(evidence, "scene_type_confidence", 1.0) or 1.0
        classification_reliable = getattr(evidence, "classification_reliable", True)

        # Reduce weight of unreliable classifications
        effective_conf = st_conf if classification_reliable else st_conf * 0.3

        total_confidence_sum += effective_conf
        total_motion += evidence.motion
        total_energy += evidence.audio_energy
        total_tempo += evidence.tempo_bpm

        # 1. Scene-type evidence (strongest signal)
        scene_weights = _SCENE_TYPE_GENRE_WEIGHTS.get(st, {})
        for genre, weight in scene_weights.items():
            if genre in raw_scores:
                raw_scores[genre] += weight * effective_conf

        # 2. Audio mood evidence (supporting signal)
        mood = (evidence.audio_mood or "").lower()
        mood_weights = _AUDIO_MOOD_GENRE_WEIGHTS.get(mood, {})
        for genre, weight in mood_weights.items():
            if genre in raw_scores:
                raw_scores[genre] += weight

        # 3. Face emotion evidence (weakest signal)
        face_emo = (evidence.visual_emotion or "").lower()
        face_weights = _FACE_EMOTION_GENRE_WEIGHTS.get(face_emo, {})
        for genre, weight in face_weights.items():
            if genre in raw_scores:
                raw_scores[genre] += weight

        # Per-scene genre scores for the curve
        scene_scores = _softmax({
            **{g: 0.01 for g in ALL_GENRES},
            **{g: scene_weights.get(g, 0) * effective_conf + mood_weights.get(g, 0) + face_weights.get(g, 0)
               for g in set(list(scene_weights.keys()) + list(mood_weights.keys()) + list(face_weights.keys()))}
        })
        curve.append({"scene_id": scene_id, "position_pct": pos_pct, **scene_scores})

    # Normalize per-scene accumulated evidence by scene count n
    normalized_scores = {g: score / n for g, score in raw_scores.items()}

    # 4. Motion/energy profile as trailer-level genre evidence
    avg_motion = total_motion / n
    avg_energy = total_energy / n
    avg_tempo = total_tempo / n

    # High motion + high energy → strong Action/Adventure signal
    if avg_motion > 0.55 and avg_energy > 0.55:
        normalized_scores["Action"] += 0.22
        normalized_scores["Adventure"] += 0.10
    elif avg_motion > 0.6:
        normalized_scores["Action"] += 0.12

    # Low motion + low energy → Drama/Romance, quiet Thriller tension, *or*
    # Horror atmospheric dread. Distinguish using the scene-type evidence
    # already accumulated above, so a quiet-but-clearly-Thriller-typed
    # trailer doesn't get overridden by a flat Horror-leaning bonus.
    if avg_motion < 0.3 and avg_energy < 0.4:
        horror_raw = normalized_scores.get("Horror", 0.0)
        thriller_raw = normalized_scores.get("Thriller", 0.0)
        drama_raw  = normalized_scores.get("Drama",  0.0)
        romance_raw = normalized_scores.get("Romance", 0.0)
        if horror_raw >= thriller_raw and horror_raw > max(drama_raw, romance_raw):
            # Atmospheric, slow-burn Horror corridor — only when Horror
            # evidence is already at least on par with Thriller.
            normalized_scores["Horror"]  += 0.12
            normalized_scores["Thriller"] += 0.05
        elif thriller_raw > max(drama_raw, romance_raw):
            # Quiet, tense Thriller (dread without Horror-coded evidence).
            normalized_scores["Thriller"] += 0.10
        else:
            normalized_scores["Drama"]   += 0.10
            normalized_scores["Romance"] += 0.10

    # High tempo → weak evidence for Comedy/Action
    if avg_tempo > 130:
        normalized_scores["Action"] += 0.05
        normalized_scores["Comedy"] += 0.05

    # Mystery: suspense mood + Drama-heavy scene mix → Mystery signal
    thriller_raw = normalized_scores.get("Thriller", 0.0)
    mystery_raw  = normalized_scores.get("Mystery",  0.0)
    if thriller_raw > 0.15 and mystery_raw > 0.05:
        normalized_scores["Mystery"] += 0.08

    # Convert to probabilities using calibrated softmax temperature.
    # T=0.75 sharpens the dominant genre without fully collapsing secondary genres.
    # This was lowered from T=1.0 because the earlier flat weights produced
    # near-uniform distributions for distinctive genres like Horror.  Once
    # human-labeled ground truth is available (Step 2), calibrate T by
    # grid-searching against label agreement in genre_baselines.py (Step 3).
    genre_probabilities = _softmax(normalized_scores, temperature=0.75)

    # Sort by probability
    sorted_genres = sorted(genre_probabilities.items(), key=lambda x: x[1], reverse=True)

    primary_genre = sorted_genres[0][0]
    primary_prob = sorted_genres[0][1]

    # Secondary genres: anything with probability >= 15% of the primary genre's probability
    secondary_genres = [
        g for g, p in sorted_genres[1:]
        if p >= 0.10 and p >= primary_prob * 0.15
    ]

    # Legacy compatibility: single secondary_genre
    secondary_genre = secondary_genres[0] if secondary_genres else None

    # Genre confidence: directly reflects the predicted dominant genre's probability
    genre_confidence = round(primary_prob, 4)

    # Build mixture (legacy format)
    trailer_mixture = {g: p for g, p in genre_probabilities.items() if p > 0.01}

    return GenreReport(
        trailer_mixture=trailer_mixture,
        genre_curve=curve,
        dominant_genre=primary_genre,
        secondary_genre=secondary_genre,
        secondary_genres=secondary_genres,
        genre_confidence=genre_confidence,
        genre_probabilities=genre_probabilities,
    )
