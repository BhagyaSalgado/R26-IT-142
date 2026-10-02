from app.services.llm_fix_generator import _synthesize_dynamic_editorial_fix


def test_comedy_recommendation_generation():
    candidates = [
        {
            "id": 1,
            "scene": 2,
            "timeframe": "00:05.96-00:08.26",
            "genre": "Comedy",
            "category": "Audio",
            "phase": "setup",
            "detected_problem": "Kinetic motion (99%) exceeds audio",
            "evidence_details": {
                "motion": 0.99,
                "audio_energy": 0.28,
                "shot_duration": 2.3,
            },
        },
        {
            "id": 2,
            "scene": 6,
            "timeframe": "00:13.35-00:20.44",
            "genre": "Comedy",
            "category": "Pacing",
            "phase": "buildup",
            "detected_problem": "Pacing drag in Scene 6: 7.1s hold",
            "evidence_details": {
                "shot_duration": 7.1,
                "trailer_median": 1.3,
            },
        },
    ]

    results = {
        item["id"]: _synthesize_dynamic_editorial_fix(item)
        for item in candidates
    }
    assert results is not None
    assert 1 in results
    assert 2 in results

    # Verify comedy-specific fix generation
    comedy_fix_audio = results[1]["fix"].lower()
    comedy_why_audio = results[1]["why"].lower()
    assert "comedy" in comedy_why_audio or "physical" in comedy_why_audio
    assert ("foley" in comedy_fix_audio or "acoustic" in comedy_fix_audio or "playful" in comedy_fix_audio)
    assert "sub-bass" not in comedy_fix_audio

    comedy_fix_pacing = results[2]["fix"].lower()
    assert "punchline" in comedy_fix_pacing or "gag" in comedy_fix_pacing or "reaction" in comedy_fix_pacing


def test_horror_recommendation_generation():
    candidate = {
        "id": 1,
        "scene": 4,
        "timeframe": "00:15.00-00:22.00",
        "genre": "Horror",
        "category": "Pacing",
        "phase": "buildup",
        "detected_problem": "Pacing hold 7.0s",
        "evidence_details": {
            "shot_duration": 7.0,
            "trailer_median": 1.5,
        },
    }
    result = _synthesize_dynamic_editorial_fix(candidate)
    assert result is not None
    horror_fix = result["fix"].lower()
    assert "tension" in horror_fix or "drone" in horror_fix or "shock" in horror_fix

