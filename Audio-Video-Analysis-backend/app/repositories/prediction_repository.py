import os
import json
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from app.core.config import settings
from app.firebase.firebase_config import get_firestore_client

OUTPUTS_DIR = settings.OUTPUT_DIR

def _parse_csv_safely(csv_path: str) -> list[dict]:
    if not os.path.exists(csv_path):
        return []
    try:
        df = pd.read_csv(csv_path)
        df = df.replace([np.nan, np.inf, -np.inf], None)
        records = df.to_dict(orient='records')
        clean_records = []
        for r in records:
            cleaned = {}
            for k, v in r.items():
                if v is None or pd.isna(v):
                    cleaned[k] = None
                elif isinstance(v, (np.integer, int)):
                    cleaned[k] = int(v)
                elif isinstance(v, (np.floating, float)):
                    cleaned[k] = round(float(v), 6)
                else:
                    cleaned[k] = str(v)
            clean_records.append(cleaned)
        return clean_records
    except Exception as e:
        print(f'Error reading CSV {csv_path}: {e}')
        return []

def _load_run_from_disk(run_id: str) -> dict | None:
    run_dir = os.path.join(str(OUTPUTS_DIR), run_id)
    if not os.path.exists(run_dir):
        return None

    final_csv = os.path.join(run_dir, 'final_system_output.csv')
    visual_csv = os.path.join(run_dir, 'visual_feature_output.csv')
    audio_csv = os.path.join(run_dir, 'audio_feature_output.csv')
    insights_json = os.path.join(run_dir, 'insights.json')

    final_data = _parse_csv_safely(final_csv)
    visual_data = _parse_csv_safely(visual_csv)
    audio_data = _parse_csv_safely(audio_csv)

    insights = {}
    if os.path.exists(insights_json):
        try:
            with open(insights_json, 'r', encoding='utf-8') as f:
                insights = json.load(f)
        except Exception:
            pass

    clean_title = run_id.replace('_', ' ').title()

    mtime = os.path.getmtime(run_dir)
    created_at = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

    return {
        'id': run_id,
        'run_id': run_id,
        'filename': clean_title,
        'created_at': created_at,
        'total_scenes': len(final_data),
        'dominant_genre': insights.get('dominant_genre', 'Drama'),
        'secondary_genre': insights.get('secondary_genre'),
        'genre_mixture': insights.get('genre_mixture', {}),
        'final_system_output': final_data,
        'visual_feature_output': visual_data,
        'audio_feature_output': audio_data,
        'insights': insights
    }

class PredictionRepository:
    def save_prediction(self, data: dict) -> str:
        doc_id = data.get('run_id') or str(datetime.now().timestamp())
        try:
            db = get_firestore_client()
            doc_ref = db.collection(settings.FIREBASE_COLLECTION).document(doc_id)
            doc_data = {
                **data,
                'created_at': datetime.now(timezone.utc),
            }
            doc_ref.set(doc_data)
            return doc_ref.id
        except Exception as e:
            print(f'Firestore save notice (saved on disk): {e}')
            return doc_id

    def get_prediction(self, prediction_id: str) -> dict | None:
        # 1. First check local disk storage (instant and complete)
        disk_data = _load_run_from_disk(prediction_id)
        if disk_data and disk_data.get('final_system_output'):
            return disk_data

        # 2. Try Firestore
        try:
            document = (
                get_firestore_client()
                .collection(settings.FIREBASE_COLLECTION)
                .document(prediction_id)
                .get(timeout=3)
            )
            if document.exists:
                data = document.to_dict() or {}
                created_at = data.get('created_at')
                if hasattr(created_at, 'isoformat'):
                    data['created_at'] = created_at.isoformat()
                data['id'] = document.id
                return data
        except Exception as e:
            print(f'Firestore get error: {e}')

        return disk_data

    def get_recent_predictions(self, limit: int = 12) -> list[dict]:
        records = []
        
        # Load from disk storage outputs
        if os.path.exists(str(OUTPUTS_DIR)):
            runs = []
            for item in os.listdir(str(OUTPUTS_DIR)):
                item_path = os.path.join(str(OUTPUTS_DIR), item)
                if os.path.isdir(item_path):
                    final_csv = os.path.join(item_path, 'final_system_output.csv')
                    if os.path.exists(final_csv):
                        mtime = os.path.getmtime(item_path)
                        runs.append((item, mtime))
            
            # Sort newest first
            runs.sort(key=lambda x: x[1], reverse=True)
            for run_id, mtime in runs[:limit]:
                run_dir = os.path.join(str(OUTPUTS_DIR), run_id)
                final_csv = os.path.join(run_dir, 'final_system_output.csv')
                insights_json = os.path.join(run_dir, 'insights.json')
                
                insights = {}
                if os.path.exists(insights_json):
                    try:
                        with open(insights_json, 'r', encoding='utf-8') as f:
                            insights = json.load(f)
                    except Exception:
                        pass
                        
                total_scenes = 0
                try:
                    with open(final_csv, 'r', encoding='utf-8') as f:
                        total_scenes = max(0, sum(1 for _ in f) - 1)
                except Exception:
                    pass
                    
                clean_title = run_id.replace('_', ' ').title()
                created_at = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
                
                records.append({
                    'id': run_id,
                    'filename': clean_title,
                    'created_at': created_at,
                    'total_scenes': total_scenes,
                    'dominant_genre': insights.get('dominant_genre', 'Drama'),
                    'secondary_genre': insights.get('secondary_genre'),
                    'average_emotional_intensity': insights.get('average_emotional_intensity', 0.65),
                    'engagement_level': insights.get('engagement_level', 'High'),
                    'high_intensity_scenes': len(insights.get('high_intensity_scenes') or []),
                })

        return records

