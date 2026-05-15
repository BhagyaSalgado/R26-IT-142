from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.dependencies import get_repository
from app.repositories.base import BaseRepository
from app.schemas.analysis import AnalysisData, AnalyzeTrailerRequest, BatchAnalyzeRequest, ComponentOutput
from app.schemas.common import ApiResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["Analysis"])


def get_analysis_service(
    settings: Settings = Depends(get_settings),
    repository: BaseRepository = Depends(get_repository),
) -> AnalysisService:
    return AnalysisService(settings=settings, repository=repository)


@router.post("/analyze", response_model=ApiResponse[AnalysisData])
def analyze_trailer(request: AnalyzeTrailerRequest, service: AnalysisService = Depends(get_analysis_service)):
    data = service.analyze(str(request.youtube_url))
    return ApiResponse(message="Trailer analyzed successfully.", data=data)


@router.post("/batch-analyze", response_model=ApiResponse[list[AnalysisData]])
def batch_analyze(request: BatchAnalyzeRequest, service: AnalysisService = Depends(get_analysis_service)):
    results = [service.analyze(str(url)) for url in request.youtube_urls]
    return ApiResponse(message="Batch trailer analysis completed.", data=results)


@router.get("/history", response_model=ApiResponse[list])
def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    service: AnalysisService = Depends(get_analysis_service),
):
    return ApiResponse(message="Analysis history retrieved.", data=service.list_history(limit=limit))


@router.get("/component-output/{video_id}", response_model=ApiResponse[ComponentOutput])
def component_output(video_id: str, service: AnalysisService = Depends(get_analysis_service)):
    return ApiResponse(message="Component integration output generated.", data=service.get_component_output(video_id))
