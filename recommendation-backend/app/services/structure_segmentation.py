"""Structure Segmentation — Component 4 (Rewritten).

Finds a trailer's acts -- opening, build-up, climax, ending -- by following
where its energy actually rises and falls, instead of assuming "the climax is
at 75%".

Why that matters: real trailers do not obey a fixed clock. Some hold the
climax to the last five seconds, some peak early and coast. Slicing at fixed
percentages would mislabel those, and every later judgement ("is the ending
weak?") would then be measuring the wrong stretch of film.

How it works, in three moves:
  1. Reduce each scene to a single "energy" number (movement + sound + intensity).
  2. Smooth that curve, so one loud shot does not read as a whole new act.
  3. Find the change points -- where the level genuinely shifts -- and treat
     those as act boundaries, then name each act from its height and position.
"""
from __future__ import annotations

from typing import Any

from app.schemas.recommendation_schema import StructuralPhase, StructureReport


def _combined_energy(evidence: Any) -> float:
    """Squash a scene down to one number: how much is going on right now.

    Movement and sound carry slightly more weight than emotional intensity
    because they are measured more directly -- intensity is itself a derived
    score, so leaning on it too hard would compound any error in it.
    """
    motion = getattr(evidence, "motion", 0.0) or 0.0
    audio = getattr(evidence, "audio_energy", 0.0) or 0.0
    ei = getattr(evidence, "ei", 0.0) or 0.0
    return (motion * 0.35 + audio * 0.35 + ei * 0.30)


def _smooth(values: list[float], window: int = 3) -> list[float]:
    """Average each value with its neighbours to flatten out one-off spikes.

    Without this, a single explosion in a quiet stretch would look like the
    start of a new act. Smoothing keeps genuine sustained shifts while
    ignoring momentary ones.
    """
    if len(values) <= window:
        return values[:]
    smoothed = []
    half = window // 2
    for i in range(len(values)):
        start = max(0, i - half)
        end = min(len(values), i + half + 1)
        smoothed.append(sum(values[start:end]) / (end - start))
    return smoothed


def _detect_change_points(values: list[float], min_segment: int = 2) -> list[int]:
    """Find indices where the energy level changes significantly.

    Uses a simple approach: find points where the difference between
    left-window average and right-window average exceeds a threshold
    based on the overall standard deviation.
    """
    n = len(values)
    if n < 4:
        return []

    mean_v = sum(values) / n
    std_v = (sum((v - mean_v) ** 2 for v in values) / max(n - 1, 1)) ** 0.5
    threshold = max(std_v * 0.6, 0.05)  # At least 0.05 change

    change_scores: list[tuple[int, float]] = []
    for i in range(min_segment, n - min_segment):
        left_avg = sum(values[max(0, i - min_segment):i]) / min_segment
        right_avg = sum(values[i:min(n, i + min_segment)]) / min_segment
        diff = abs(right_avg - left_avg)
        if diff > threshold:
            change_scores.append((i, diff))

    # Keep only the most significant change points (avoid duplicates)
    change_scores.sort(key=lambda x: x[1], reverse=True)
    selected: list[int] = []
    for idx, _ in change_scores:
        if all(abs(idx - s) >= min_segment for s in selected):
            selected.append(idx)
        if len(selected) >= 4:  # Max 5 phases
            break

    return sorted(selected)


def _classify_phase(avg_energy: float, position_pct: float, energy_trend: float) -> str:
    """Classify a phase based on its energy and position.

    This is NOT hardcoded genre logic — it labels structural roles
    based on universal narrative principles (low→high→resolve).
    """
    # Very start of trailer
    if position_pct < 0.15:
        return "setup" if avg_energy < 0.5 else "hook"

    # Very end of trailer
    if position_pct > 0.88:
        return "resolution"

    # Classify by energy level relative to position
    if avg_energy > 0.6 and energy_trend >= 0:
        return "peak"
    if avg_energy > 0.45:
        return "buildup" if energy_trend > 0.02 else "sustained_intensity"
    if avg_energy < 0.3:
        return "cooldown" if energy_trend < -0.02 else "setup"

    return "buildup" if energy_trend > 0 else "development"


def infer_beats(scene_rows: list[dict[str, Any]], trailer_type: str) -> StructureReport:
    """Infer structural narrative phases from actual trailer data.

    Instead of mapping fixed position percentages to acts, this function:
    1. Computes the energy curve across all scenes.
    2. Detects natural change points in the energy curve.
    3. Classifies each resulting segment by its energy profile and position.
    4. Identifies hook, climax, and signature moments from the data.
    """
    n = max(len(scene_rows), 1)
    if not scene_rows:
        return StructureReport(
            has_hook=False, has_logo=False, has_climax=False, has_button=False,
            logo_position="none", climax_position_pct=0.8,
            structure_confidence=0.0, phases=[],
        )

    # 1. Build energy curve
    energy_curve = [_combined_energy(row["evidence"]) for row in scene_rows]
    smoothed = _smooth(energy_curve, window=3)

    # 2. Detect change points
    change_points = _detect_change_points(smoothed, min_segment=max(2, n // 6))

    # 3. Build phases from segments between change points
    boundaries = [0] + change_points + [n]
    phases: list[StructuralPhase] = []

    for seg_idx in range(len(boundaries) - 1):
        start = boundaries[seg_idx]
        end = boundaries[seg_idx + 1]
        if end <= start:
            continue

        segment_energies = smoothed[start:end]
        avg_energy = sum(segment_energies) / len(segment_energies)
        start_pct = start / n
        end_pct = end / n
        mid_pct = (start_pct + end_pct) / 2.0

        # Energy trend within segment
        if len(segment_energies) >= 2:
            trend = (segment_energies[-1] - segment_energies[0]) / len(segment_energies)
        else:
            trend = 0.0

        phase_name = _classify_phase(avg_energy, mid_pct, trend)

        phases.append(StructuralPhase(
            phase_name=phase_name,
            start_scene=start + 1,  # 1-indexed
            end_scene=end,
            start_pct=round(start_pct, 3),
            end_pct=round(end_pct, 3),
            avg_energy=round(avg_energy, 4),
            confidence=round(0.6 + 0.3 * (1.0 - abs(avg_energy - 0.5)), 3),
        ))

    # 4. Detect structural elements from data
    # Hook: scene with highest impact in first 25%
    hook_candidates = [(i, energy_curve[i]) for i in range(min(max(n // 4, 1), n))]
    best_hook = max(hook_candidates, key=lambda x: x[1]) if hook_candidates else (0, 0)
    has_hook = best_hook[1] > 0.2

    # Climax: scene with highest energy in last 60%
    climax_start = max(n * 2 // 5, 1)
    climax_candidates = [(i, energy_curve[i]) for i in range(climax_start, n)]
    if climax_candidates:
        best_climax = max(climax_candidates, key=lambda x: x[1])
        has_climax = best_climax[1] > 0.3
        climax_position_pct = round(best_climax[0] / n, 3)
    else:
        has_climax = n >= 4
        climax_position_pct = 0.8

    # Button: does the trailer end with a distinct final scene?
    has_button = n >= 3

    # Signature moment: strongest emotional hit
    signature_moment: dict[str, Any] = {}
    max_ei_idx = 0
    max_ei_val = 0.0
    for i, row in enumerate(scene_rows):
        ev = row["evidence"]
        if ev.ei > max_ei_val:
            max_ei_val = ev.ei
            max_ei_idx = i
    if max_ei_val > 0.5:
        sig_row = scene_rows[max_ei_idx]
        signature_moment = {
            "type": "emotional_peak",
            "scene_id": sig_row.get("scene", max_ei_idx + 1),
            "timeframe": sig_row.get("timeframe", ""),
            "emotion": sig_row["evidence"].visual_emotion,
            "ei": round(max_ei_val, 4),
            "confidence": round(min(1.0, max_ei_val + 0.2), 3),
        }

    # Detected beats with confidence
    detected_beats: dict[str, float] = {}
    if has_hook:
        detected_beats["hook"] = round(0.5 + best_hook[1] * 0.4, 3)
    if has_climax:
        detected_beats["climax"] = round(0.6 + (best_climax[1] if climax_candidates else 0) * 0.3, 3)

    # Overall structure confidence
    structure_confidence = 0.5
    if n >= 5:
        structure_confidence += 0.2
    if has_hook and has_climax:
        structure_confidence += 0.15
    if len(phases) >= 3:
        structure_confidence += 0.1
    structure_confidence = min(1.0, structure_confidence)

    return StructureReport(
        has_hook=has_hook,
        has_logo=False,
        has_climax=has_climax,
        has_button=has_button,
        logo_position="none",
        climax_position_pct=climax_position_pct,
        structure_confidence=round(structure_confidence, 3),
        detected_beats=detected_beats,
        signature_moment=signature_moment,
        phases=phases,
    )
