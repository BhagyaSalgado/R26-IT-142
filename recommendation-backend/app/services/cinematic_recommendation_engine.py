"""Cinematic Recommendation Engine — Component 5 (Complete Rewrite).

Evidence-based, genre-aware, context-sensitive problem detection engine.

KEY PRINCIPLES:
  1. Only flag genuine problems with evidence.
  2. Use the trailer's own statistical baseline for anomaly detection.
  3. Genre changes interpretation, not rules.
  4. Respect scene_type_confidence — don't make strong recommendations
     from unreliable classifications.
  5. Context matters: position, neighbors, structural phase.
  6. If the trailer is working well, say so.
  7. Every recommendation has: WHAT, WHERE, WHY, HOW, and exact timestamps.
"""
from __future__ import annotations

import math
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from app.schemas.recommendation_schema import (
    CategoryType,
    ComponentScores,
    Evidence,
    Recommendation,
    SeverityLevel,
    StructureReport,
    TimelineInsight,
    TimingRoadmapItem,
    TrailerBaseline,
    TrailerProfile,
)
from app.services.anomaly_detector import detect_scene_anomalies
from app.services.finding_language import band_for, compose as compose_finding
from app.services.llm_fix_generator import generate_fix_text
from app.services.norm_deviation_detector import detect_norm_deviations
from app.services.problem_model import PROBLEM_LANGUAGE, predict_problems
from app.services.visual_integrity_detector import detect_visual_integrity

_FEATURE_DISPLAY_NAMES = {
    "ei": "emotional intensity",
    "audio_energy": "audio energy",
    "motion": "motion",
    "object_score": "visual impact",
    "emotion_confidence": "emotion clarity",
    "tempo_bpm": "musical tempo",
}


# ── Candidate problem: an intermediate object before filtering ─────────

class _ProblemCandidate:
    """Internal representation of a potential problem before severity scoring."""
    __slots__ = (
        "scene_idx", "scene_id", "timeframe", "start_time", "end_time",
        "problem", "why", "fix", "evidence_details", "category",
        "raw_confidence", "severity_score", "focus_area", "fix_source",
    )

    def __init__(
        self,
        scene_idx: int,
        scene_id: int,
        timeframe: str,
        start_time: float,
        end_time: float,
        problem: str,
        why: str,
        fix: str,
        evidence_details: dict[str, Any],
        category: CategoryType,
        raw_confidence: float,
        severity_score: float,
        focus_area: str,
        fix_source: str = "template",
    ):
        self.scene_idx = scene_idx
        self.scene_id = scene_id
        self.timeframe = timeframe
        self.start_time = start_time
        self.end_time = end_time
        self.problem = problem
        self.why = why
        self.fix = fix
        self.evidence_details = evidence_details
        self.category = category
        self.raw_confidence = raw_confidence
        self.severity_score = severity_score
        self.focus_area = focus_area
        self.fix_source = fix_source


def _parse_timeframe_seconds(timeframe: str) -> tuple[float, float]:
    """Parse 'MM:SS-MM:SS' into (start_seconds, end_seconds)."""
    try:
        parts = timeframe.split("-")
        def _to_sec(t: str) -> float:
            segs = [float(x) for x in t.strip().split(":")]
            s = 0.0
            for x in segs:
                s = s * 60 + x
            return s
        return _to_sec(parts[0]), _to_sec(parts[1])
    except Exception:
        return 0.0, 0.0


# ==============================================================================
# STEP 1: BASE PROBLEM SEVERITY & PRIORITY SCORE MAPPING
# Converts candidate anomaly severity score into discrete urgency categories:
# - HIGH (score >= 0.7)   -> Priority 1, Base Score: 85
# - MEDIUM (score >= 0.4) -> Priority 2, Base Score: 60
# - LOW (score < 0.4)    -> Priority 3, Base Score: 35
# ==============================================================================
def _severity_from_score(score: float) -> SeverityLevel:
    """Convert 0-1 severity score to HIGH/MEDIUM/LOW."""
    if score >= 0.7:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


def _priority_from_severity(severity: SeverityLevel) -> tuple[str, int, int]:
    """Map detected problem severity to base priority values (Label, Rank P1-P3, Base Score 0-100)."""
    if severity == "HIGH":
        return "High", 1, 85      # Urgent critical fix
    if severity == "MEDIUM":
        return "Medium", 2, 60    # Moderate edit recommendation
    return "Low", 3, 35           # Minor polish tweak


# NOTE: a hand-written per-genre fix vocabulary used to live here (12 genres
# x 6 fix categories of hand-authored prose), along with two functions that
# suppressed findings based on typed-in genre conventions. All of it has been
# removed. Genre-appropriateness is now measured rather than asserted: the
# learned norms in artifacts/genre_norms/ say what each genre actually does,
# so a long hold in a Horror trailer stops being flagged because real Horror
# trailers hold long shots -- not because someone wrote a rule saying so.
# See norm_deviation_detector.py.


# ── Technical problem detectors (deterministic) ───────────────────────

def _detect_technical_problems(
    scene_rows: list[dict[str, Any]],
) -> list[_ProblemCandidate]:
    """Detect objective technical problems that are always wrong."""
    problems: list[_ProblemCandidate] = []

    for i, row in enumerate(scene_rows):
        ev = row["evidence"]
        timeframe = row.get("timeframe", "")
        scene_id = row.get("scene", i + 1)
        start_t, end_t = _parse_timeframe_seconds(timeframe)

        # 1. Invalid timestamps (end <= start)
        if end_t <= start_t and timeframe:
            problems.append(_ProblemCandidate(
                scene_idx=i, scene_id=scene_id, timeframe=timeframe,
                start_time=start_t, end_time=end_t,
                problem=f"Invalid timestamp range: end ({end_t:.2f}s) <= start ({start_t:.2f}s).",
                why="Impossible timestamp ranges indicate data corruption or processing errors.",
                fix="Verify scene boundary detection output and re-run shot segmentation for this section.",
                evidence_details={"start_time": start_t, "end_time": end_t},
                category="Structure",
                raw_confidence=1.0,
                severity_score=0.9,
                focus_area="data integrity",
            ))

        # 2. Missing audio (energy ≈ 0)
        if ev.audio_energy < 0.01 and ev.shot_duration > 1.0:
            problems.append(_ProblemCandidate(
                scene_idx=i, scene_id=scene_id, timeframe=timeframe,
                start_time=start_t, end_time=end_t,
                problem=f"Near-zero audio energy ({ev.audio_energy:.4f}) in a {ev.shot_duration:.1f}s segment.",
                why="Complete audio silence in a trailer segment may indicate a missing audio track, muted section, or extraction error.",
                fix="Check whether this section has intentional silence (e.g., dramatic pause) or if the audio track was not properly extracted.",
                evidence_details={"audio_energy": ev.audio_energy, "shot_duration": ev.shot_duration},
                category="Audio",
                raw_confidence=0.95,
                severity_score=0.75,
                focus_area="audio integrity",
            ))

        # 3. Overlapping timestamps with previous scene
        if i > 0:
            prev_timeframe = scene_rows[i - 1].get("timeframe", "")
            _, prev_end = _parse_timeframe_seconds(prev_timeframe)
            if start_t < prev_end - 0.1:  # Allow 0.1s tolerance
                problems.append(_ProblemCandidate(
                    scene_idx=i, scene_id=scene_id, timeframe=timeframe,
                    start_time=start_t, end_time=end_t,
                    problem=f"Scene overlaps with previous scene (starts at {start_t:.2f}s, previous ends at {prev_end:.2f}s).",
                    why="Overlapping scene boundaries indicate a segmentation error that may cause duplicate analysis.",
                    fix="Re-examine shot boundary detection for this section.",
                    evidence_details={"scene_start": start_t, "prev_end": prev_end},
                    category="Structure",
                    raw_confidence=0.95,
                    severity_score=0.8,
                    focus_area="data integrity",
                ))

    return problems


# ── Statistical anomaly detectors (trailer-relative) ─────────────────

def _dominant_observed_value(dominant: str, ev: Any) -> float:
    """This scene's actual value for whichever feature the model flagged."""
    return float(getattr(ev, dominant, 0.0) or 0.0)


# Musical tempo below/above this is not a tempo — it is an octave error or a
# failed estimate. Real trailer scores sit well inside it.
_PLAUSIBLE_BPM = (40.0, 200.0)


def _is_scene_level_signal(dominant: str, baseline: TrailerBaseline) -> bool:
    """Does this feature actually vary shot to shot in THIS trailer?

    Tempo is estimated once per track, so the same BPM is copied onto every
    scene row -- 37 of 48 scenes in one trailer carried an identical value.
    A handful of rows then differ only because the estimator slipped an
    octave. Treating those as "the music speeds up in this shot" invents an
    editorial problem out of an analysis artefact, which is exactly the kind
    of finding an editor would check and find nothing at.

    So a feature only earns a per-scene finding when it genuinely moves per
    scene: more than a couple of distinct values, and not one value dominating
    almost every shot.
    """
    stats = getattr(baseline, {"tempo_bpm": "tempo"}.get(dominant, dominant), None)
    values = list(getattr(stats, "values", []) or []) if stats is not None else []
    if len(values) < 8:
        return True  # too short to judge; leave the model's decision alone

    rounded = [round(v, 3) for v in values]
    distinct = len(set(rounded))
    most_common_share = max(Counter(rounded).values()) / len(rounded)
    return distinct >= 4 and most_common_share <= 0.80


def _measurement_is_trustworthy(
    dominant: str, observed: float, baseline: TrailerBaseline
) -> bool:
    """Reject values that are analysis failures rather than measurements.

    Detectors report "found nothing" as exactly 0.0, which is indistinguishable
    from a real measurement of zero unless you look at the whole series. When a
    sizeable share of scenes sit on exactly 0.0, that value is the detector's
    sentinel -- 21% of scenes in one trailer had object_score 0.0 with an empty
    object list, meaning YOLO detected nothing there, not that the frame was
    visually empty. Calling that "visually emptier than the trailer's median"
    turns a detector miss into an aesthetic judgement about the film.

    Checking the share (rather than one row's object list) is what makes this a
    property of the measurement instead of a special case per feature.
    """
    if dominant == "tempo_bpm" and not (_PLAUSIBLE_BPM[0] <= observed <= _PLAUSIBLE_BPM[1]):
        return False

    if observed != 0.0:
        return True

    stats = getattr(baseline, {"tempo_bpm": "tempo"}.get(dominant, dominant), None)
    values = list(getattr(stats, "values", []) or []) if stats is not None else []
    if not values:
        # No series to judge by: an exact zero on a signal that should be a
        # measured quantity is far more likely a miss than a real reading.
        return False
    zero_share = sum(1 for v in values if v == 0.0) / len(values)
    return zero_share < 0.05


def _baseline_median_for(dominant: str, baseline: TrailerBaseline) -> float | None:
    """This trailer's own median for that feature, or None if it keeps no
    baseline for it (object_score and emotion_confidence have none), so the
    text can omit the comparison instead of printing a fabricated 0.00."""
    attr = {"tempo_bpm": "tempo"}.get(dominant, dominant)
    stats = getattr(baseline, attr, None)
    median = getattr(stats, "median", None) if stats is not None else None
    return float(median) if isinstance(median, (int, float)) else None


def _explain_anomaly(
    dominant: str, dominant_z: float, unusualness: float, i: int, n: int,
    scene_rows: list[dict[str, Any]], baseline: TrailerBaseline, primary_genre: str,
    phase_name: str, pos_pct: float, scene_id: Any, timeframe: str,
    start_t: float, end_t: float, scene_type_conf: float,
) -> "_ProblemCandidate | None":
    """Turn 'the model flagged scene i as anomalous, dominant feature X' into
    a genre-aware problem/why/fix. The DECISION that this scene is unusual
    already came from the real IsolationForest model; this only explains it
    in readable terms and applies craft-convention checks (an intentionally
    held emotional beat isn't an editing error even if it's statistically
    unusual) to avoid flagging deliberate choices as mistakes.
    """
    ev = scene_rows[i]["evidence"]
    confidence = round(min(0.95, 0.35 + unusualness * 0.6), 4)
    severity = round(min(0.9, 0.25 + unusualness * 0.65), 4)

    if dominant == "shot_duration":
        direction = "longer" if ev.shot_duration > baseline.shot_duration.median else "shorter"
        return _ProblemCandidate(
            scene_idx=i, scene_id=scene_id, timeframe=timeframe, start_time=start_t, end_time=end_t,
            problem=(
                f"Shot duration ({ev.shot_duration:.1f}s) is a statistical outlier for this trailer "
                f"(model anomaly score: {unusualness:.0%}; trailer median: {baseline.shot_duration.median:.1f}s)."
            ),
            why=(
                f"This {ev.shot_duration:.1f}s shot stands out as unusual against every other scene "
                f"in this specific trailer, which disrupts its established pacing rhythm."
            ),
            fix=(
                f"Trim this shot toward the trailer's own median of "
                f"{baseline.shot_duration.median:.1f}s, or confirm the hold is deliberate."
                if direction == "longer" else
                f"Extend this shot toward the trailer's own median of "
                f"{baseline.shot_duration.median:.1f}s so it has room to register."
            ),
            evidence_details={
                "shot_duration": ev.shot_duration, "trailer_median": baseline.shot_duration.median,
                "anomaly_score": unusualness, "phase": phase_name, "scene_type": ev.scene_type,
            },
            category="Pacing", raw_confidence=confidence, severity_score=severity, focus_area="pacing",
        )

    if dominant in ("energy_delta_prev", "energy_delta_next"):
        curr_energy = (ev.motion + ev.audio_energy) / 2.0
        neighbor_idx = i - 1 if dominant == "energy_delta_prev" else i + 1
        if 0 <= neighbor_idx < n:
            neighbor_ev = scene_rows[neighbor_idx]["evidence"]
            neighbor_energy = (neighbor_ev.motion + neighbor_ev.audio_energy) / 2.0
        else:
            neighbor_energy = curr_energy
        is_drop = curr_energy < neighbor_energy

        if is_drop:
            return _ProblemCandidate(
                scene_idx=i, scene_id=scene_id, timeframe=timeframe, start_time=start_t, end_time=end_t,
                problem=(
                    f"Energy discontinuity: this scene's energy ({curr_energy:.2f}) drops sharply "
                    f"from its neighbor ({neighbor_energy:.2f}) — flagged as statistically unusual "
                    f"for this trailer (anomaly score: {unusualness:.0%})."
                ),
                why="This gap disrupts momentum relative to the trailer's own established rhythm.",
                fix=(
                    f"Close the {abs(curr_energy - neighbor_energy):.2f} energy gap to its neighbour, "
                    f"or confirm this is a deliberate breath and the surrounding cuts prepare for it."
                ),
                evidence_details={
                    "scene_energy": curr_energy, "neighbor_energy": neighbor_energy,
                    "anomaly_score": unusualness, "phase": phase_name,
                },
                category="Pacing", raw_confidence=confidence, severity_score=severity, focus_area="pacing continuity",
            )

        if phase_name in ("peak", "climax_montage", "hook") or pos_pct >= 0.7:
            return None  # a spike near the climax is expected, not an error
        return _ProblemCandidate(
            scene_idx=i, scene_id=scene_id, timeframe=timeframe, start_time=start_t, end_time=end_t,
            problem=(
                f"Unexpected energy spike: this scene's energy ({curr_energy:.2f}) is significantly "
                f"higher than its neighbor ({neighbor_energy:.2f}) in the {phase_name} phase "
                f"(anomaly score: {unusualness:.0%})."
            ),
            why=(
                "A sharp, statistically unusual energy spike outside the climax can feel premature "
                "and may undercut the trailer's escalation arc."
            ),
            fix=(
                f"Reposition this beat closer to the climax, or add a transitional shot so the "
                f"jump from {neighbor_energy:.2f} to {curr_energy:.2f} is prepared rather than abrupt."
            ),
            evidence_details={
                "scene_energy": curr_energy, "neighbor_energy": neighbor_energy,
                "anomaly_score": unusualness, "phase": phase_name,
            },
            category="Pacing", raw_confidence=confidence, severity_score=severity, focus_area="escalation",
        )

    if dominant == "audio_motion_gap":
        is_motion_high = ev.motion > ev.audio_energy
        if ev.scene_type.lower() in ("dialogue", "drama") and not is_motion_high:
            return None  # quiet dialogue is a normal cinematic register, not an error
        return _ProblemCandidate(
            scene_idx=i, scene_id=scene_id, timeframe=timeframe, start_time=start_t, end_time=end_t,
            problem=(
                f"Audio-visual energy mismatch: motion={ev.motion:.2f} vs audio_energy={ev.audio_energy:.2f} "
                f"(anomaly score: {unusualness:.0%})."
            ),
            why=(
                f"{'High visual motion with low audio energy' if is_motion_high else 'High audio intensity with low visual motion'} "
                f"stands out as statistically unusual for this trailer and can feel dissonant."
            ),
            fix=(
                f"Bring the {'audio up to match the movement' if is_motion_high else 'visuals up to match the audio'} "
                f"at {timeframe} — the two currently sit {abs(ev.motion - ev.audio_energy):.2f} apart."
            ),
            evidence_details={
                "motion": ev.motion, "audio_energy": ev.audio_energy,
                "anomaly_score": unusualness, "scene_type": ev.scene_type,
            },
            category="Audio" if is_motion_high else "Visual",
            raw_confidence=confidence, severity_score=severity, focus_area="audio-visual sync",
        )

    # A raw signal (motion, audio energy, visual impact, tempo, emotional
    # intensity) dominates without a specific pacing/AV pattern above.
    display_name = _FEATURE_DISPLAY_NAMES.get(dominant, dominant.replace("_", " "))
    is_high = dominant_z > 0

    if dominant == "ei" and is_high:
        # An unusually high emotional-intensity scene is very likely this
        # trailer's signature moment, not an editing mistake — don't flag it.
        return None

    observed = _dominant_observed_value(dominant, ev)

    # Two validity gates before this becomes an editorial note. They ask
    # whether the number is a real per-scene measurement of THIS trailer, not
    # whether the value is one we like — a finding built on a global constant
    # or a detector miss is fabricated no matter how the sentence is worded.
    if not _is_scene_level_signal(dominant, baseline):
        return None
    if not _measurement_is_trustworthy(dominant, observed, baseline):
        return None

    category = "Audio" if dominant in ("audio_energy", "tempo_bpm") else "Visual"
    direction_text = "unusually high" if is_high else "unusually low"

    # This branch handles every raw signal (tempo, motion, audio energy, visual
    # impact, emotion clarity), so it produces most of the output. It used to
    # fill one f-string from just the measurement name and its direction — ten
    # possible sentences for the whole detector, which is why the same wording
    # recurred across trailers. It now composes from the measurement, its
    # magnitude band, the structural phase, the position in the runtime and
    # the scene's own type, all of which were already computed here and simply
    # went unused. Two findings now read alike only when they measure alike.
    reference = _baseline_median_for(dominant, baseline)
    text = compose_finding(
        display_name=display_name,
        observed=observed,
        reference=reference,
        reference_label="this trailer's own median",
        is_high=is_high,
        magnitude=unusualness,
        phase=phase_name,
        position_pct=pos_pct,
        scene_type=ev.scene_type,
        unit=" BPM" if dominant == "tempo_bpm" else "",
    )

    return _ProblemCandidate(
        scene_idx=i, scene_id=scene_id, timeframe=timeframe, start_time=start_t, end_time=end_t,
        problem=text["problem"],
        why=text["why"],
        fix=text["fix"],
        evidence_details={
            "dominant_feature": dominant, "direction": direction_text,
            "observed": observed, "trailer_median": reference,
            "anomaly_score": unusualness, "phase": phase_name,
            "magnitude_band": text["band"], "scene_type": ev.scene_type,
        },
        category=category, raw_confidence=confidence, severity_score=severity, focus_area="intensity consistency",
    )


def _detect_statistical_anomalies(
    scene_rows: list[dict[str, Any]],
    baseline: TrailerBaseline,
    genre_profile: TrailerProfile,
    structure: StructureReport,
) -> list[_ProblemCandidate]:
    """Detect scenes that are real statistical anomalies for this trailer.

    Uses a real IsolationForest (anomaly_detector.py) fit fresh on this
    trailer's own real per-scene evidence — unsupervised, no synthetic
    data, no hand-picked magic-number thresholds. The model decides
    whether each scene is unusual; craft-convention checks below only
    suppress cases where the statistically-unusual scene is a deliberate,
    recognizable cinematic choice (an emotional hold, a suspense beat)
    rather than an editing mistake.
    """
    problems: list[_ProblemCandidate] = []
    n = len(scene_rows)

    anomalies = detect_scene_anomalies(scene_rows)
    if not anomalies:
        return problems  # not enough scenes for the model to learn this trailer's own structure

    primary_genre = genre_profile.primary_genre

    for a in anomalies:
        if not a["is_anomaly"]:
            continue
        if band_for(float(a["anomaly_score"])) == "marginal":
            continue

        i = a["scene_idx"]
        row = scene_rows[i]
        timeframe = row.get("timeframe", "")
        scene_id = row.get("scene", i + 1)
        start_t, end_t = _parse_timeframe_seconds(timeframe)
        pos_pct = i / max(n, 1)
        phase_name = _get_scene_phase(i, structure)
        scene_type_conf = getattr(row["evidence"], "scene_type_confidence", 1.0) or 1.0

        candidate = _explain_anomaly(
            a["dominant_feature"], a["dominant_z"], a["anomaly_score"], i, n, scene_rows, baseline,
            primary_genre, phase_name, pos_pct, scene_id, timeframe, start_t, end_t, scene_type_conf,
        )
        if candidate is not None:
            problems.append(candidate)

    return problems


def _opening_resolution_scene_idxs(structure: StructureReport) -> tuple[set[int], set[int]]:
    """0-indexed scene indices belonging to the opening (setup/hook) or
    resolution phases, per THIS trailer's own energy-curve-derived structure
    (structure_segmentation.py) — not a fixed "first 10%" rule."""
    opening, resolution = set(), set()
    for phase in structure.phases:
        idxs = range(phase.start_scene - 1, phase.end_scene)  # to 0-indexed
        if phase.phase_name in ("setup", "hook"):
            opening.update(idxs)
        elif phase.phase_name == "resolution":
            resolution.update(idxs)
    return opening, resolution


def _detect_visual_integrity_problems(
    scene_rows: list[dict[str, Any]],
    frames_dir: Path | None,
    real_title: str,
    real_release_date: str,
    structure: StructureReport,
) -> list[_ProblemCandidate]:
    """Frame-level checks: logo placement, on-screen title, on-screen release
    date. Returns [] when no scene thumbnails exist for this trailer (older
    runs that predate frame mirroring) — a coverage gap, not a finding to
    fabricate around."""
    opening_idxs, resolution_idxs = _opening_resolution_scene_idxs(structure)
    findings = detect_visual_integrity(
        scene_rows, frames_dir, real_title, real_release_date, opening_idxs, resolution_idxs
    )
    if not findings.frames_available or findings.scenes_scanned == 0:
        return []

    coverage = findings.scenes_scanned / max(len(scene_rows), 1)
    candidates: list[_ProblemCandidate] = []

    if findings.logo_hits and findings.logo_outside_expected_phase:
        hit = findings.logo_hits[0]
        start_t, end_t = _parse_timeframe_seconds(hit["timeframe"])
        candidates.append(_ProblemCandidate(
            scene_idx=hit["scene_idx"], scene_id=hit["scene_id"], timeframe=hit["timeframe"],
            start_time=start_t, end_time=end_t,
            problem=f"A studio/production logo card appears mid-trailer (scene {hit['scene_id']}), outside this trailer's own opening or closing beats.",
            why="Logo cards conventionally bookend a trailer — open on production idents, close on the distributor card. One appearing mid-trailer reads as a stray clip rather than a deliberate structural choice.",
            fix="Move this logo card to the opening beat or the closing button, or confirm it's an intentional mid-trailer co-production credit and leave it.",
            evidence_details={"logo_confidence": hit["confidence"], "detected_at_position_pct": round((hit["scene_idx"] + 0.5) / max(len(scene_rows), 1), 2)},
            category="Structure", raw_confidence=round(hit["confidence"] * coverage, 3), severity_score=0.5,
            focus_area="logo placement",
        ))

    total_scenes = max(len(scene_rows), 1)
    last_idx = total_scenes - 1
    last_row = scene_rows[last_idx]
    last_timeframe = last_row.get("timeframe", "")
    last_start, last_end = _parse_timeframe_seconds(last_timeframe)
    last_scene_id = last_row.get("scene", last_idx + 1)

    # OCR is capped at _MAX_OCR_CALLS scenes, so on a long trailer only part of
    # it is actually read. Claiming the title appears "nowhere" after reading a
    # third of the scenes overstates the evidence, so the sentence reports the
    # scan it really performed. Note this uses scenes_ocr_read, NOT
    # scenes_scanned — the latter counts the logo pass, which covers every
    # frame and would make partial OCR look like full coverage.
    ocr_read = findings.scenes_ocr_read
    ocr_coverage = ocr_read / total_scenes
    scanned_all = ocr_coverage >= 0.80
    scan_note = (
        "anywhere in the trailer"
        if scanned_all
        else f"in the {ocr_read} of {total_scenes} scenes that were read for text "
             f"({ocr_coverage:.0%} of the trailer)"
    )

    if findings.title_hit is None and real_title:
        candidates.append(_ProblemCandidate(
            scene_idx=last_idx, scene_id=last_scene_id, timeframe=last_timeframe,
            start_time=last_start, end_time=last_end,
            problem=f'"{real_title}" was not found as on-screen text {scan_note}.',
            why=("A trailer that never shows its own title leaves the audience without the one piece "
                 "of information they need to look the movie up afterward."
                 + ("" if scanned_all else " Confirm against the unscanned scenes before acting on this.")),
            fix="Add a title card — most commonly right after the hook or as the final beat before the release date.",
            evidence_details={"real_title": real_title, "scenes_read_for_text": ocr_read,
                              "total_scenes": total_scenes, "text_scan_coverage_pct": round(ocr_coverage, 2)},
            category="Metadata", raw_confidence=round(0.55 + 0.25 * ocr_coverage, 3), severity_score=0.55,
            focus_area="movie identification",
        ))

    if findings.release_date_hit is None and real_release_date:
        candidates.append(_ProblemCandidate(
            scene_idx=last_idx, scene_id=last_scene_id, timeframe=last_timeframe,
            start_time=last_start, end_time=last_end,
            problem=f"No release-date text (e.g. \"IN THEATERS ...\") was found {scan_note}.",
            why=f"The real release date ({real_release_date}) exists but this cut never tells the audience when to expect it.",
            fix="Add a release-date card as the trailer's closing beat.",
            evidence_details={"real_release_date": real_release_date, "scenes_read_for_text": ocr_read,
                              "total_scenes": total_scenes, "text_scan_coverage_pct": round(ocr_coverage, 2)},
            category="Metadata", raw_confidence=round(0.5 + 0.25 * ocr_coverage, 3), severity_score=0.5,
            focus_area="release info",
        ))

    # Tag the whole group at the exit rather than in each constructor above, so
    # a check added later cannot be left mislabelled as a template finding.
    # Without this they default to "template" and become indistinguishable from
    # the pacing/audio detectors in the response.
    for candidate in candidates:
        candidate.fix_source = "visual-integrity"

    return candidates


def _get_scene_phase(scene_idx: int, structure: StructureReport) -> str:
    """Get the structural phase name for a scene index."""
    scene_num = scene_idx + 1  # 1-indexed
    for phase in structure.phases:
        if phase.start_scene <= scene_num <= phase.end_scene:
            return phase.phase_name
    return "unknown"


_SOURCE_BONUS = {
    "technical": 0.16,
    "problem-model": 0.12,
    "visual-integrity": 0.10,
    "genre-norm": 0.08,
    "trailer-anomaly": 0.0,
}


def _candidate_rank_score(candidate: _ProblemCandidate) -> float:
    """Comparable quality score used only to order candidate findings."""
    return (
        0.55 * candidate.severity_score
        + 0.35 * candidate.raw_confidence
        + _SOURCE_BONUS.get(candidate.fix_source, 0.0)
    )


def _candidate_issue_key(candidate: _ProblemCandidate) -> str:
    """Stable root-cause key shared by repeated detections of one issue."""
    details = candidate.evidence_details
    root = (
        details.get("problem_class")
        or details.get("dimension")
        or details.get("dominant_feature")
        or candidate.focus_area
    )
    normalised = re.sub(r"[^a-z0-9]+", "-", str(root).lower()).strip("-")
    return f"{candidate.fix_source}:{candidate.category.lower()}:{normalised}"


def _time_overlap(a: _ProblemCandidate, b: _ProblemCandidate) -> float:
    intersection = max(0.0, min(a.end_time, b.end_time) - max(a.start_time, b.start_time))
    shortest = min(
        max(a.end_time - a.start_time, 0.01),
        max(b.end_time - b.start_time, 0.01),
    )
    return intersection / shortest


def _select_diverse_candidates(
    candidates: list[_ProblemCandidate], total_scenes: int
) -> list[_ProblemCandidate]:
    """Keep the strongest distinct, actionable findings.

    Different detectors often rediscover the same underlying issue at several
    adjacent shots. The strongest instance is kept as the recommendation and
    the other locations are retained as supporting evidence. A small adaptive
    cap favours precision and usability over a report that flags most scenes.
    """
    ordered = sorted(candidates, key=_candidate_rank_score, reverse=True)
    unique: list[_ProblemCandidate] = []
    by_issue: dict[str, _ProblemCandidate] = {}

    for candidate in ordered:
        issue_key = _candidate_issue_key(candidate)
        existing = by_issue.get(issue_key)
        if existing is not None:
            related = existing.evidence_details.setdefault("related_locations", [])
            location = {
                "scene": candidate.scene_id,
                "timeframe": candidate.timeframe,
                "confidence": round(candidate.raw_confidence, 4),
            }
            if location not in related:
                related.append(location)
            continue
        by_issue[issue_key] = candidate
        unique.append(candidate)

    max_recommendations = min(8, max(3, math.ceil(math.sqrt(max(total_scenes, 1)))))
    selected: list[_ProblemCandidate] = []
    category_counts: Counter[str] = Counter()

    for candidate in unique:
        # No more than two findings can compete for exactly the same time
        # range, even if different detectors name them differently.
        overlapping = sum(_time_overlap(candidate, item) >= 0.70 for item in selected)
        if overlapping >= 2:
            continue
        if category_counts[candidate.category] >= 3 and len(selected) >= 4:
            continue
        selected.append(candidate)
        category_counts[candidate.category] += 1
        if len(selected) >= max_recommendations:
            break

    return selected


_ACTION_STOPWORDS = {
    "a", "an", "and", "at", "for", "in", "of", "or", "the", "this",
    "to", "toward", "with", "so", "that", "it", "is", "be",
}


def _action_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z]+", text.lower())
        if len(token) > 2 and token not in _ACTION_STOPWORDS
    }


def _actions_are_similar(left: str, right: str) -> bool:
    a, b = _action_tokens(left), _action_tokens(right)
    if not a or not b:
        return False
    return len(a & b) / max(1, len(a | b)) >= 0.55


# ── Main recommendation generation ───────────────────────────────────

def generate_cinematic_recommendations(
    scene_rows: list[dict[str, Any]],
    trailer_title: str,
    dominant_genre: str,
    secondary_genre: str | None,
    trailer_type: str,
    structure_report: StructureReport,
    baseline: TrailerBaseline | None = None,
    genre_profile: TrailerProfile | None = None,
    popularity_context: Any = None,
    sentiment_context: Any = None,
    frames_dir: Path | None = None,
    real_title: str = "",
    real_release_date: str = "",
    colour_series: dict[str, list[float]] | None = None,
) -> tuple[list[Recommendation], list[TimelineInsight], list[TimingRoadmapItem], ComponentScores]:
    """Generate evidence-based, genre-aware recommendations.

    This function:
    1. Runs technical problem detection (deterministic).
    2. Runs statistical anomaly detection (trailer-relative).
    3. Filters and ranks candidates by severity.
    4. Returns only significant problems (not 1 per scene).
    5. Generates timeline insights for all scenes (always).
    """
    total_scenes = max(len(scene_rows), 1)

    # Ensure we have baseline and profile
    if baseline is None:
        from app.services.trailer_baseline import build_trailer_baseline
        baseline = build_trailer_baseline(scene_rows)

    if genre_profile is None:
        genre_profile = TrailerProfile(
            primary_genre=dominant_genre,
            secondary_genres=[secondary_genre] if secondary_genre else [],
            genre_probabilities={dominant_genre: 0.6},
            genre_confidence=0.5,
        )

    # ── 1. Detect problems ───────────────────────────────────────────
    #
    # Three independent detectors run and each proposes "candidate" problems.
    # Nothing is final yet — candidates get filtered and ranked in section 2.

    candidates: list[_ProblemCandidate] = []

    # Detector A — objective faults. Not opinions: silent audio, a shot that
    # ends before it starts, two scenes claiming the same timestamps. These
    # are always wrong regardless of genre, so no model is involved.
    technical_candidates = _detect_technical_problems(scene_rows)
    for candidate in technical_candidates:
        candidate.fix_source = "technical"
    candidates.extend(technical_candidates)

    # Detector B — the odd-one-out model (IsolationForest). Finds scenes that
    # stand apart from the rest of THIS trailer. Note the limitation: it can
    # only spot internal inconsistency, so a trailer that is uniformly wrong
    # looks fine to it. That gap is what the genre norms are being built for.
    anomaly_candidates = _detect_statistical_anomalies(
        scene_rows, baseline, genre_profile, structure_report
    )
    for candidate in anomaly_candidates:
        candidate.fix_source = "trailer-anomaly"
    candidates.extend(anomaly_candidates)

    # Detector C — looks at the actual picture, not the numbers. Uses CLIP to
    # spot logo cards and OCR to read on-screen text, checked against the real
    # title and release date from IMDb.
    #
    # Kept in its own list rather than added to `candidates` for a reason: these
    # are facts about the WHOLE trailer ("the title never appears"), not about
    # one scene. If they went into the shared pool, the per-scene de-duplication
    # below would make them compete against that scene's own anomaly — and a
    # missing title card would silently vanish whenever the last scene happened
    # to have a higher-severity pacing problem. That bug did occur; this is the fix.
    visual_integrity_candidates = [
        c for c in _detect_visual_integrity_problems(
            scene_rows, frames_dir, real_title, real_release_date, structure_report
        )
        if c.raw_confidence >= 0.45
    ]

    # Detector E — the trained editorial-problem classifier.
    #
    # This is the only detector that names a PROBLEM rather than reporting a
    # measurement that stands out. Detectors B and D both answer "which number
    # is unusual here?", which is why their findings read as comparisons. This
    # one answers "which known editorial defect does this stretch look like?",
    # having been trained on professional trailers deliberately broken in six
    # specific ways. Its findings therefore carry a named fault and a fix for
    # that fault, with the measurements demoted to supporting evidence.
    #
    # It also has a property none of the others do: it can return nothing.
    # An outlier detector always finds a most-unusual scene even in a flawless
    # trailer; a classifier can say every window looks professionally cut.
    problem_candidates: list[_ProblemCandidate] = []
    model_predictions, model_meta = predict_problems(scene_rows)
    for pred in model_predictions:
        lang = PROBLEM_LANGUAGE.get(pred.problem)
        if lang is None:
            continue
        first_row = scene_rows[pred.start_idx]
        last_row = scene_rows[min(pred.end_idx, len(scene_rows) - 1)]
        start_t, _ = _parse_timeframe_seconds(first_row.get("timeframe", ""))
        _, end_t = _parse_timeframe_seconds(last_row.get("timeframe", ""))
        problem_candidates.append(_ProblemCandidate(
            scene_idx=pred.start_idx,
            scene_id=first_row.get("scene", pred.start_idx + 1),
            timeframe=f"{int(start_t // 60):02d}:{start_t % 60:05.2f}-{int(end_t // 60):02d}:{end_t % 60:05.2f}",
            start_time=start_t, end_time=end_t,
            problem=lang["problem"],
            why=(f"A model trained on {model_meta.get('trained_on', 0)} professional trailers "
                 f"recognises this stretch as {lang['label'].lower()} "
                 f"({pred.confidence:.0%} confidence). Scenes "
                 f"{first_row.get('scene', pred.start_idx + 1)} to {last_row.get('scene', pred.end_idx + 1)}."),
            fix=lang["fix"],
            evidence_details={
                "problem_class": pred.problem,
                "model_confidence": pred.confidence,
                "class_probabilities": pred.class_probabilities,
                "model_drivers": pred.drivers,
                "scene_range": [pred.start_idx + 1, pred.end_idx + 1],
            },
            category="Pacing" if pred.problem in ("pacing_drag", "over_cutting", "rhythm_monotony") else "Audio" if pred.problem == "dead_air" else "Structure",
            raw_confidence=pred.confidence,
            severity_score=round(min(0.9, 0.4 + 0.5 * pred.confidence), 4),
            focus_area=lang["label"].lower(),
            fix_source="problem-model",
        ))

    # Detector D — compare against what real trailers of this genre do.
    # This is the one detector that can catch a trailer which is uniformly
    # wrong: detectors B and C only see inconsistency *within* the trailer,
    # so a film whose pacing is bad from start to finish looks self-consistent
    # to them. Its findings are also kept out of the per-scene pool, because a
    # norm deviation is a statement about a stretch of the trailer rather than
    # a competitor to one scene's own anomaly.
    norm_candidates: list[_ProblemCandidate] = []
    if genre_profile.genre_confidence >= 0.45:
        norm_findings, norm_meta = detect_norm_deviations(
            scene_rows, dominant_genre, colour_series=colour_series
        )
    else:
        norm_findings, norm_meta = [], {
            "norm_available": False,
            "genre": dominant_genre,
            "note": "Genre confidence is too low for genre-specific norms.",
        }
    for f in norm_findings:
        norm_candidates.append(_ProblemCandidate(
            scene_idx=f["scene_idx"], scene_id=f["scene_id"], timeframe=f["timeframe"],
            start_time=f["start_time"], end_time=f["end_time"],
            problem=f["problem"], why=f["why"], fix=f["fix"],
            evidence_details={
                "measured": f["observed"], "genre_expected": f["expected"],
                "genre_sd": f["expected_std"], "z_score": f["z"],
                "dimension": f["dimension"], "norm_trailers": norm_meta.get("norm_trailers"),
                "genre": norm_meta.get("genre"),
            },
            category=f["category"], raw_confidence=f["confidence"],
            severity_score=f["severity_score"], focus_area=f["focus_area"],
            fix_source="genre-norm",
        ))

    # ── 2. Filter and deduplicate ────────────────────────────────────
    #
    # A detector that flags everything is useless. This section cuts the
    # candidate list down to the findings worth an editor's attention.

    # Weak findings and marginal outliers are more likely to be intentional
    # creative choices than genuine defects.
    candidates = [c for c in candidates if c.raw_confidence >= 0.45]

    final_candidates = _select_diverse_candidates(
        problem_candidates
        + candidates
        + visual_integrity_candidates
        + norm_candidates,
        total_scenes,
    )

    # ── 2b. Generate genuinely unique fix text via Claude, grounded in
    #        each candidate's real detected evidence (falls back to the
    #        template text below on any failure — never blocks). ──────
    if final_candidates:
        llm_payload = [
            {
                "id": idx,
                "scene": c.scene_id,
                "timeframe": c.timeframe,
                "genre": dominant_genre,
                "category": c.category,
                "focus_area": c.focus_area,
                "phase": _get_scene_phase(c.scene_idx, structure_report),
                "detected_problem": c.problem,
                "evidence_details": c.evidence_details,
            }
            for idx, c in enumerate(final_candidates)
        ]
        llm_results = generate_fix_text(llm_payload)
        if llm_results:
            for idx, c in enumerate(final_candidates):
                result = llm_results.get(idx)
                if result:
                    c.evidence_details["detector_source"] = c.fix_source
                    c.why = result["why"]
                    c.fix = result["fix"]
                    c.fix_source = str(result.get("source") or "generated-wording")

    # A text generator can still phrase distinct detections as the same edit.
    # Keep one actionable recommendation and attach the suppressed location to
    # its evidence instead of showing duplicate cards to the editor.
    wording_diverse: list[_ProblemCandidate] = []
    for candidate in final_candidates:
        duplicate = next(
            (
                existing
                for existing in wording_diverse
                if _actions_are_similar(candidate.fix, existing.fix)
            ),
            None,
        )
        if duplicate is not None:
            duplicate.evidence_details.setdefault("related_recommendations", []).append({
                "scene": candidate.scene_id,
                "timeframe": candidate.timeframe,
                "focus_area": candidate.focus_area,
                "confidence": round(candidate.raw_confidence, 4),
            })
            continue
        wording_diverse.append(candidate)
    final_candidates = wording_diverse

    # ── 3. Convert to Recommendation objects ─────────────────────────

    recommendations: list[Recommendation] = []

    for candidate in final_candidates:
        row = scene_rows[candidate.scene_idx]
        ev = row["evidence"]
        # 1. Map candidate anomaly score to Base Priority Score (35, 60, or 85)
        severity = _severity_from_score(candidate.severity_score)
        priority_label, priority_num, priority_score = _priority_from_severity(severity)

        # Priority follows the detected defect and its confidence. A globally
        # low signal (for example low motion in dialogue) is not automatically
        # a problem and must not inflate an unrelated finding.
        confidence_score = int(round(candidate.raw_confidence * 100))
        final_priority_score = int(round(priority_score * 0.70 + confidence_score * 0.30))

        rec = Recommendation(
            id=str(uuid.uuid4()),
            scene=candidate.scene_id,
            scene_label=f"Scene {candidate.scene_id}",
            timeframe=candidate.timeframe,
            phase=_get_scene_phase(candidate.scene_idx, structure_report),
            problem=candidate.problem,
            recommendation=candidate.fix,
            reason=candidate.why,
            reasoning=f"Detected by statistical analysis (genre: {dominant_genre}, phase: {_get_scene_phase(candidate.scene_idx, structure_report)}).",
            strengths=[f"Emotional Intensity: {ev.ei:.2f}", f"Scene Type: {ev.scene_type}"],
            problems=[candidate.problem],
            expected_improvement="Evidence-based improvement",
            focus_area=candidate.focus_area,
            priority_score=max(10, min(100, final_priority_score)),
            priority=priority_label,
            evidence=ev,
            title=candidate.problem[:80],
            action=candidate.fix,
            evidence_text=candidate.why,
            category=candidate.category,
            priority_num=priority_num,
            component="Statistical Anomaly Detection Engine",
            expected_impact=f"Confidence: {candidate.raw_confidence:.0%}",
            severity=severity,
            confidence=round(candidate.raw_confidence, 4),
            evidence_details=candidate.evidence_details,
            start_time=candidate.start_time,
            end_time=candidate.end_time,
            why=candidate.why,
            fix_source=candidate.fix_source,
        )
        recommendations.append(rec)

    # ── 4. Generate timeline insights (for ALL scenes) ───────────────

    timeline_insights: list[TimelineInsight] = []
    timing_roadmap: list[TimingRoadmapItem] = []

    for i, row in enumerate(scene_rows):
        evidence = row["evidence"]
        ei_level = "High" if evidence.ei >= 0.65 else "Medium" if evidence.ei >= 0.40 else "Low"

        timeline_insights.append(TimelineInsight(
            scene=row["scene"],
            timeframe=row["timeframe"],
            intensity_level=ei_level,
            strongest_signal=(
                f"Emotional Intensity ({evidence.ei:.2f})"
                if evidence.ei >= evidence.motion and evidence.ei >= evidence.audio_energy
                else f"Motion ({evidence.motion:.2f})"
                if evidence.motion >= evidence.audio_energy
                else f"Audio Energy ({evidence.audio_energy:.2f})"
            ),
            weakest_signal=(
                f"Motion ({evidence.motion:.2f})"
                if evidence.motion <= evidence.audio_energy and evidence.motion <= evidence.ei
                else f"Audio Energy ({evidence.audio_energy:.2f})"
                if evidence.audio_energy <= evidence.ei
                else f"Emotional Intensity ({evidence.ei:.2f})"
            ),
            evidence=evidence,
        ))

        # Find recommendation for this scene (if any)
        scene_rec = next((r for r in recommendations if r.scene == row["scene"]), None)
        suggestion = scene_rec.action if scene_rec else "No significant issues detected."
        priority = scene_rec.priority_num if scene_rec else 3

        timing_roadmap.append(TimingRoadmapItem(
            timeframe=row["timeframe"],
            scene=f"Scene {row['scene']}",
            currentEmotion=(evidence.visual_emotion or "neutral").title(),
            suggestion=suggestion,
            priority=priority,
        ))

    # ── 5. Component scores ──────────────────────────────────────────

    avg_ei = sum(r["evidence"].ei for r in scene_rows) / total_scenes if scene_rows else 0.8

    # Base scores from actual data quality
    audio_issues = sum(1 for r in recommendations if r.category == "Audio")
    visual_issues = sum(1 for r in recommendations if r.category == "Visual")
    pacing_issues = sum(1 for r in recommendations if r.category == "Pacing")

    component_scores = ComponentScores(
        audio=max(60, min(98, 95 - audio_issues * 8)),
        visual=max(60, min(98, 95 - visual_issues * 8)),
        metadata=max(70, min(98, int(82 + (popularity_context.popularity_score or 0.8) * 10 if popularity_context else 84))),
        fusion=max(65, min(98, 95 - (audio_issues + visual_issues + pacing_issues) * 3)),
    )

    return recommendations, timeline_insights, timing_roadmap, component_scores
