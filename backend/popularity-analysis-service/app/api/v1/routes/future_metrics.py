from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, HttpUrl

from app.api.v1.routes.analysis import get_analysis_service
from app.schemas.common import ApiResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/future-metrics", tags=["Future Metrics"])


class FutureMetricsRequest(BaseModel):
    youtube_url: HttpUrl | str = Field(description="YouTube trailer URL or video id")
    horizon_days: int = Field(default=7, ge=1, le=365)
    save_result: bool = True


@router.post("/predict", response_model=ApiResponse[dict])
def predict_future_metrics(
    request: FutureMetricsRequest,
    service: AnalysisService = Depends(get_analysis_service),
):
    data = service.predict_future_metrics(
        youtube_url=str(request.youtube_url),
        horizon_days=request.horizon_days,
        save_result=request.save_result,
    )
    return ApiResponse(message="Future metrics predicted successfully.", data=data)


@router.get("/history", response_model=ApiResponse[list])
def get_future_metrics_history(
    limit: int = Query(default=20, ge=1, le=100),
    service: AnalysisService = Depends(get_analysis_service),
):
    return ApiResponse(message="Future metrics history retrieved.", data=service.list_future_history(limit=limit))


@router.get("/{video_id}", response_model=ApiResponse[dict])
def get_future_prediction(
    video_id: str,
    horizon_days: int = Query(default=7, ge=1, le=365),
    service: AnalysisService = Depends(get_analysis_service),
):
    return ApiResponse(
        message="Future metrics prediction retrieved.",
        data=service.get_future_prediction(video_id=video_id, horizon_days=horizon_days),
    )
