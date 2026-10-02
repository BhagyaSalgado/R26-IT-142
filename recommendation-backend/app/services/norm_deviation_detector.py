"""Finds problems by comparing a trailer against its genre's learned norm.

This is the detector that replaces hand-written genre knowledge. The old
approach needed rules typed into Python ("Horror holds long shots, don't flag
them"); here that knowledge is measured -- if real Horror trailers hold long
shots, the Horror norm says so, and a long shot in a Horror trailer simply
does not deviate.

It also fixes a blind spot the per-trailer detector cannot cover: a trailer
whose pacing is uniformly wrong contains no internal outlier, so comparing it
to itself finds nothing. Comparing it to its genre finds the whole curve
sitting away from the norm.

The fix text is generated from the measurement itself -- the observed value,
the genre's expected value, and the gap between them. The sentence pattern is
shared across every genre; only the numbers differ. That is the important
distinction from the old phrase table, which stored different hand-written
prose per genre and so encoded a person's opinion about each genre.

Reports nothing at all for a genre with no norm, rather than falling back to
something weaker and presenting it as the same thing.
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any

from app.services.genre_norm import (
    Deviation,
    GenreNorm,
    load_norms,
    profile_from_scene_rows,
    score_profile,
)

logger = logging.getLogger(__name__)

NORMS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "genre_norms"

# How each measurement is described to an editor, and what a fix looks like in
# each direction. Note what this is NOT: it holds no genre knowledge. The same
# entry serves Horror and Comedy -- what differs between them is the number
# the norm supplies, not the wording stored here.
_DIM_LANGUAGE: dict[str, dict[str, str]] = {
    "shot_duration": {
        "label": "shot length", "unit": "s",
        "above": "shots here are held much longer than this genre normally holds them",
        "below": "shots here are cut much faster than this genre normally cuts",
        "fix_above": "tighten this run toward ~{expected:.1f}s per shot",
        "fix_below": "let these shots breathe toward ~{expected:.1f}s each",
    },
    "ei": {
        "label": "emotional intensity", "unit": "",
        "above": "emotional intensity here runs well above the genre norm",
        "below": "emotional intensity here falls well below the genre norm",
        "fix_above": "consider whether this peak arrives too early and undercuts the climax",
        "fix_below": "raise the emotional charge here toward the genre's typical {expected:.2f}",
    },
    "audio_energy": {
        "label": "audio energy", "unit": "",
        "above": "the mix is much louder here than this genre typically runs",
        "below": "the mix is much quieter here than this genre typically runs",
        "fix_above": "pull the level back toward the genre's typical {expected:.2f}",
        "fix_below": "lift the level toward the genre's typical {expected:.2f}",
    },
    "motion": {
        "label": "on-screen motion", "unit": "",
        "above": "there is far more movement here than the genre normally carries",
        "below": "there is far less movement here than the genre normally carries",
        "fix_above": "check this section is not busier than the story needs",
        "fix_below": "add movement or cut to more kinetic coverage here",
    },
    "tempo_bpm": {
        "label": "musical tempo", "unit": " BPM",
        "above": "the music runs faster here than the genre typically scores",
        "below": "the music runs slower here than the genre typically scores",
        "fix_above": "ease the tempo toward the genre's typical {expected:.0f} BPM",
        "fix_below": "lift the tempo toward the genre's typical {expected:.0f} BPM",
    },
    "brightness": {
        "label": "brightness", "unit": "",
        "above": "this section is graded far brighter than the genre normally sits",
        "below": "this section is graded far darker than the genre normally sits",
        "fix_above": "bring the exposure down toward the genre's typical {expected:.2f}",
        "fix_below": "lift the exposure toward the genre's typical {expected:.2f}",
    },
    "saturation": {
        "label": "colour saturation", "unit": "",
        "above": "colour here is far more vivid than the genre normally grades",
        "below": "colour here is far flatter than the genre normally grades",
        "fix_above": "desaturate toward the genre's typical {expected:.2f}",
        "fix_below": "add saturation toward the genre's typical {expected:.2f}",
    },
    "warmth": {
        "label": "colour temperature", "unit": "",
        "above": "the grade here is much warmer than this genre usually runs",
        "below": "the grade here is much cooler than this genre usually runs",
        "fix_above": "cool the grade toward the genre's typical {expected:+.2f}",
        "fix_below": "warm the grade toward the genre's typical {expected:+.2f}",
    },
    "contrast": {
        "label": "contrast", "unit": "",
        "above": "contrast here is far harsher than the genre normally grades",
        "below": "contrast here is far flatter than the genre normally grades",
        "fix_above": "soften the contrast toward the genre's typical {expected:.2f}",
        "fix_below": "lift the contrast toward the genre's typical {expected:.2f}",
    },
}

_FOCUS_AREA = {
    "shot_duration": "pacing", "ei": "emotional intensity", "audio_energy": "audio",
    "motion": "motion", "tempo_bpm": "audio", "brightness": "colour grading",
    "saturation": "colour grading", "warmth": "colour grading", "contrast": "colour grading",
}
_CATEGORY = {
    "shot_duration": "Pacing", "ei": "Visual", "audio_energy": "Audio",
    "motion": "Visual", "tempo_bpm": "Audio", "brightness": "Visual",
    "saturation": "Visual", "warmth": "Visual", "contrast": "Visual",
}


# Which scene-row field backs each curve dimension, for the flatness check.
# Only dimensions read straight off a per-scene column can be checked this way;
# the rest are derived and genuinely vary.
_DIM_SOURCE_ATTR = {
    "tempo_bpm": "tempo_bpm",
    "audio_energy": "audio_energy",
    "motion": "motion",
    "ei": "ei",
}


def _flat_dimensions(scene_rows: list[dict[str, Any]]) -> set[str]:
    """Dimensions whose value barely changes from scene to scene.

    A signal that is constant across the trailer carries no per-scene
    information, so any per-scene finding drawn from it is an artefact of how
    it was measured rather than something an editor could act on.
    """
    flat: set[str] = set()
    for dim, attr in _DIM_SOURCE_ATTR.items():
        values = []
        for row in scene_rows:
            ev = row.get("evidence")
            val = getattr(ev, attr, None) if ev is not None else None
            if isinstance(val, (int, float)):
                values.append(round(float(val), 3))
        if len(values) < 8:
            continue
        share = max(Counter(values).values()) / len(values)
        if len(set(values)) < 4 or share > 0.80:
            flat.add(dim)
    return flat


def _load() -> dict[str, GenreNorm]:
    return load_norms(NORMS_DIR)


def available_genres() -> list[str]:
    return sorted(_load().keys())


def describe(dev: Deviation, norm: GenreNorm) -> dict[str, str]:
    """Turn one measured deviation into problem / why / fix sentences.

    Every number in the output is measured: what this trailer does, what the
    genre does, how many trailers that expectation rests on.
    """
    lang = _DIM_LANGUAGE.get(dev.dimension)
    if lang is None:
        return {}
    direction = "above" if dev.z > 0 else "below"
    unit = lang["unit"]

    ratio = ""
    if dev.expected > 1e-6 and dev.dimension in ("shot_duration", "tempo_bpm"):
        factor = dev.observed / dev.expected
        if factor >= 1.15 or factor <= 0.87:
            ratio = f" ({factor:.1f}x the genre norm)"

    problem = (
        f"{lang['label'].capitalize()} here is {dev.observed:.2f}{unit}; "
        f"{norm.genre} trailers at this point average {dev.expected:.2f}{unit}"
        f" (n={norm.n_trailers}, sd {dev.expected_std:.2f}){ratio}."
    )
    why = (
        f"At this point in the trailer, {lang[direction]} "
        f"— {abs(dev.z):.1f} standard deviations from what {norm.n_trailers} real "
        f"{norm.genre} trailers do."
    )
    fix = lang[f"fix_{direction}"].format(expected=dev.expected)
    return {"problem": problem, "why": fix_capitalise(fix), "fix": fix_capitalise(fix), "why_text": why}


def fix_capitalise(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


def detect_norm_deviations(
    scene_rows: list[dict[str, Any]],
    genre: str,
    colour_series: dict[str, list[float]] | None = None,
    z_threshold: float = 2.0,
    max_findings: int = 12,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compare this trailer to its genre norm.

    Returns (findings, meta). `meta` always explains what happened -- including
    "no norm exists for this genre" -- so the caller can report that honestly
    instead of silently producing nothing.
    """
    norms = _load()
    norm = norms.get(genre.title()) if genre else None
    if norm is None:
        return [], {
            "norm_available": False,
            "genre": genre,
            "available_genres": sorted(norms.keys()),
            "note": f"No learned norm for '{genre}'. Norm-based checks skipped.",
        }

    profile = profile_from_scene_rows(scene_rows, colour_series, norm.bins)
    if profile is None:
        return [], {"norm_available": False, "genre": genre, "note": "Could not profile this trailer."}

    deviations, scalars = score_profile(profile, norm, z_threshold)

    # Drop dimensions that are not really measured per scene in this trailer.
    # Tempo is the case that matters: it is estimated once per track and copied
    # onto every scene row (118 of 127 scenes in one trailer carried an
    # identical BPM), so a "the music is faster here" finding describes the
    # estimator, not the cut. Comparing a global constant against a per-bin
    # genre curve produces a confident number with nothing behind it.
    flat = _flat_dimensions(scene_rows)
    if flat:
        deviations = [d for d in deviations if d.dimension not in flat]
    total = float(profile["_scalar"][0])

    findings: list[dict[str, Any]] = []
    for dev in deviations[:max_findings]:
        text = describe(dev, norm)
        if not text:
            continue
        # Map the normalised bin back to the real scene it covers, so the
        # editor gets a scene number rather than an abstract position.
        scene_idx = min(
            range(len(scene_rows)),
            key=lambda i: abs(((i + 0.5) / max(len(scene_rows), 1)) - ((dev.bin_index + 0.5) / norm.bins)),
        )
        findings.append({
            "scene_idx": scene_idx,
            "scene_id": scene_rows[scene_idx].get("scene", scene_idx + 1),
            "timeframe": f"{int(dev.start_time // 60):02d}:{dev.start_time % 60:05.2f}-{int(dev.end_time // 60):02d}:{dev.end_time % 60:05.2f}",
            "start_time": dev.start_time,
            "end_time": dev.end_time,
            "dimension": dev.dimension,
            "focus_area": _FOCUS_AREA.get(dev.dimension, "pacing"),
            "category": _CATEGORY.get(dev.dimension, "Visual"),
            "problem": text["problem"],
            "why": text["why_text"],
            "fix": text["fix"],
            "z": dev.z,
            "observed": dev.observed,
            "expected": dev.expected,
            "expected_std": dev.expected_std,
            # Confidence rises with how far from the norm it sits, capped so a
            # single wild outlier never reads as certainty.
            "confidence": round(min(0.95, 0.45 + 0.12 * abs(dev.z)), 4),
            "severity_score": round(min(0.95, 0.30 + 0.13 * abs(dev.z)), 4),
        })

    meta = {
        "norm_available": True,
        "genre": norm.genre,
        "norm_trailers": norm.n_trailers,
        "norm_reliable": norm.reliable,
        "colour_measured": bool(float(profile["_has_colour"][0]) >= 1.0),
        "total_duration": round(total, 2),
        "scalar_comparison": scalars,
        "deviations_found": len(deviations),
    }
    return findings, meta
