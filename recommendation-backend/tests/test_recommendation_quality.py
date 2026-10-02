from app.schemas.recommendation_schema import RecommendationRequest
from app.services.cinematic_recommendation_engine import (
    _ProblemCandidate,
    _actions_are_similar,
    _select_diverse_candidates,
)
from app.services.recommendation_service import (
    _build_scene_rows,
    _classify_genre,
    _refine_scene_types,
)


def _scene(scene: int, scene_type: str, confidence: float) -> dict:
    start = (scene - 1) * 2
    return {
        "scene": scene,
        "time": f"00:{start:02d}-00:{start + 2:02d}",
        "scene_type": scene_type,
        "scene_type_confidence": confidence,
        "classification_reliable": confidence >= 0.4,
        "M": 0.4,
        "A": 0.5,
        "O": 0.5,
        "F": 0.7,
        "EI": 0.55,
        "audio_mood": "emotional",
        "face_emotion": "neutral",
    }


def test_scene_refinement_only_changes_isolated_uncertain_label():
    payload = RecommendationRequest(
        final_system_output=[
            _scene(1, "Comedy", 0.90),
            _scene(2, "Action", 0.28),
            _scene(3, "Comedy", 0.86),
            _scene(4, "Thriller", 0.25),
        ]
    )
    rows = _build_scene_rows(payload)

    stats = _refine_scene_types(rows)

    assert rows[1]["evidence"].scene_type == "Comedy"
    assert rows[1]["evidence"].classification_reliable is True
    assert rows[3]["evidence"].scene_type == "Thriller"
    assert rows[3]["evidence"].classification_reliable is False
    assert stats == {"corrected": 1, "unreliable": 1}


def test_complete_trailer_genre_and_metadata_override_flat_local_scores():
    payload = RecommendationRequest(
        final_system_output=[_scene(i, "Action", 0.52) for i in range(1, 7)]
    )
    rows = _build_scene_rows(payload)
    report = _classify_genre(
        rows,
        "Example Trailer",
        12.0,
        insights={
            "dominant_genre": "Comedy",
            "secondary_genre": "Action",
            "genre_mixture": {"Comedy": 0.45, "Action": 0.40, "Drama": 0.15},
        },
        metadata={"genres": ["Comedy", "Action"]},
    )

    assert report.dominant_genre == "Comedy"
    assert report.genre_confidence >= 0.75
    assert report.genre_source == "upstream-analysis+metadata"


def _candidate(scene: int, source: str, category: str, root: str) -> _ProblemCandidate:
    return _ProblemCandidate(
        scene_idx=scene - 1,
        scene_id=scene,
        timeframe=f"00:{scene * 2:02d}-00:{scene * 2 + 2:02d}",
        start_time=float(scene * 2),
        end_time=float(scene * 2 + 2),
        problem=f"{root} problem",
        why="Measured evidence",
        fix=f"Fix {root}",
        evidence_details={"dominant_feature": root},
        category=category,
        raw_confidence=0.8,
        severity_score=0.7,
        focus_area=root,
        fix_source=source,
    )


def test_candidate_selection_collapses_repeated_root_cause():
    first = _candidate(2, "trailer-anomaly", "Pacing", "shot_duration")
    repeated = _candidate(8, "trailer-anomaly", "Pacing", "shot_duration")
    distinct = _candidate(5, "trailer-anomaly", "Audio", "audio_energy")

    selected = _select_diverse_candidates([first, repeated, distinct], total_scenes=20)

    assert len(selected) == 2
    pacing = next(item for item in selected if item.category == "Pacing")
    assert pacing.evidence_details["related_locations"][0]["scene"] == 8


def test_rephrased_duplicate_actions_are_detected():
    assert _actions_are_similar(
        "Trim this shot closer to the trailer median and insert a reaction angle.",
        "Trim the shot toward the median or insert a clearer reaction angle.",
    )
    assert not _actions_are_similar(
        "Trim this shot toward the trailer median.",
        "Raise dialogue clarity by reducing the music level.",
    )
