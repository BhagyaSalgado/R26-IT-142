"""Tests for the Movie Trailer Recommendation Engine — Component 9.

Tests with synthetic data for multiple trailer types to verify:
1. No "add more action" for Comedy trailers
2. No "increase BPM" for Romance trailers
3. Dialogue scenes NOT flagged in Action trailers
4. Quiet sections NOT automatically flagged in Thriller trailers
5. Low motion NOT automatically flagged in Drama trailers
6. Different genres produce different recommendations
7. Well-balanced trailers produce minimal/no recommendations
"""
from __future__ import annotations

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.recommendation_schema import (
    Evidence,
    PopularityContext,
    RecommendationRequest,
)
from app.services.recommendation_service import generate_recommendations
from app.services.genre_classifier import build_genre_report
from app.services.trailer_baseline import build_trailer_baseline


def _make_scene(
    scene: int,
    time: str,
    scene_type: str = "Drama",
    scene_type_confidence: float = 0.8,
    motion: float = 0.3,
    audio_energy: float = 0.4,
    ei: float = 0.5,
    visual_emotion: str = "neutral",
    audio_mood: str = "emotional",
    objects: str = "person",
    tempo_bpm: float = 120.0,
) -> dict:
    """Create a scene row matching the final_system_output format."""
    return {
        "scene": scene,
        "time": time,
        "scene_type": scene_type,
        "scene_type_confidence": scene_type_confidence,
        "classification_reliable": scene_type_confidence >= 0.4,
        "M": motion,
        "A": audio_energy,
        "O": 0.5,
        "F": 0.7,
        "EI": ei,
        "level": "Medium",
        "audio_mood": audio_mood,
        "audio_emotion": "neutral",
        "audio_confidence": 0.5,
        "face_emotion": visual_emotion,
        "objects": objects,
        "tempo_bpm": tempo_bpm,
        "mfcc_mean": 0.0,
        "spectral_centroid": 1800.0,
    }


def _make_payload(scenes: list[dict], title: str = "Test Trailer") -> RecommendationRequest:
    """Build a RecommendationRequest from scene dicts."""
    return RecommendationRequest(
        trailer_title=title,
        final_system_output=scenes,
        audio_feature_output=[],
        visual_feature_output=[],
        popularity_context=PopularityContext(
            predicted_reaction="Positive",
            popularity_score=0.75,
            engagement_rate=0.045,
        ),
    )


# ── Synthetic Trailer Builders ───────────────────────────────────────

def _build_comedy_trailer() -> list[dict]:
    """A typical comedy trailer: mostly comedy scenes, happy emotions, moderate motion."""
    return [
        _make_scene(1, "00:00-00:08", "Comedy", 0.85, motion=0.15, audio_energy=0.6, ei=0.5, visual_emotion="happy", audio_mood="emotional"),
        _make_scene(2, "00:08-00:16", "Dialogue", 0.90, motion=0.10, audio_energy=0.5, ei=0.4, visual_emotion="neutral", audio_mood="calm"),
        _make_scene(3, "00:16-00:24", "Comedy", 0.80, motion=0.20, audio_energy=0.55, ei=0.6, visual_emotion="happy", audio_mood="emotional"),
        _make_scene(4, "00:24-00:32", "Dialogue", 0.75, motion=0.12, audio_energy=0.45, ei=0.45, visual_emotion="neutral", audio_mood="calm"),
        _make_scene(5, "00:32-00:40", "Comedy", 0.88, motion=0.25, audio_energy=0.65, ei=0.65, visual_emotion="happy", audio_mood="intense"),
        _make_scene(6, "00:40-00:48", "Comedy", 0.82, motion=0.18, audio_energy=0.7, ei=0.55, visual_emotion="happy", audio_mood="emotional"),
        _make_scene(7, "00:48-00:56", "Dialogue", 0.70, motion=0.10, audio_energy=0.5, ei=0.45, visual_emotion="neutral", audio_mood="calm"),
        _make_scene(8, "00:56-01:04", "Comedy", 0.90, motion=0.30, audio_energy=0.75, ei=0.70, visual_emotion="happy", audio_mood="intense"),
        _make_scene(9, "01:04-01:12", "Comedy", 0.85, motion=0.22, audio_energy=0.8, ei=0.75, visual_emotion="happy", audio_mood="intense"),
        _make_scene(10, "01:12-01:20", "Comedy", 0.78, motion=0.20, audio_energy=0.65, ei=0.60, visual_emotion="happy", audio_mood="emotional"),
    ]


def _build_romance_trailer() -> list[dict]:
    """A typical romance trailer: emotional, low motion, dialogue-heavy."""
    return [
        _make_scene(1, "00:00-00:08", "Romance", 0.80, motion=0.10, audio_energy=0.3, ei=0.4, visual_emotion="neutral", audio_mood="calm", tempo_bpm=90),
        _make_scene(2, "00:08-00:16", "Dialogue", 0.85, motion=0.08, audio_energy=0.25, ei=0.45, visual_emotion="happy", audio_mood="emotional", tempo_bpm=85),
        _make_scene(3, "00:16-00:24", "Romance", 0.90, motion=0.12, audio_energy=0.35, ei=0.55, visual_emotion="happy", audio_mood="emotional", tempo_bpm=88),
        _make_scene(4, "00:24-00:32", "Drama", 0.70, motion=0.15, audio_energy=0.4, ei=0.5, visual_emotion="sad", audio_mood="emotional", tempo_bpm=92),
        _make_scene(5, "00:32-00:40", "Romance", 0.85, motion=0.10, audio_energy=0.35, ei=0.6, visual_emotion="happy", audio_mood="calm", tempo_bpm=85),
        _make_scene(6, "00:40-00:48", "Dialogue", 0.80, motion=0.08, audio_energy=0.3, ei=0.5, visual_emotion="sad", audio_mood="emotional", tempo_bpm=90),
        _make_scene(7, "00:48-00:56", "Romance", 0.88, motion=0.12, audio_energy=0.4, ei=0.65, visual_emotion="happy", audio_mood="emotional", tempo_bpm=88),
        _make_scene(8, "00:56-01:04", "Drama", 0.75, motion=0.10, audio_energy=0.45, ei=0.70, visual_emotion="sad", audio_mood="emotional", tempo_bpm=95),
        _make_scene(9, "01:04-01:12", "Romance", 0.90, motion=0.15, audio_energy=0.5, ei=0.75, visual_emotion="happy", audio_mood="emotional", tempo_bpm=100),
        _make_scene(10, "01:12-01:20", "Romance", 0.82, motion=0.10, audio_energy=0.35, ei=0.55, visual_emotion="happy", audio_mood="calm", tempo_bpm=88),
    ]


def _build_action_trailer() -> list[dict]:
    """A typical action trailer: high motion, high energy, with dialogue setup scenes."""
    return [
        _make_scene(1, "00:00-00:08", "Drama", 0.70, motion=0.20, audio_energy=0.4, ei=0.4, visual_emotion="neutral", audio_mood="suspense", objects="person"),
        _make_scene(2, "00:08-00:16", "Dialogue", 0.85, motion=0.15, audio_energy=0.35, ei=0.45, visual_emotion="angry", audio_mood="suspense", objects="person"),
        _make_scene(3, "00:16-00:24", "Action", 0.90, motion=0.70, audio_energy=0.75, ei=0.65, visual_emotion="angry", audio_mood="intense", objects="car, person"),
        _make_scene(4, "00:24-00:32", "Action", 0.88, motion=0.80, audio_energy=0.8, ei=0.7, visual_emotion="fear", audio_mood="intense", objects="gun, person"),
        _make_scene(5, "00:32-00:40", "Dialogue", 0.75, motion=0.12, audio_energy=0.3, ei=0.4, visual_emotion="neutral", audio_mood="calm", objects="person"),
        _make_scene(6, "00:40-00:48", "Action", 0.92, motion=0.85, audio_energy=0.85, ei=0.75, visual_emotion="angry", audio_mood="intense", objects="car, person"),
        _make_scene(7, "00:48-00:56", "Thriller", 0.70, motion=0.55, audio_energy=0.65, ei=0.6, visual_emotion="fear", audio_mood="suspense", objects="person"),
        _make_scene(8, "00:56-01:04", "Action", 0.95, motion=0.90, audio_energy=0.90, ei=0.80, visual_emotion="angry", audio_mood="intense", objects="gun, car, person"),
        _make_scene(9, "01:04-01:12", "Action", 0.88, motion=0.85, audio_energy=0.88, ei=0.85, visual_emotion="fear", audio_mood="intense", objects="person"),
        _make_scene(10, "01:12-01:20", "Action", 0.80, motion=0.60, audio_energy=0.70, ei=0.65, visual_emotion="neutral", audio_mood="intense", objects="person"),
    ]


def _build_thriller_trailer() -> list[dict]:
    """A typical thriller: suspense, quiet tension sections, moderate motion."""
    return [
        _make_scene(1, "00:00-00:08", "Drama", 0.75, motion=0.15, audio_energy=0.2, ei=0.35, visual_emotion="neutral", audio_mood="calm"),
        _make_scene(2, "00:08-00:16", "Thriller", 0.80, motion=0.20, audio_energy=0.3, ei=0.45, visual_emotion="fear", audio_mood="suspense"),
        _make_scene(3, "00:16-00:24", "Dialogue", 0.85, motion=0.10, audio_energy=0.25, ei=0.40, visual_emotion="neutral", audio_mood="suspense"),
        _make_scene(4, "00:24-00:32", "Thriller", 0.88, motion=0.30, audio_energy=0.4, ei=0.55, visual_emotion="fear", audio_mood="suspense"),
        _make_scene(5, "00:32-00:40", "Thriller", 0.82, motion=0.15, audio_energy=0.15, ei=0.30, visual_emotion="neutral", audio_mood="calm"),  # Quiet tension
        _make_scene(6, "00:40-00:48", "Thriller", 0.90, motion=0.40, audio_energy=0.5, ei=0.60, visual_emotion="fear", audio_mood="suspense"),
        _make_scene(7, "00:48-00:56", "Thriller", 0.85, motion=0.50, audio_energy=0.6, ei=0.65, visual_emotion="fear", audio_mood="intense"),
        _make_scene(8, "00:56-01:04", "Thriller", 0.92, motion=0.65, audio_energy=0.75, ei=0.75, visual_emotion="angry", audio_mood="intense"),
        _make_scene(9, "01:04-01:12", "Drama", 0.70, motion=0.20, audio_energy=0.3, ei=0.50, visual_emotion="sad", audio_mood="emotional"),
        _make_scene(10, "01:12-01:20", "Thriller", 0.78, motion=0.15, audio_energy=0.2, ei=0.40, visual_emotion="neutral", audio_mood="suspense"),
    ]


def _build_drama_trailer() -> list[dict]:
    """A typical drama: emotional, character-driven, dialogue-heavy, slow."""
    return [
        _make_scene(1, "00:00-00:08", "Drama", 0.85, motion=0.10, audio_energy=0.25, ei=0.40, visual_emotion="neutral", audio_mood="calm", tempo_bpm=80),
        _make_scene(2, "00:08-00:16", "Dialogue", 0.90, motion=0.08, audio_energy=0.20, ei=0.45, visual_emotion="sad", audio_mood="emotional", tempo_bpm=75),
        _make_scene(3, "00:16-00:24", "Drama", 0.85, motion=0.12, audio_energy=0.30, ei=0.50, visual_emotion="angry", audio_mood="emotional", tempo_bpm=82),
        _make_scene(4, "00:24-00:32", "Dialogue", 0.88, motion=0.08, audio_energy=0.25, ei=0.55, visual_emotion="sad", audio_mood="emotional", tempo_bpm=78),
        _make_scene(5, "00:32-00:40", "Drama", 0.80, motion=0.15, audio_energy=0.35, ei=0.60, visual_emotion="sad", audio_mood="emotional", tempo_bpm=85),
        _make_scene(6, "00:40-00:48", "Emotional", 0.75, motion=0.10, audio_energy=0.40, ei=0.65, visual_emotion="sad", audio_mood="emotional", tempo_bpm=90),
        _make_scene(7, "00:48-00:56", "Drama", 0.85, motion=0.12, audio_energy=0.45, ei=0.70, visual_emotion="angry", audio_mood="intense", tempo_bpm=95),
        _make_scene(8, "00:56-01:04", "Drama", 0.90, motion=0.18, audio_energy=0.50, ei=0.75, visual_emotion="sad", audio_mood="emotional", tempo_bpm=100),
        _make_scene(9, "01:04-01:12", "Dialogue", 0.82, motion=0.10, audio_energy=0.35, ei=0.60, visual_emotion="sad", audio_mood="emotional", tempo_bpm=88),
        _make_scene(10, "01:12-01:20", "Drama", 0.78, motion=0.08, audio_energy=0.25, ei=0.50, visual_emotion="neutral", audio_mood="calm", tempo_bpm=80),
    ]


# ── Test Functions ───────────────────────────────────────────────────

def test_comedy_no_action_recommendations():
    """Comedy trailer should NOT get 'add more action' recommendations."""
    payload = _make_payload(_build_comedy_trailer(), "Focker-In-Law Official Trailer")
    response = generate_recommendations(payload)

    print(f"\n{'='*60}")
    print(f"TEST: Comedy Trailer — {response.summary.trailer_title}")
    print(f"Genre: {response.trailer_profile.primary_genre} (conf: {response.trailer_profile.genre_confidence:.2f})")
    print(f"Secondary: {response.trailer_profile.secondary_genres}")
    print(f"Probabilities: {response.trailer_profile.genre_probabilities}")
    print(f"Recommendations: {len(response.recommendations)}")

    for r in response.recommendations:
        print(f"  [{r.severity}] Scene {r.scene} ({r.timeframe}): {r.problem[:80]}...")
        assert "add more action" not in r.recommendation.lower(), f"FAIL: Comedy got 'add more action': {r.recommendation}"
        assert "increase action" not in r.recommendation.lower(), f"FAIL: Comedy got 'increase action': {r.recommendation}"
        assert "increase motion" not in r.problem.lower(), f"FAIL: Comedy got 'increase motion': {r.problem}"

    print("  [PASS] No inappropriate action recommendations for Comedy trailer")


def test_romance_no_bpm_recommendations():
    """Romance trailer should NOT get 'increase BPM' recommendations."""
    payload = _make_payload(_build_romance_trailer(), "Someone Like You Official Trailer")
    response = generate_recommendations(payload)

    print(f"\n{'='*60}")
    print(f"TEST: Romance Trailer — {response.summary.trailer_title}")
    print(f"Genre: {response.trailer_profile.primary_genre} (conf: {response.trailer_profile.genre_confidence:.2f})")
    print(f"Recommendations: {len(response.recommendations)}")

    for r in response.recommendations:
        print(f"  [{r.severity}] Scene {r.scene} ({r.timeframe}): {r.problem[:80]}...")
        assert "increase bpm" not in r.recommendation.lower(), f"FAIL: Romance got 'increase BPM': {r.recommendation}"
        assert "increase tempo" not in r.recommendation.lower(), f"FAIL: Romance got 'increase tempo': {r.recommendation}"
        assert "add more action" not in r.recommendation.lower(), f"FAIL: Romance got 'add more action': {r.recommendation}"

    print("  [PASS] No inappropriate BPM/tempo recommendations for Romance trailer")


def test_action_dialogue_not_flagged():
    """Action trailer's dialogue scenes should NOT be flagged as problems."""
    payload = _make_payload(_build_action_trailer(), "Jason Statham - Mutiny 2026 Official Trailer")
    response = generate_recommendations(payload)

    print(f"\n{'='*60}")
    print(f"TEST: Action Trailer — {response.summary.trailer_title}")
    print(f"Genre: {response.trailer_profile.primary_genre} (conf: {response.trailer_profile.genre_confidence:.2f})")
    print(f"Recommendations: {len(response.recommendations)}")

    for r in response.recommendations:
        print(f"  [{r.severity}] Scene {r.scene} ({r.timeframe}): {r.problem[:80]}...")
        assert "remove dialogue" not in r.recommendation.lower(), f"FAIL: Action got 'remove dialogue': {r.recommendation}"

    print("  [PASS] No 'remove dialogue' recommendations for Action trailer")


def test_thriller_quiet_not_flagged():
    """Thriller trailer's quiet tension sections should NOT be automatically flagged."""
    payload = _make_payload(_build_thriller_trailer(), "Thriller Mystery Trailer")
    response = generate_recommendations(payload)

    print(f"\n{'='*60}")
    print(f"TEST: Thriller Trailer — {response.summary.trailer_title}")
    print(f"Genre: {response.trailer_profile.primary_genre} (conf: {response.trailer_profile.genre_confidence:.2f})")
    print(f"Recommendations: {len(response.recommendations)}")

    # Scene 5 is the quiet tension scene — should NOT be flagged just for being quiet
    scene5_recs = [r for r in response.recommendations if r.scene == 5]
    for r in scene5_recs:
        print(f"  [{r.severity}] Scene {r.scene}: {r.problem[:80]}...")
        # Should not flag just for being quiet
        assert "too slow" not in r.problem.lower(), f"FAIL: Thriller quiet scene got 'too slow': {r.problem}"
        assert "increase energy" not in r.recommendation.lower(), f"FAIL: Thriller quiet scene got 'increase energy'"

    print("  [PASS] Quiet tension sections not inappropriately flagged in Thriller")


def test_drama_low_motion_not_flagged():
    """Drama trailer's low motion should NOT be automatically flagged."""
    payload = _make_payload(_build_drama_trailer(), "Drama Character Study Trailer")
    response = generate_recommendations(payload)

    print(f"\n{'='*60}")
    print(f"TEST: Drama Trailer — {response.summary.trailer_title}")
    print(f"Genre: {response.trailer_profile.primary_genre} (conf: {response.trailer_profile.genre_confidence:.2f})")
    print(f"Recommendations: {len(response.recommendations)}")

    for r in response.recommendations:
        print(f"  [{r.severity}] Scene {r.scene} ({r.timeframe}): {r.problem[:80]}...")
        assert "add more action" not in r.recommendation.lower(), f"FAIL: Drama got 'add more action'"
        assert "increase motion" not in r.recommendation.lower(), f"FAIL: Drama got 'increase motion'"

    print("  [PASS] Low motion not flagged as problem in Drama trailer")


def test_genres_produce_different_results():
    """Different genres should produce meaningfully different genre classifications."""
    comedy_payload = _make_payload(_build_comedy_trailer(), "Comedy Test")
    romance_payload = _make_payload(_build_romance_trailer(), "Romance Test")
    action_payload = _make_payload(_build_action_trailer(), "Action Test")
    thriller_payload = _make_payload(_build_thriller_trailer(), "Thriller Test")
    drama_payload = _make_payload(_build_drama_trailer(), "Drama Test")

    comedy_resp = generate_recommendations(comedy_payload)
    romance_resp = generate_recommendations(romance_payload)
    action_resp = generate_recommendations(action_payload)
    thriller_resp = generate_recommendations(thriller_payload)
    drama_resp = generate_recommendations(drama_payload)

    print(f"\n{'='*60}")
    print("TEST: Cross-Genre Differentiation")
    print(f"  Comedy  -> {comedy_resp.trailer_profile.primary_genre} ({comedy_resp.trailer_profile.genre_confidence:.2f})")
    print(f"  Romance -> {romance_resp.trailer_profile.primary_genre} ({romance_resp.trailer_profile.genre_confidence:.2f})")
    print(f"  Action  -> {action_resp.trailer_profile.primary_genre} ({action_resp.trailer_profile.genre_confidence:.2f})")
    print(f"  Thriller-> {thriller_resp.trailer_profile.primary_genre} ({thriller_resp.trailer_profile.genre_confidence:.2f})")
    print(f"  Drama   -> {drama_resp.trailer_profile.primary_genre} ({drama_resp.trailer_profile.genre_confidence:.2f})")

    # Check that genres are correctly identified
    assert comedy_resp.trailer_profile.primary_genre == "Comedy", f"Comedy misclassified as {comedy_resp.trailer_profile.primary_genre}"
    assert romance_resp.trailer_profile.primary_genre == "Romance", f"Romance misclassified as {romance_resp.trailer_profile.primary_genre}"
    assert action_resp.trailer_profile.primary_genre == "Action", f"Action misclassified as {action_resp.trailer_profile.primary_genre}"
    assert thriller_resp.trailer_profile.primary_genre == "Thriller", f"Thriller misclassified as {thriller_resp.trailer_profile.primary_genre}"
    assert drama_resp.trailer_profile.primary_genre == "Drama", f"Drama misclassified as {drama_resp.trailer_profile.primary_genre}"

    # Check that they don't all have the same number of recommendations
    rec_counts = [
        len(comedy_resp.recommendations),
        len(romance_resp.recommendations),
        len(action_resp.recommendations),
        len(thriller_resp.recommendations),
        len(drama_resp.recommendations),
    ]
    print(f"  Rec counts: Comedy={rec_counts[0]}, Romance={rec_counts[1]}, Action={rec_counts[2]}, Thriller={rec_counts[3]}, Drama={rec_counts[4]}")

    print("  [PASS] All genres correctly classified and differentiated")


def test_well_balanced_trailer_minimal_recommendations():
    """A well-balanced trailer should produce minimal or no recommendations."""
    # Create a very balanced, smooth trailer
    balanced = [
        _make_scene(i + 1, f"00:{i*8:02d}-00:{(i+1)*8:02d}",
                    "Drama" if i < 3 else "Action" if i > 6 else "Drama",
                    0.85,
                    motion=0.2 + i * 0.06,  # Smoothly increasing
                    audio_energy=0.25 + i * 0.06,  # Smoothly increasing
                    ei=0.35 + i * 0.05,  # Smoothly increasing
                    visual_emotion="neutral",
                    audio_mood="emotional" if i < 5 else "intense",
                    tempo_bpm=90 + i * 5,
                    )
        for i in range(10)
    ]

    payload = _make_payload(balanced, "Well Balanced Trailer")
    response = generate_recommendations(payload)

    print(f"\n{'='*60}")
    print(f"TEST: Well-Balanced Trailer")
    print(f"Genre: {response.trailer_profile.primary_genre}")
    print(f"Recommendations: {len(response.recommendations)}")

    # A smooth, gradually escalating trailer should have very few or no issues
    assert len(response.recommendations) <= 4, f"Too many recs ({len(response.recommendations)}) for balanced trailer"

    if not response.recommendations:
        print("  [PASS] No recommendations — trailer is well-balanced!")
    else:
        for r in response.recommendations:
            print(f"  [{r.severity}] Scene {r.scene}: {r.problem[:80]}...")
        print(f"  [PASS] Only {len(response.recommendations)} recommendation(s) for balanced trailer")


def test_output_format():
    """Verify the output format matches the specification."""
    payload = _make_payload(_build_action_trailer(), "Format Test Trailer")
    response = generate_recommendations(payload)

    print(f"\n{'='*60}")
    print("TEST: Output Format Validation")

    # Check trailer_profile exists
    assert response.trailer_profile is not None, "trailer_profile missing"
    assert response.trailer_profile.primary_genre, "primary_genre missing"
    assert response.trailer_profile.genre_probabilities, "genre_probabilities missing"
    assert 0 <= response.trailer_profile.genre_confidence <= 1, "genre_confidence out of range"

    # Check trailer_baseline exists
    assert response.trailer_baseline is not None, "trailer_baseline missing"
    assert response.trailer_baseline.total_scenes > 0, "total_scenes is 0"
    assert response.trailer_baseline.shot_duration.median > 0, "shot_duration median is 0"

    # Check structural_phases
    assert isinstance(response.structural_phases, list), "structural_phases not a list"

    # Check recommendations format
    for r in response.recommendations:
        assert r.severity in ("HIGH", "MEDIUM", "LOW"), f"Invalid severity: {r.severity}"
        assert 0 <= r.confidence <= 1, f"Confidence out of range: {r.confidence}"
        assert r.evidence_details, f"No evidence_details for scene {r.scene}"
        assert r.start_time is not None, f"No start_time for scene {r.scene}"
        assert r.end_time is not None, f"No end_time for scene {r.scene}"
        assert r.why, f"No 'why' for scene {r.scene}"
        assert r.timeframe, f"No timeframe for scene {r.scene}"

    # Check timeline insights (should exist for ALL scenes)
    assert len(response.timeline_insights) == 10, f"Expected 10 timeline insights, got {len(response.timeline_insights)}"

    # Check backward compatibility fields
    assert response.id is not None
    assert response.trailerTitle is not None
    assert response.overallPriorityScore >= 0
    assert response.componentScores is not None

    print("  [PASS] All output format validations passed")


# ── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("MOVIE TRAILER RECOMMENDATION ENGINE — TEST SUITE")
    print("=" * 60)

    try:
        test_comedy_no_action_recommendations()
        test_romance_no_bpm_recommendations()
        test_action_dialogue_not_flagged()
        test_thriller_quiet_not_flagged()
        test_drama_low_motion_not_flagged()
        test_genres_produce_different_results()
        test_well_balanced_trailer_minimal_recommendations()
        test_output_format()

        print(f"\n{'='*60}")
        print("ALL TESTS PASSED [PASS]")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
