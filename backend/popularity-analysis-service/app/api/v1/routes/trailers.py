from fastapi import APIRouter, Depends

from app.api.v1.routes.analysis import get_analysis_service
from app.schemas.common import ApiResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/trailers", tags=["Trailers"])


@router.get("/{video_id}", response_model=ApiResponse[dict])
def get_trailer(video_id: str, service: AnalysisService = Depends(get_analysis_service)):
    return ApiResponse(message="Trailer retrieved.", data=service.get_trailer(video_id).model_dump())


@router.get("/{video_id}/metrics", response_model=ApiResponse[dict])
def get_metrics(video_id: str, service: AnalysisService = Depends(get_analysis_service)):
    return ApiResponse(message="Trailer metrics retrieved.", data=service.get_metrics(video_id).model_dump())


@router.get("/{video_id}/features", response_model=ApiResponse[dict])
def get_features(video_id: str, service: AnalysisService = Depends(get_analysis_service)):
    return ApiResponse(message="Trailer features retrieved.", data=service.get_features(video_id).model_dump())


@router.get("/{video_id}/prediction", response_model=ApiResponse[dict])
def get_prediction(video_id: str, service: AnalysisService = Depends(get_analysis_service)):
    return ApiResponse(message="Trailer prediction retrieved.", data=service.get_prediction(video_id).model_dump())
