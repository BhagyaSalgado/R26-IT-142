from unittest.mock import patch
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def _no_external_generation_calls():
    """Keep unit tests deterministic and network-free.

    These tests exercise the rule-based, evidence-driven recommendation
    engine using synthetic scene data and placeholder trailer titles (e.g.
    "Action Test"). generate_recommendations() also tries a real OMDb
    lookup first when OMDB_API_KEY is configured — without this fixture,
    placeholder titles can fuzzy-match unrelated real movies on OMDb,
    making tests slow, network-dependent, and flaky. Force the lookup to
    report "not found" so these tests stay isolated and deterministic.
    """
    with (
        patch("app.services.recommendation_service.fetch_movie_metadata", return_value=None),
        patch("app.services.recommendation_service._resolve_output_dir", return_value=None),
        patch("app.services.cinematic_recommendation_engine.generate_fix_text", return_value=None),
        patch(
            "app.services.llm_fix_generator.get_settings",
            return_value=SimpleNamespace(gemini_api_key="", anthropic_api_key=""),
        ),
    ):
        yield
