"""Colour-grading measurements per scene.

Why this exists: the structural features (shot length, motion, loudness,
tempo) tell Action apart from everything else, but leave Horror, Romance and
Comedy statistically indistinguishable -- measured at roughly chance in
scripts/validate_genre_norms.py. That makes sense, because all three can be
slow, moderate-energy and dialogue-driven. What actually separates them on
screen is how they are GRADED: horror is dark and desaturated, romance is warm
and golden, comedy is bright and saturated.

None of that was being measured anywhere in the pipeline, so this module adds
it. Four numbers per scene, each chosen to be simple enough to explain and
defend rather than clever:

  brightness  how light or dark the image is        (0 dark  -> 1 bright)
  saturation  how vivid or washed-out the colour is (0 grey  -> 1 vivid)
  warmth      colour temperature                    (-1 cool/blue -> +1 warm/orange)
  contrast    spread between lights and darks       (0 flat  -> 1 harsh)

Computed straight from the scene thumbnails the analysis pipeline already
saves, so no video is re-decoded and no new model is needed.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

COLOUR_DIMS = ("brightness", "saturation", "warmth", "contrast")

# Frames are 1280x720; colour statistics do not need that resolution, and
# shrinking first makes the whole corpus pass roughly 25x faster.
_SAMPLE_SIZE = (160, 90)


def colour_stats(image_path: Path) -> dict[str, float] | None:
    """Measure the four colour-grading numbers for one frame.

    Returns None if the image cannot be read, so callers can skip it rather
    than record a fabricated zero.
    """
    try:
        from PIL import Image

        with Image.open(image_path) as im:
            im = im.convert("RGB").resize(_SAMPLE_SIZE)
            arr = np.asarray(im, dtype=np.float32) / 255.0
    except Exception as exc:
        logger.warning("Could not read frame %s: %s", image_path, exc)
        return None

    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

    # Perceived brightness. The green coefficient is largest because human
    # vision is most sensitive to green -- a plain (r+g+b)/3 would call a
    # saturated blue frame far brighter than it looks.
    luma = 0.299 * r + 0.587 * g + 0.114 * b

    # Saturation as used in HSV: how far the strongest and weakest channels
    # are apart. Equal channels = grey = 0.
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    saturation = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)

    # Warmth: red-vs-blue balance. Teal-and-orange grading, the dominant look
    # in modern trailers, lives almost entirely on this axis.
    warmth = (r - b) / np.maximum(r + b, 1e-6)

    return {
        "brightness": float(luma.mean()),
        "saturation": float(saturation.mean()),
        "warmth": float(warmth.mean()),
        # Standard deviation of brightness: a flatly-lit comedy scene scores
        # low, a horror scene of bright faces against blackness scores high.
        "contrast": float(luma.std()),
    }


def scene_colour_series(frames_dir: Path, scene_ids: list[int]) -> dict[str, list[float]] | None:
    """Measure every scene of one trailer, in order.

    Missing frames carry the previous scene's values forward rather than
    breaking the series, because the curve has to stay aligned with the scene
    list for the norm comparison to line up. Returns None if no frame at all
    could be read.
    """
    if not frames_dir.exists():
        return None

    series: dict[str, list[float]] = {dim: [] for dim in COLOUR_DIMS}
    last: dict[str, float] | None = None
    found = 0

    for scene_id in scene_ids:
        stats = colour_stats(frames_dir / f"scene_{scene_id}.jpg")
        if stats is None:
            stats = last if last is not None else {d: 0.0 for d in COLOUR_DIMS}
        else:
            last = stats
            found += 1
        for dim in COLOUR_DIMS:
            series[dim].append(stats[dim])

    return series if found else None
