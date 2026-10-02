"""Builds finding text as a function of the measurement, not from a fixed frame.

The problem this solves
-----------------------
The detectors measure each trailer individually, but the text describing a
finding used to come from one f-string per measurement type. So every trailer
with an unusual tempo got the identical sentence with a different number in it
-- "This scene's musical tempo is unusually high..." appeared 12 times across
four trailers. The findings were per-trailer; the writing was not.

The approach
------------
Every clause here is selected by a real measured feature:

  magnitude  -- how far from normal (band: marginal / clear / extreme)
  direction  -- above or below
  measure    -- which of the signals is off
  phase      -- where in the trailer's own structure it happens
  position   -- how far through the runtime
  scene_type -- what the shot actually contains

The point is NOT to paraphrase the same advice in more ways. It is that the
advice genuinely differs: a flat mix in the opening is a different editorial
problem from a flat mix at the climax, so they get different consequences and
different fixes. Two findings read the same only when they measure the same.

What this is and isn't
----------------------
This is deterministic composition: identical measurements produce identical
text, which makes every sentence traceable back to a number. It is not
generative writing -- for that the engine calls Claude via llm_fix_generator,
which supersedes this text when an API key is configured. The vocabulary here
describes measurements and editing craft; it holds no per-genre rules, so it
cannot reintroduce the hand-written genre assumptions that were removed.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Magnitude bands ───────────────────────────────────────────────────
# How emphatic the language should be, chosen from how far off the value is.
# Thresholds are on a 0-1 "unusualness" scale (anomaly score, or |z| capped).
#
# These used to be hand-picked constants (0.75 / 0.45). That scale is a
# per-trailer min-max rescaling of an IsolationForest score (0 = this
# trailer's most normal scene, 1 = its most unusual one), so a fixed number
# had no real anchor -- nothing said 0.75 was actually rare. The cutoffs
# below are read off the REAL distribution of that same score across 8,742
# scenes from 99 professionally-cut trailers (scripts/build_magnitude_bands.py):
# "extreme" is the ~top 10% most unusual a scene gets in real professional
# cutting, "clear" the next slice down. Falls back to those same historical
# constants only if the artifact hasn't been generated yet.
_BANDS_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "magnitude_bands.json"


def _load_bands() -> tuple[tuple[float, str], ...]:
    try:
        data = json.loads(_BANDS_PATH.read_text(encoding="utf-8"))
        return (
            (float(data["extreme"]), "extreme"),
            (float(data["clear"]), "clear"),
            (0.00, "marginal"),
        )
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.warning(
            "No learned magnitude bands at %s (%s) — run "
            "scripts/build_magnitude_bands.py. Using placeholder cutoffs.",
            _BANDS_PATH, exc,
        )
        return ((0.75, "extreme"), (0.45, "clear"), (0.00, "marginal"))


_BANDS = _load_bands()

_BAND_ADVERB = {
    "extreme": "far",
    "clear": "well",
    "marginal": "slightly",
}

# How firmly to word the recommendation. A marginal deviation should not be
# ordered fixed -- it should be checked.
_BAND_MODAL = {
    "extreme": "",
    "clear": "",
    "marginal": "if this wasn't intentional, ",
}


def band_for(magnitude: float) -> str:
    """Name the magnitude band for a 0-1 unusualness score."""
    for threshold, name in _BANDS:
        if magnitude >= threshold:
            return name
    return "marginal"


# ── Where in the trailer ──────────────────────────────────────────────
# Position phrasing, so two findings for the same measurement at different
# points in the runtime do not open with the same words.
def _where(position_pct: float) -> str:
    if position_pct < 0.10:
        return "in the opening seconds"
    if position_pct < 0.30:
        return "early in the cut"
    if position_pct < 0.55:
        return "around the midpoint"
    if position_pct < 0.80:
        return "in the back half"
    return "in the closing stretch"


# ── What each structural phase is FOR ─────────────────────────────────
# This is the axis that makes the advice differ rather than merely the words:
# the same measurement being low means something different depending on the
# job the phase has to do.
_PHASE_JOB = {
    "hook": "the hook has to buy the audience's attention in a few seconds",
    "setup": "the setup is establishing who and what this is",
    "escalation": "this stretch is meant to be building pressure",
    "peak": "this is the trailer's peak",
    "climax_montage": "the climax montage is the payoff the cut has been promising",
    "resolution": "the closing beat is the last impression the audience keeps",
}
_PHASE_DEFAULT = "this section still has to carry the cut forward"

# Phases where WHERE the problem falls is the most notable thing about it,
# because the beat has a specific job that the deviation interferes with.
_STRUCTURAL_PHASES = frozenset({"hook", "peak", "climax_montage", "resolution"})


# ── What each measurement means to an editor ──────────────────────────
# Per MEASUREMENT, never per genre. "audio energy" means the same thing in a
# Horror trailer and a Comedy one; what differs is the number the norm supplies.
_MEASURE = {
    "emotional intensity": {
        "noun": "emotional intensity",
        "high": "carrying more emotional weight than",
        "low": "carrying less emotional weight than",
        "fix_high": "check this beat is not spending the emotional peak early",
        "fix_low": "raise the emotional charge here, or cut to a beat that carries more",
    },
    "audio energy": {
        "noun": "the mix",
        "high": "louder and denser than",
        "low": "thinner and quieter than",
        "fix_high": "pull the level back so the later beats still have somewhere to go",
        "fix_low": "lift the level, or layer in the score earlier",
    },
    "motion": {
        "noun": "on-screen movement",
        "high": "busier than",
        "low": "stiller than",
        "fix_high": "check the frame is readable at this speed",
        "fix_low": "cut to more kinetic coverage, or shorten the hold",
    },
    "visual impact": {
        "noun": "visual density",
        "high": "more visually loaded than",
        "low": "visually emptier than",
        "fix_high": "simplify the frame so the eye knows where to land",
        "fix_low": "choose a frame with more to look at",
    },
    "musical tempo": {
        "noun": "the music",
        "high": "faster than",
        "low": "slower than",
        "fix_high": "ease the tempo, or cut the picture to match the faster bar",
        "fix_low": "lift the tempo, or hold the cut until the track catches up",
    },
    "emotion clarity": {
        "noun": "the read on the performance",
        "high": "more legible than",
        "low": "harder to read than",
        "fix_high": "no change needed unless the beat plays as overstated",
        "fix_low": "favour a take where the expression reads, or hold a beat longer",
    },
}

# Falls back to the raw measurement name rather than inventing meaning for a
# signal this table does not know about.
def _measure_entry(display_name: str) -> dict[str, str]:
    return _MEASURE.get(display_name, {
        "noun": display_name,
        "high": "higher than",
        "low": "lower than",
        "fix_high": f"bring the {display_name} down toward the surrounding level",
        "fix_low": f"bring the {display_name} up toward the surrounding level",
    })


# ── What the shot contains ────────────────────────────────────────────
# Shapes the fix: the same low-motion finding is answered differently on a
# dialogue shot than on an action shot.
_SCENE_TYPE_NOTE = {
    "dialogue": "on a dialogue beat, tighten around the line rather than the movement",
    "action": "on an action beat, this is usually a coverage problem rather than a grade problem",
    "emotional": "on an emotional beat, protect the performance before the pace",
    "montage": "inside a montage, the surrounding rhythm matters more than this shot alone",
}


def compose(
    display_name: str,
    observed: float,
    reference: float | None,
    reference_label: str,
    is_high: bool,
    magnitude: float,
    phase: str,
    position_pct: float,
    scene_type: str = "",
    unit: str = "",
) -> dict[str, str]:
    """Compose problem / why / fix text from the measurement itself.

    `reference_label` names what the value was compared against -- "this
    trailer's own median" or "Horror trailers at this point" -- so the
    sentence states the basis of the judgement rather than asserting it.
    `reference` may be None when no baseline exists for that signal, in which
    case the comparison is left out rather than printed as a fabricated zero.
    """
    m = _measure_entry(display_name)
    band = band_for(magnitude)
    adverb = _BAND_ADVERB[band]
    modal = _BAND_MODAL[band]
    where = _where(position_pct)
    direction_key = "high" if is_high else "low"

    # Without a reference the sentence must not name one -- saying "than this
    # trailer's own median (0.00)" promises a comparison it then fails to show.
    if reference is None or reference <= 1e-6:
        comparison = f"({observed:.2f}{unit})"
        against = "for the surrounding cut"
    else:
        factor = observed / reference
        ratio = f", {factor:.1f}x" if (factor >= 1.15 or factor <= 0.87) else ""
        comparison = f"({observed:.2f}{unit} against {reference:.2f}{unit}{ratio})"
        against = reference_label

    noun = m["noun"]
    gap = m[direction_key]

    # Which fact leads the sentence is itself decided by the measurement, so
    # the opening words vary with the finding rather than with one axis. An
    # extreme value is led by the size of the gap; a finding sitting on a beat
    # that carries structural weight is led by where it falls; everything else
    # is led by the measurement. Leading always with position (the first
    # version of this) just moved the repetition to the first three words.
    if band == "extreme":
        problem = (
            f"{noun.capitalize()} is {adverb} {gap} {against} {where} "
            f"{comparison}."
        )
    elif phase in _STRUCTURAL_PHASES:
        problem = (
            f"{where.capitalize()}, where {_PHASE_JOB.get(phase, _PHASE_DEFAULT)}, "
            f"{noun} is {adverb} {gap} {against} {comparison}."
        )
    else:
        problem = (
            f"{noun.capitalize()} {where} is {adverb} {gap} {against} "
            f"{comparison}."
        )

    # The "why" carries whichever context the problem sentence did NOT already
    # state, so the two sentences complement each other instead of restating
    # the phase twice on structural beats.
    job = _PHASE_JOB.get(phase, _PHASE_DEFAULT)
    if phase in _STRUCTURAL_PHASES and band != "extreme":
        why = (
            f"The measurement itself is only {band}; what makes it worth a look is "
            f"that it lands on the beat carrying that job, where the audience is "
            f"most likely to feel it."
        )
    elif band == "extreme":
        why = (
            f"A gap this size stops reading as a stylistic choice — {job}, and a "
            f"departure this far from the surrounding cut pulls attention to the "
            f"edit rather than the film."
        )
    else:
        why = (
            f"This lands where {job}, so a {band} departure changes what the section "
            f"does for the audience rather than only how it measures."
        )

    fix = m[f"fix_{direction_key}"]
    note = _SCENE_TYPE_NOTE.get(str(scene_type).strip().lower())
    fix_text = f"{modal}{fix}"
    if note:
        fix_text = f"{fix_text} — {note}"
    return {
        "problem": problem,
        "why": why,
        "fix": fix_text[0].upper() + fix_text[1:] if fix_text else fix_text,
        "band": band,
    }
