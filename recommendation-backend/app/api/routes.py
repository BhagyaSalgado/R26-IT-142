from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.dependencies import AuthenticatedUser, get_current_user
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation_schema import PopularityContext, RecommendationRequest, RecommendationResponse
from app.services.recommendation_service import generate_recommendations
from app.services.sentiment_fetcher import get_sentiment_context

settings = get_settings()

router = APIRouter(prefix="/api/v1", tags=["recommendations"])
recommendation_repository = RecommendationRepository()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.post("/recommendations/generate", response_model=RecommendationResponse)
async def generate(
    payload: RecommendationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RecommendationResponse:
    if payload.popularity_context is None:
        payload.popularity_context = await _load_latest_popularity_context(current_user.id_token)

    # Fetch this user's own audience sentiment (uses trailer_id if provided, else latest)
    sentiment_context = await run_in_threadpool(
        get_sentiment_context,
        current_user.uid,
        payload.trailer_id,
    )

    try:
        # generate_recommendations makes blocking network calls (OMDb,
        # Firestore) — offload to a thread so it doesn't stall the event
        # loop and block every other concurrent request being served.
        response = await run_in_threadpool(generate_recommendations, payload, sentiment_context=sentiment_context)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return await run_in_threadpool(recommendation_repository.save, response, current_user.uid)


@router.get("/recommendations/latest", response_model=RecommendationResponse)
async def generate_latest(current_user: AuthenticatedUser = Depends(get_current_user)) -> RecommendationResponse:
    latest_detail = await _load_latest_emotion_analysis(current_user.id_token)
    popularity_context = await _load_latest_popularity_context(current_user.id_token)

    # Fetch this user's latest audience sentiment
    sentiment_context = await run_in_threadpool(get_sentiment_context, current_user.uid)

    payload = RecommendationRequest(
        trailer_title=str(latest_detail.get("filename") or "Latest emotion analysis"),
        source_prediction_id=str(latest_detail.get("id") or ""),
        insights=_analysis_insights(latest_detail),
        final_system_output=_as_rows(latest_detail.get("final_system_output")),
        audio_feature_output=_as_rows(latest_detail.get("audio_feature_output")),
        visual_feature_output=_as_rows(latest_detail.get("visual_feature_output")),
        popularity_context=popularity_context,
    )
    try:
        # generate_recommendations makes blocking network calls (OMDb,
        # Firestore) — offload to a thread so it doesn't stall the event
        # loop and block every other concurrent request being served.
        response = await run_in_threadpool(generate_recommendations, payload, sentiment_context=sentiment_context)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return await run_in_threadpool(recommendation_repository.save, response, current_user.uid)


@router.get("/recommendations/prediction/{prediction_id}", response_model=RecommendationResponse)
async def generate_for_prediction(
    prediction_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RecommendationResponse:
    detail = await _load_emotion_analysis_by_id(prediction_id, current_user.id_token)
    popularity_context = await _load_latest_popularity_context(current_user.id_token)
    sentiment_context = await run_in_threadpool(get_sentiment_context, current_user.uid)

    payload = RecommendationRequest(
        trailer_title=str(detail.get("filename") or f"Emotion analysis ({prediction_id})"),
        source_prediction_id=prediction_id,
        insights=_analysis_insights(detail),
        final_system_output=_as_rows(detail.get("final_system_output")),
        audio_feature_output=_as_rows(detail.get("audio_feature_output")),
        visual_feature_output=_as_rows(detail.get("visual_feature_output")),
        popularity_context=popularity_context,
    )
    try:
        # generate_recommendations makes blocking network calls (OMDb,
        # Firestore) — offload to a thread so it doesn't stall the event
        # loop and block every other concurrent request being served.
        response = await run_in_threadpool(generate_recommendations, payload, sentiment_context=sentiment_context)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return await run_in_threadpool(recommendation_repository.save, response, current_user.uid)


@router.get("/recommendations/history")
async def recommendation_history(
    limit: int = Query(default=12, ge=1, le=50),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, list[dict[str, Any]]]:
    items = await run_in_threadpool(recommendation_repository.list_recent, current_user.uid, limit)
    return {"items": items}


@router.get("/recommendations/history/{recommendation_id}")
async def recommendation_detail(
    recommendation_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    result = await run_in_threadpool(recommendation_repository.get, recommendation_id, current_user.uid)
    if not result:
        raise HTTPException(status_code=404, detail="Recommendation result not found.")
    return result


async def _load_latest_emotion_analysis(id_token: str) -> dict[str, Any]:
    base_url = settings.emotion_api_base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {id_token}"} if id_token else {}

    async with httpx.AsyncClient(timeout=20.0) as client:
        history_response = await client.get(
            f"{base_url}/api/v1/predict/history", params={"limit": 1}, headers=headers
        )
        if history_response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail="Unable to load emotion analysis history from the emotion backend.",
            )

        history_payload = history_response.json()
        items = history_payload.get("items") if isinstance(history_payload, dict) else None
        if not items:
            raise HTTPException(status_code=404, detail="No saved emotion analysis found.")

        prediction_id = items[0].get("id")
        if not prediction_id:
            raise HTTPException(status_code=502, detail="Latest emotion analysis does not contain an id.")

        return await _load_emotion_analysis_by_id(prediction_id, id_token)


async def _load_emotion_analysis_by_id(prediction_id: str, id_token: str) -> dict[str, Any]:
    base_url = settings.emotion_api_base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {id_token}"} if id_token else {}

    async with httpx.AsyncClient(timeout=20.0) as client:
        detail_response = await client.get(
            f"{base_url}/api/v1/predict/history/{prediction_id}", headers=headers
        )
        if detail_response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Unable to load emotion analysis detail for '{prediction_id}' from emotion backend.",
            )

        detail_payload = detail_response.json()
        if not isinstance(detail_payload, dict):
            raise HTTPException(status_code=502, detail="Emotion backend returned an invalid detail payload.")
        return detail_payload


async def _load_latest_popularity_context(id_token: str) -> PopularityContext | None:
    base_url = settings.popularity_api_base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {id_token}"} if id_token else {}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            history_response = await client.get(
                f"{base_url}/api/v1/history", params={"limit": 1}, headers=headers
            )
            if history_response.status_code >= 400:
                return None

            history_payload = history_response.json()
            items = history_payload.get("data") if isinstance(history_payload, dict) else None
            if not items:
                return None

            latest = items[0] if isinstance(items, list) and items else None
            video_id = latest.get("video_id") if isinstance(latest, dict) else None
            if not video_id:
                return None

            component_response = await client.get(
                f"{base_url}/api/v1/component-output/{video_id}", headers=headers
            )
            if component_response.status_code >= 400:
                return None

            component_payload = component_response.json()
            component_data = component_payload.get("data") if isinstance(component_payload, dict) else None
            if not isinstance(component_data, dict):
                return None

            return PopularityContext(
                predicted_reaction=str(component_data.get("prediction") or "unknown"),
                confidence_score=_to_float(component_data.get("confidence")),
                popularity_score=_to_float(component_data.get("popularity_score")),
                engagement_rate=_to_float(component_data.get("engagement_rate")),
                model_version=str(component_data.get("model_version") or "unknown"),
            )
    except httpx.HTTPError:
        return None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _analysis_insights(detail: dict[str, Any]) -> dict[str, Any]:
    """Preserve complete-trailer classifications supplied by the analyser."""
    insights = dict(_as_dict(detail.get("insights")))
    for key in ("dominant_genre", "secondary_genre", "genre_mixture"):
        if insights.get(key) is None and detail.get(key) is not None:
            insights[key] = detail[key]
    return insights


def _as_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
