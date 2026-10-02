"""Scene Ratio Analyzer — Component 8 (Rewritten).

Reports the actual confidence-weighted scene-type distribution.
Does NOT compare against hardcoded "expected" genre ratios.
Only flags extreme imbalances as noteworthy observations (not problems).
"""
from __future__ import annotations

from typing import Any


def analyze_ratios(scene_rows: list[dict[str, Any]], dominant_genre: str) -> dict[str, Any]:
    """Analyze scene-type distribution with confidence weighting.

    Returns actual distribution and flags only extreme imbalances
    (e.g., a single scene type dominating 90%+ of the trailer).
    """
    n = max(len(scene_rows), 1)

    # Confidence-weighted scene type counts
    weighted_counts: dict[str, float] = {}
    raw_counts: dict[str, int] = {}

    for row in scene_rows:
        evidence = row["evidence"]
        st = evidence.scene_type
        conf = getattr(evidence, "scene_type_confidence", 1.0) or 1.0

        weighted_counts[st] = weighted_counts.get(st, 0.0) + conf
        raw_counts[st] = raw_counts.get(st, 0) + 1

    # Normalize weighted distribution
    total_weight = sum(weighted_counts.values()) or 1.0
    weighted_distribution = {k: round(v / total_weight, 4) for k, v in weighted_counts.items()}

    # Raw distribution
    raw_distribution = {k: round(v / n, 4) for k, v in raw_counts.items()}

    # Diversity score: how many different scene types appear?
    unique_types = len([k for k, v in raw_counts.items() if v > 0])
    diversity_score = min(1.0, unique_types / max(5, n * 0.3))

    # Flag extreme imbalances only
    observations: list[str] = []
    is_balanced = True

    max_type_pct = max(weighted_distribution.values()) if weighted_distribution else 0.0
    max_type_name = max(weighted_distribution, key=weighted_distribution.get) if weighted_distribution else "Unknown"

    if max_type_pct > 0.85 and n >= 5:
        observations.append(
            f"Scene type '{max_type_name}' dominates {max_type_pct:.0%} of the trailer. "
            f"This may indicate limited variety, but could be intentional depending on the genre."
        )
        is_balanced = False

    if unique_types == 1 and n >= 5:
        observations.append(
            f"Only one scene type detected ('{max_type_name}'). Consider whether "
            f"the scene classifier is accurately capturing variety in this trailer."
        )
        is_balanced = False

    return {
        "weighted_distribution": weighted_distribution,
        "raw_distribution": raw_distribution,
        "raw_counts": raw_counts,
        "unique_scene_types": unique_types,
        "diversity_score": round(diversity_score, 4),
        "is_balanced": is_balanced,
        "observations": observations,
        "dominant_genre": dominant_genre,
    }
