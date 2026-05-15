from fastapi import APIRouter, Depends

from app.api.v1.routes.analysis import get_analysis_service
from app.ml.model_registry import ModelRegistry
from app.schemas.common import ApiResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/model", tags=["Model"])


@router.get("/performance", response_model=ApiResponse[dict])
def get_model_performance(service: AnalysisService = Depends(get_analysis_service)):
    return ApiResponse(message="Model performance retrieved.", data=service.get_latest_model_performance())


@router.post("/train-simulated", response_model=ApiResponse[dict])
def train_simulated(service: AnalysisService = Depends(get_analysis_service)):
    evaluation = service.create_simulated_evaluation()
    return ApiResponse(message="Simulated model evaluation saved. Replace this after real model training.", data=evaluation)


@router.get("/artifact-status", response_model=ApiResponse[dict])
def artifact_status():
    registry = ModelRegistry()
    return ApiResponse(message="Model artifact status retrieved.", data=registry.artifact_status())
