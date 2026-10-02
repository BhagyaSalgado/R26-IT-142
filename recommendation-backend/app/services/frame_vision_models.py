"""Lazy-loaded pretrained vision models for frame-level checks (logo cards,
on-screen text) that the tabular per-scene CSVs can't answer on their own.

Both models are loaded once per process and reused — mirrors how
Movie_Trailer-main's ModelManager avoids reloading CLIP per request.

CLIP (openai/clip-vit-base-patch32): the same zero-shot model already used
upstream for scene-type classification, reused here zero-shot for "is this
frame a logo card" — no fine-tuning, no labels, a real pretrained model doing
what it was pretrained to do (image/text similarity).

EasyOCR: a pretrained scene-text recognition model (CRAFT detector + CRNN
recognizer), not a hand-written text-matching rule — reads whatever text is
actually on screen.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_LOGO_PROMPTS = [
    "a studio or production company logo card on a plain background",
    "a live-action scene from a movie trailer",
]


@lru_cache(maxsize=1)
def _load_clip():
    import torch
    from transformers import CLIPModel, CLIPProcessor

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model.eval()
    return model, processor, torch


@lru_cache(maxsize=1)
def _load_ocr_reader():
    import easyocr

    return easyocr.Reader(["en"], gpu=False, verbose=False)


def logo_probabilities_batch(image_paths: list[Path]) -> list[float | None]:
    """Zero-shot CLIP probability that each frame is a logo/production card
    rather than a live trailer scene, for a whole trailer in one forward pass
    (CPU inference is dominated by per-call overhead, not FLOPs at this
    resolution — batching ~90 frames is far faster than 90 single calls).
    Returns None per-entry for any image that failed to load; [] entirely if
    CLIP itself can't be loaded."""
    if not image_paths:
        return []
    try:
        from PIL import Image

        model, processor, torch = _load_clip()
        images, valid_mask = [], []
        for p in image_paths:
            try:
                images.append(Image.open(p).convert("RGB"))
                valid_mask.append(True)
            except Exception as exc:
                logger.warning("Could not open frame %s: %s", p, exc)
                valid_mask.append(False)

        if not images:
            return [None] * len(image_paths)

        inputs = processor(text=_LOGO_PROMPTS, images=images, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)[:, 0].tolist()

        results: list[float | None] = []
        prob_iter = iter(probs)
        for ok in valid_mask:
            results.append(float(next(prob_iter)) if ok else None)
        return results
    except Exception as exc:
        logger.warning("CLIP batch logo scoring failed: %s", exc)
        return [None] * len(image_paths)


def read_on_screen_text(image_path: Path) -> str:
    """OCR every text fragment visible in the frame, joined into one string.
    Returns "" if OCR is unavailable or finds nothing — callers treat that as
    "no readable text", not an error."""
    try:
        reader = _load_ocr_reader()
        results = reader.readtext(str(image_path), detail=0)
        return " ".join(results)
    except Exception as exc:
        logger.warning("OCR failed for %s: %s", image_path, exc)
        return ""
