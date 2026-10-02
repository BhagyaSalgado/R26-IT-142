"""Frame-level checks that the per-scene CSVs alone can't answer: is there a
logo card and is it positioned where this trailer's own structure would
expect one, is the real movie title ever shown on screen, is a release date
ever shown. All three need to actually look at the scene thumbnails.

Detection is model-driven, not hand-written pattern rules:
  - Logo presence: CLIP zero-shot (frame_vision_models.logo_probabilities_batch).
  - On-screen text: EasyOCR (frame_vision_models.read_on_screen_text) reads
    whatever is actually in the frame; matching that text against the real
    title (fetched from OMDb — ground truth, not a guess) uses difflib's
    sequence-similarity, not a keyword rule.
  - "Wrong position" is judged against THIS trailer's own structural phases
    (opening_hook / resolution), which structure_segmentation.py already
    derives from the trailer's real energy curve — not a fixed percentage.

The one piece that's necessarily deterministic rather than model-based:
recognizing that a string like "DECEMBER 25" or "12/25/2026" is shaped like
a date. That's data-format parsing, not an editorial judgment — there's no
meaningful sense in which a model should be "trained" to know what a date
looks like, the same way _detect_technical_problems() doesn't need a model
to know a timestamp range is invalid.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.frame_vision_models import logo_probabilities_batch, read_on_screen_text

_LOGO_CONFIDENCE_THRESHOLD = 0.5
_TITLE_SIMILARITY_THRESHOLD = 0.6
_MAX_OCR_CALLS = 40  # CPU OCR is the slow step; bounds worst-case runtime per trailer

_DATE_PATTERN = re.compile(
    r"\b("
    r"(JAN(UARY)?|FEB(RUARY)?|MAR(CH)?|APR(IL)?|MAY|JUNE?|JULY?|AUG(UST)?|SEPT?(EMBER)?|OCT(OBER)?|NOV(EMBER)?|DEC(EMBER)?)\.?\s+\d{1,2}(ST|ND|RD|TH)?(,?\s+\d{4})?"
    r"|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}"
    r"|\d{4}"
    r")\b",
    re.IGNORECASE,
)
_RELEASE_CUE_WORDS = ("theaters", "theatres", "cinemas", "coming soon", "in theaters", "only in", "releasing")


@dataclass
class SceneTextHit:
    scene_idx: int
    scene_id: int
    timeframe: str
    start_time: float
    end_time: float
    text: str


@dataclass
class VisualIntegrityFindings:
    frames_available: bool
    scenes_scanned: int = 0
    # Scenes actually put through OCR. Distinct from scenes_scanned: logo
    # detection sees every frame, but OCR stops at _MAX_OCR_CALLS, so a
    # "title never appears" claim is only as strong as THIS number.
    scenes_ocr_read: int = 0
    logo_hits: list[dict[str, Any]] = field(default_factory=list)
    logo_outside_expected_phase: bool = False
    title_hit: SceneTextHit | None = None
    release_date_hit: SceneTextHit | None = None
    real_title: str = ""
    real_release_date: str = ""


def _text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _title_appears_in(ocr_text: str, real_title: str) -> bool:
    if not ocr_text.strip() or not real_title.strip():
        return False
    # Whole-string similarity catches a clean title card; a sliding window
    # over OCR tokens catches a title embedded in a longer noisy OCR read
    # (e.g. a title card also showing a tagline).
    if _text_similarity(ocr_text, real_title) >= _TITLE_SIMILARITY_THRESHOLD:
        return True
    words = ocr_text.split()
    title_word_count = max(1, len(real_title.split()))
    window = max(title_word_count, 2)
    for i in range(0, max(1, len(words) - window + 1)):
        chunk = " ".join(words[i:i + window])
        if _text_similarity(chunk, real_title) >= _TITLE_SIMILARITY_THRESHOLD:
            return True
    return False


def _looks_like_release_date(ocr_text: str) -> bool:
    lower = ocr_text.lower()
    has_cue = any(cue in lower for cue in _RELEASE_CUE_WORDS)
    has_date_shape = bool(_DATE_PATTERN.search(ocr_text))
    # Require BOTH a release-framing cue and a date-shaped token so a random
    # 4-digit number (a phone number fragment, a badge number) doesn't count.
    return has_cue and has_date_shape


def detect_visual_integrity(
    scene_rows: list[dict[str, Any]],
    frames_dir: Path | None,
    real_title: str,
    real_release_date: str,
    opening_scene_idxs: set[int],
    resolution_scene_idxs: set[int],
) -> VisualIntegrityFindings:
    if frames_dir is None or not frames_dir.exists():
        return VisualIntegrityFindings(frames_available=False, real_title=real_title, real_release_date=real_release_date)

    findings = VisualIntegrityFindings(frames_available=True, real_title=real_title, real_release_date=real_release_date)

    # Scan the opening/resolution phases first — title and release-date cards
    # conventionally live there — then fall back to every remaining scene.
    # This is a scan-ORDER optimization, not a coverage limit: logo detection
    # (fast, CLIP) still covers every frame; only the OCR budget below is
    # capped, and the priority order means that cap mostly trims frames in
    # the middle of the trailer, the least likely place for either card.
    priority_idxs = [i for i in range(len(scene_rows)) if i in opening_scene_idxs or i in resolution_scene_idxs]
    rest_idxs = [i for i in range(len(scene_rows)) if i not in opening_scene_idxs and i not in resolution_scene_idxs]
    scan_order = priority_idxs + rest_idxs

    existing_paths = []
    for idx in scan_order:
        scene_id = scene_rows[idx].get("scene", idx + 1)
        p = frames_dir / f"scene_{scene_id}.jpg"
        existing_paths.append(p if p.exists() else None)

    # One batched CLIP forward pass for every frame in this trailer, instead
    # of one call each — the dominant cost on CPU is per-call overhead, not
    # image count, so this covers every frame (needed: a misplaced logo can
    # be anywhere) without paying for it per-frame.
    logo_probs = logo_probabilities_batch([p for p in existing_paths if p is not None])
    logo_prob_by_idx: dict[int, float | None] = {}
    prob_iter = iter(logo_probs)
    for idx, p in zip(scan_order, existing_paths):
        if p is not None:
            logo_prob_by_idx[idx] = next(prob_iter)

    ocr_calls = 0
    for idx, frame_path in zip(scan_order, existing_paths):
        row = scene_rows[idx]
        scene_id = row.get("scene", idx + 1)
        if frame_path is None:
            continue
        findings.scenes_scanned += 1

        timeframe = row.get("timeframe", "")
        ev = row["evidence"]

        logo_conf = logo_prob_by_idx.get(idx)
        if logo_conf is not None and logo_conf >= _LOGO_CONFIDENCE_THRESHOLD:
            findings.logo_hits.append({
                "scene_idx": idx, "scene_id": scene_id, "timeframe": timeframe,
                "start_time": ev.shot_duration, "confidence": round(logo_conf, 3),
            })

        need_title = findings.title_hit is None
        need_date = findings.release_date_hit is None and bool(real_release_date)
        if (need_title or need_date) and ocr_calls < _MAX_OCR_CALLS:
            ocr_calls += 1
            findings.scenes_ocr_read = ocr_calls
            ocr_text = read_on_screen_text(frame_path)
            if ocr_text:
                if findings.title_hit is None and _title_appears_in(ocr_text, real_title):
                    findings.title_hit = SceneTextHit(idx, scene_id, timeframe, 0.0, 0.0, ocr_text)
                if findings.release_date_hit is None and real_release_date and _looks_like_release_date(ocr_text):
                    findings.release_date_hit = SceneTextHit(idx, scene_id, timeframe, 0.0, 0.0, ocr_text)

    if findings.logo_hits:
        findings.logo_outside_expected_phase = not any(
            hit["scene_idx"] in opening_scene_idxs or hit["scene_idx"] in resolution_scene_idxs
            for hit in findings.logo_hits
        )

    return findings
