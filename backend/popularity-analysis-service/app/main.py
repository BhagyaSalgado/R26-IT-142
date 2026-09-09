from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError, EntityNotFoundError, InvalidYouTubeUrlError
from app.schemas.common import ErrorResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI microservice for Movie Trailer Popularity Metrics Analysis with Firebase Firestore integration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidYouTubeUrlError)
async def invalid_youtube_url_handler(request: Request, exc: InvalidYouTubeUrlError):
    return JSONResponse(status_code=400, content=ErrorResponse(message=str(exc)).model_dump())


@app.exception_handler(EntityNotFoundError)
async def not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content=ErrorResponse(message=str(exc)).model_dump())


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=400, content=ErrorResponse(message=str(exc)).model_dump())


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.api_v1_prefix,
    }


@app.get("/health")
def root_health():
    return {
        "status": "success",
        "message": "Service is running.",
        "firebase_project_id": settings.firebase_project_id,
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)
