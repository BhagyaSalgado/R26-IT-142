from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.common import ApiResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ApiResponse[dict])
def health(settings: Settings = Depends(get_settings)):
    return ApiResponse(
        message="Service is running.",
        data={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "firebase_mock_mode": settings.firebase_mock_mode,
        },
    )
