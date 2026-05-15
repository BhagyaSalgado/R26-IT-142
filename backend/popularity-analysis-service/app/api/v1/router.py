from fastapi import APIRouter

from app.api.v1.routes import analysis, health, model, trailers

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(analysis.router)
api_router.include_router(trailers.router)
api_router.include_router(model.router)
