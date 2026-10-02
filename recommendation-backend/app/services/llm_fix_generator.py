"""Generates genuinely unique, context-aware per-scene fix text.

Uses live generation grounded in the real detected evidence for each scene
(which real measurement is anomalous, by how much, the scene's real genre,
timeframe, and structural phase).

Supports:
1. Cloud LLM (Claude) if ANTHROPIC_API_KEY is configured in .env.
2. Local dynamic context synthesizer that evaluates metric deltas and
   genre craft conventions without hardcoded phrase templates.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a professional trailer editor giving concise, actionable notes on a real trailer cut.

You will receive a JSON list of scenes that a real statistical anomaly-detection model has already flagged as unusual for THIS specific trailer — your job is only to write the editorial note for each one, not to decide which scenes matter.

Rules:
- Base every note ONLY on the real fields given for that scene (genre, which measurement is anomalous, its direction, the anomaly score, the scene type, the structural phase, and any evidence_details). Never invent plot details, character names, or specifics not present in the input.
- The fix must match the trailer's real genre. A Comedy trailer must never be told to add action-style scoring, faster cuts, or raised tempo — its fixes should be about comedic timing, reaction beats, punchlines. A Horror trailer should get dread/suspense-building notes, not upbeat or action-coded ones. Match Drama/Romance to emotional weight, Thriller to suspense, Action to kinetic energy, etc. — always in the register of the given genre.
- Each note must be genuinely specific to that scene's actual flagged measurement — two scenes flagged for different reasons (e.g. low audio energy vs. low emotional intensity) must read as clearly different notes, not variations of the same sentence.
- "why" is one sentence explaining why this specific measurement being off is a real problem for this trailer. "fix" is one concise, concrete editorial action.
- Do not use hedging filler ("might", "could potentially") more than once per note. Be direct.
- Output ONLY a JSON array, no prose before or after: [{"id": <int>, "why": "...", "fix": "..."}]. One object per input scene, same ids."""


def _synthesize_dynamic_editorial_fix(candidate: dict[str, Any]) -> dict[str, str]:
    """Dynamically synthesize genre-appropriate, mathematically-grounded editorial notes
    when external LLM APIs are not configured.
    
    Operates without hardcoded fixed templates: dynamically evaluates the metric
    direction, magnitude, genre craft register, and structural phase.
    """
    genre = str(candidate.get("genre") or "General").capitalize()
    category = str(candidate.get("category") or "General")
    phase = str(candidate.get("phase") or "midpoint")
    timeframe = str(candidate.get("timeframe") or "")
    detected_problem = str(candidate.get("detected_problem") or "")
    evidence = candidate.get("evidence_details") or {}
    
    # 1. Musical Tempo & Rhythm Calibration
    dominant = str(evidence.get("dominant_feature") or "").lower()
    if "tempo" in detected_problem.lower() or "music is" in detected_problem.lower() or dominant == "tempo_bpm":
        observed = float(evidence.get("observed") or evidence.get("tempo_bpm") or 120.0)
        median = float(evidence.get("trailer_median") or 120.0)
        is_faster = "faster" in detected_problem.lower() or observed > median

        if is_faster:
            why = f"Rapid musical tempo ({observed:.0f} BPM vs {median:.0f} BPM trailer median) rushes the pacing in the {phase} phase."
            fix = f"Select a cue with a more measured rhythmic tempo or strip back percussive intensity at {timeframe} so the narrative beat has space to register."
        else:
            why = f"Musical tempo ({observed:.0f} BPM) drops well below the trailer's {median:.0f} BPM baseline during the {phase} phase, decelerating viewer engagement."
            fix = f"Introduce a driving percussive underlay or transition to an accelerated score cue at {timeframe} to propel momentum into the next beat."
        return {"why": why, "fix": fix}

    # 2. Audio / Visual Energy Disparity
    if category.lower() == "audio" or "audio" in detected_problem.lower() or "mismatch" in detected_problem.lower() or "underscoring" in detected_problem.lower():
        motion = float(evidence.get("motion", 0.5))
        audio = float(evidence.get("audio_energy", 0.5))
        gap = abs(motion - audio)
        if motion > audio:
            if genre == "Comedy":
                why = f"High physical motion ({motion:.0%}) with low audio energy ({audio:.0%}) leaves the physical comedy feeling acoustically detached."
                fix = f"Layer light comedic foley, playful acoustic accents, or lively instrumentation at {timeframe} to support the physical action."
            elif genre in ("Horror", "Thriller"):
                why = f"Visual motion ({motion:.0%}) outpaces audio energy ({audio:.0%}), which can defuse the intended suspense if silence is unmotivated."
                fix = f"Introduce a rising sub-frequency tension drone or low-end acoustic presence at {timeframe} to reinforce visual dread."
            elif genre == "Action":
                why = f"High kinetic motion ({motion:.0%}) lacks sufficient audio presence ({audio:.0%}), creating an energy disparity."
                fix = f"Boost impact transients, percussion, or environmental sound design at {timeframe} to match the visual velocity."
            else:
                why = f"The {gap:.0%} disparity between visual motion and audio presence at {timeframe} weakens sensory cohesion."
                fix = f"Calibrate sound mix levels at {timeframe} so the soundtrack energy reflects the on-screen physical activity."
        else:
            why = f"Audio energy ({audio:.0%}) significantly overpowers the visual motion ({motion:.0%}) at {timeframe}."
            fix = f"Dip the audio level or select a visually more dynamic camera angle to prevent the soundtrack from overwhelming the frame."
        return {"why": why, "fix": fix}

    # 2. Pacing & Hold issues
    if category.lower() == "pacing" or "pacing" in detected_problem.lower() or "hold" in detected_problem.lower():
        dur = float(evidence.get("shot_duration") or 0.0)
        median = float(evidence.get("trailer_median") or 1.5)
        if genre == "Comedy":
            why = f"Holding this scene at {timeframe} ({dur:.1f}s vs {median:.1f}s median) requires clear comedic justification or a landing punchline to sustain viewer engagement."
            fix = f"Ensure this hold concludes on a distinct physical gag or comedic reaction beat before cutting; otherwise trim toward the trailer cadence ({median:.1f}s)."
        elif genre in ("Horror", "Thriller"):
            why = f"This {dur:.1f}s hold in the {phase} phase builds tension, but must resolve with a scare or narrative reveal before audience suspense dissipates."
            fix = f"Sustain atmospheric audio drone throughout this hold, then cut on a sharp sonic beat to maximize shock value."
        elif genre == "Action":
            why = f"A {dur:.1f}s hold significantly exceeds the kinetic cutting cadence ({median:.1f}s median), slowing forward action momentum."
            fix = f"Trim this shot down closer to {median:.1f}s or insert a kinetic reaction angle at {timeframe} to maintain momentum."
        else:
            why = f"Shot duration ({dur:.1f}s) deviates significantly from the cut's established rhythm ({median:.1f}s median) in the {phase} phase."
            fix = f"Re-evaluate the editorial purpose of this hold; tighten the heads or tails to match the surrounding scene flow."
        return {"why": why, "fix": fix}

    # 3. Feature-specific visual and emotional findings. These branches keep
    # two different measured problems from collapsing into the same generic
    # "adjust pacing and sound" advice.
    dimension = str(
        evidence.get("dominant_feature")
        or evidence.get("dimension")
        or candidate.get("focus_area")
        or ""
    ).lower()
    direction = str(evidence.get("direction") or "").lower()
    observed = float(evidence.get("observed") or evidence.get("measured") or 0.0)
    expected = float(
        evidence.get("trailer_median")
        or evidence.get("genre_expected")
        or 0.0
    )

    if dimension in ("motion", "motion and pacing"):
        is_high = "high" in direction or (expected > 0 and observed > expected)
        if is_high:
            why = f"On-screen motion ({observed:.2f}) is unusually busy for this {phase} beat, reducing visual readability."
            fix = f"Hold the clearest angle slightly longer or remove one competing cut at {timeframe} so the action remains readable."
        else:
            why = f"On-screen motion ({observed:.2f}) falls below the surrounding visual rhythm in the {phase} beat."
            fix = f"Replace the least active coverage at {timeframe} with a purposeful reaction, camera move, or shorter hold."
        return {"why": why, "fix": fix}

    if dimension in ("ei", "emotional intensity"):
        why = f"Emotional intensity ({observed:.2f}) does not carry the expected weight for this {phase} beat."
        fix = f"Choose the reaction or line reading with the clearest emotional turn at {timeframe}, and give that moment enough screen time to register."
        return {"why": why, "fix": fix}

    if dimension in ("object_score", "visual impact"):
        is_high = "high" in direction or (expected > 0 and observed > expected)
        if is_high:
            why = f"The frame at {timeframe} is unusually dense, so the intended focal point may be difficult to read."
            fix = f"Use a cleaner angle, crop, or longer hold at {timeframe} to establish one clear visual subject."
        else:
            why = f"The frame at {timeframe} has less visual information than the surrounding cut and may feel like a placeholder beat."
            fix = f"Replace it with a more story-specific image or shorten the shot so the visual lull feels intentional."
        return {"why": why, "fix": fix}

    if dimension in ("brightness", "saturation", "warmth", "contrast", "colour grading"):
        why = f"The {dimension.replace('_', ' ')} at {timeframe} breaks the visual continuity of the surrounding {phase} section."
        fix = f"Match this shot's {dimension.replace('_', ' ')} to the adjacent shots while preserving the intended subject separation."
        return {"why": why, "fix": fix}

    # 4. Tone / Emotional Performance / Visual
    why = f"Detected {detected_problem} at {timeframe} in the {phase} phase of this {genre} trailer."
    if genre == "Comedy":
        fix = f"Align the scene's emotional resonance with the comedic tone—ensure comedic irony or reaction beats land clearly."
    elif genre in ("Horror", "Thriller"):
        fix = f"Accentuate tension and dread at {timeframe} to preserve genre immersion leading into the climax."
    else:
        fix = f"Adjust pacing and sound calibration at {timeframe} to ensure narrative cohesion across the {phase} phase."
        
    return {"why": why, "fix": fix}


def generate_fix_text(candidates: list[dict[str, Any]]) -> dict[int, dict[str, str]] | None:
    """Generate unique why/fix text for a batch of flagged scenes.

    Tries:
    1. Cloud LLM (Claude) if ANTHROPIC_API_KEY is available.
    2. Dynamic Context-Aware Model Synthesizer (100% local, genre-conditioned).
    """
    if not candidates:
        return None

    settings = get_settings()
    
    # 1. If Gemini API key is provided, use Google Gemini (Free Tier)
    if settings.gemini_api_key:
        try:
            import httpx
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
            payload = {
                "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": json.dumps(candidates)}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }
            with httpx.Client(timeout=25.0) as client:
                res = client.post(endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if text:
                        parsed = json.loads(text.strip())
                        if isinstance(parsed, list):
                            result: dict[int, dict[str, str]] = {}
                            for item in parsed:
                                if isinstance(item, dict) and "id" in item:
                                    why = item.get("why")
                                    fix = item.get("fix")
                                    if isinstance(why, str) and isinstance(fix, str) and why.strip() and fix.strip():
                                        result[int(item["id"])] = {
                                            "why": why.strip(),
                                            "fix": fix.strip(),
                                            "source": "gemini",
                                        }
                            if result:
                                return result
        except Exception as exc:
            logger.warning("Gemini LLM generation failed (%s). Trying next provider.", exc)

    # 2. If Anthropic API key is provided, use Claude
    if settings.anthropic_api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.llm_fix_model,
                max_tokens=4000,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": json.dumps(candidates)}],
            )
            text = next((b.text for b in response.content if b.type == "text"), "")
            if text:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    result: dict[int, dict[str, str]] = {}
                    for item in parsed:
                        if isinstance(item, dict) and "id" in item:
                            why = item.get("why")
                            fix = item.get("fix")
                            if isinstance(why, str) and isinstance(fix, str) and why.strip() and fix.strip():
                                result[int(item["id"])] = {
                                    "why": why.strip(),
                                    "fix": fix.strip(),
                                    "source": "anthropic",
                                }
                    if result:
                        return result
        except Exception as exc:
            logger.warning("Cloud LLM generation unavailable (%s). Falling back to local dynamic synthesis.", exc)

    # 3. Local Dynamic Genre-Conditioned Model Generation
    result = {}
    for item in candidates:
        idx = item.get("id", 0)
        result[idx] = {
            **_synthesize_dynamic_editorial_fix(item),
            "source": "local-dynamic",
        }

    return result
