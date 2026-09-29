from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.prediction import router as prediction_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(prediction_router, prefix="/predict", tags=["Prediction"])
