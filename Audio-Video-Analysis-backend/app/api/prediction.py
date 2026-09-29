from pathlib import Path
import os
import re
import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from app.services.prediction_service import PredictionService
from app.repositories.prediction_repository import PredictionRepository
from app.core.config import settings
from fastapi.concurrency import run_in_threadpool

router = APIRouter()

def resolve_video_file(prediction_id: str, clean_name: str = "") -> Path | None:
    upload_root = settings.UPLOAD_DIR.resolve()
    if not upload_root.exists():
        return None
        
    # 1. Exact match by clean_name / filename
    if clean_name:
        exact_p = upload_root / clean_name
        if exact_p.is_file():
            return exact_p
            
    # 2. Match by the unique hex ID embedded in the prediction_id
    # The run_id format is: {safe_name}_{uuid_hex8}
    # The upload filename format is: {original_name}_{uuid_hex8}.mp4
    parts = prediction_id.split('_')
    for hex_len in [8, 10, 12]:
        if len(parts) >= 2:
            short_id = parts[-1]
            if len(short_id) >= 6:
                for f in upload_root.glob("*.mp4"):
                    if short_id in f.name:
                        return f
    
    # 3. Try second-to-last part as hex ID (for compound prediction IDs)
    if len(parts) >= 3:
        short_id = parts[-2]
        if len(short_id) >= 6:
            for f in upload_root.glob("*.mp4"):
                if short_id in f.name:
                    return f
        
    return None

@router.get('/history')
async def prediction_history(limit: int = Query(default=12, ge=1, le=50)):
    try:
        repository = PredictionRepository()
        return {'items': repository.get_recent_predictions(limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Could not load analysis history: {str(e)}')

@router.get('/history/{prediction_id}')
async def prediction_history_detail(prediction_id: str):
    try:
        result = PredictionRepository().get_prediction(prediction_id)
        if result is None:
            raise HTTPException(status_code=404, detail='Analysis not found.')
        result['video_url'] = f'/api/v1/predict/history/{prediction_id}/video'
        result['thumbnail_url'] = f'/api/v1/predict/history/{prediction_id}/thumbnail'
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Could not load analysis: {str(e)}')

@router.get('/history/{prediction_id}/thumbnail')
async def prediction_history_thumbnail(prediction_id: str):
    outputs_root = settings.OUTPUT_DIR.resolve()
    
    # 1. Search in storage/outputs/{prediction_id}/frames/
    target_dir = outputs_root / prediction_id
    if not target_dir.exists():
        short_id = prediction_id.split('_')[-1] if '_' in prediction_id else prediction_id
        for d in os.listdir(str(outputs_root)):
            if (short_id in d or prediction_id in d) and os.path.isdir(str(outputs_root / d)):
                target_dir = outputs_root / d
                break
                
    if target_dir.exists():
        frames_dir = target_dir / "frames"
        if frames_dir.exists():
            # Pick a non-black frame (scene_2, scene_3, or largest file size)
            candidates = []
            for f in os.listdir(str(frames_dir)):
                if f.endswith(('.jpg', '.jpeg', '.png')):
                    p = frames_dir / f
                    size = p.stat().st_size
                    candidates.append((p, size, f))
            # Sort by file size descending (largest frame has visual content, avoiding 4KB black intro)
            candidates.sort(key=lambda x: x[1], reverse=True)
            if candidates and candidates[0][1] > 10000:
                return FileResponse(candidates[0][0], media_type="image/jpeg", headers={"Access-Control-Allow-Origin": "*"})
            elif candidates:
                return FileResponse(candidates[0][0], media_type="image/jpeg", headers={"Access-Control-Allow-Origin": "*"})

    # 2. If no pre-extracted frame, extract from the matched video at 3.0s
    result = PredictionRepository().get_prediction(prediction_id) or {}
    clean_name = str(result.get('filename', ''))
    video_path = resolve_video_file(prediction_id, clean_name)
    
    if video_path and video_path.is_file():
        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 3.0))  # 3.0 seconds in
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 1.0))
                ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                temp_thumb = outputs_root / f"thumb_{prediction_id}.jpg"
                cv2.imwrite(str(temp_thumb), frame)
                return FileResponse(temp_thumb, media_type="image/jpeg", headers={"Access-Control-Allow-Origin": "*"})
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="Thumbnail not found.")

@router.get('/history/{prediction_id}/video')
async def prediction_history_video(prediction_id: str):
    result = PredictionRepository().get_prediction(prediction_id)
    clean_name = str(result.get('filename', '')) if result else ''
    
    video_path = resolve_video_file(prediction_id, clean_name)
    if video_path and video_path.is_file():
        return FileResponse(
            video_path,
            media_type='video/mp4',
            filename=video_path.name,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Accept-Ranges": "bytes"
            }
        )

    raise HTTPException(status_code=404, detail=f'Stored video not found for {prediction_id}.')

@router.post('/video')
async def predict_video(video: UploadFile = File(...)):
    if not video.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail='Upload a valid video file.')
    try:
        def _init_and_analyze(saved_path_str: str, movie_name: str):
            service = PredictionService()
            result = service.analyzer.analyze(saved_path_str, movie_name=movie_name)
            firestore_id = service.repository.save_prediction(result)
            result["firestore_id"] = firestore_id
            return result

        from app.utils.file_utils import save_upload_file
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        saved_path = await save_upload_file(video, settings.UPLOAD_DIR)
        
        result = await run_in_threadpool(
            _init_and_analyze,
            str(saved_path),
            Path(video.filename).stem
        )
        
        run_id = result.get('run_id', '')
        result['video_url'] = f'/api/v1/predict/history/{run_id}/video'
        result['thumbnail_url'] = f'/api/v1/predict/history/{run_id}/thumbnail'
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Video analysis failed: {str(e)}')
