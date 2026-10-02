# Movie Trailer Recommendation Engine

Separate backend component for **Content Insight and Recommendation**.

This service does not re-analyze video. It consumes the real outputs from the emotional analysis backend:

- `final_system_output`
- `audio_feature_output`
- `visual_feature_output`
- `insights`

Then it detects scene/time-frame problems and generates ranked recommendations using an explainable Recommendation Priority Score.

The backend now supports a supervised Random Forest recommendation model. When `RECOMMENDATION_MODEL_REQUIRED=true`, API responses are produced from the trained model artifact and the request is rejected if the model file is missing or confidence is below threshold.

Generated recommendation results are stored in Firestore in a separate collection.

## Structure

```text
app/
	api/routes.py
	core/config.py
	firebase/firebase_config.py
	repositories/recommendation_repository.py
	schemas/recommendation_schema.py
	services/recommendation_service.py
	main.py
```

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

The emotion analysis backend should already run on `http://127.0.0.1:8000`.

```bash
uvicorn app.main:app --reload --port 8010
```

Open:

```text
http://127.0.0.1:8010/docs
```

## Endpoints

```text
GET  /api/v1/health
POST /api/v1/recommendations/generate
GET  /api/v1/recommendations/latest
GET  /api/v1/recommendations/history
GET  /api/v1/recommendations/history/{recommendation_id}
```

## Train a Real Recommendation Model

Create a labeled CSV dataset where each row is one scene. Required columns:

```text
ei,audio_energy,motion,object_score,emotion_confidence,scene_type,visual_emotion,audio_mood,popularity_score,engagement_rate,priority_score,focus_area
```

Example target values:

- `priority_score`: integer 0..100
- `focus_area`: one of `emotional intensity`, `soundtrack energy`, `motion and pacing`, `visual impact`, `emotion clarity`

The categorical values must match the live pipeline's vocabulary:

- `scene_type`: `Action`, `Thriller`, `Dialogue`, `Emotional`, `Romance`, `Drama`
- `visual_emotion`: `angry`, `disgust`, `fear`, `happy`, `sad`, `surprise`, `neutral` (DeepFace)
- `audio_mood`: `intense`, `emotional`, `suspense`, `calm`

### Generate a large synthetic training set

`training/recommendation_labels.csv` only has 25 hand-written rows, which memorizes
instantly instead of generalizing. Use the generator to build thousands of rows
across the full feature space with the correct categorical vocabulary:

```bash
python scripts/generate_synthetic_training_data.py --rows 6000 --seed 7 --output training/recommendation_labels_synthetic.csv
```

Train and export model artifacts:

```bash
python scripts/train_recommendation_model.py --input training/recommendation_labels_synthetic.csv --output artifacts/recommendation_model.joblib --metrics artifacts/recommendation_model_metrics.json
```

After training, restart the API (the model bundle is cached in-process). The response includes `summary.recommendation_model_version`, `summary.mean_prediction_confidence`, and `model_metrics` from validation.

If no artifact exists and `RECOMMENDATION_MODEL_REQUIRED=true`, recommendation endpoints return `503`. If the model's focus-area confidence is low for one specific scene, that scene falls back to the deterministic weakest-signal rule instead of failing the whole request.

Use `/generate` when the frontend already has an emotion analysis result.

Use `/latest` when you want this backend to fetch the latest saved emotion analysis from the emotional analysis backend and generate recommendations from it.

Use `/history` to retrieve recommendation outputs saved by this component.

## Firestore

Create `.env` from `.env.example` and set:

```text
FIREBASE_CREDENTIALS_PATH
FIREBASE_PROJECT_ID
FIREBASE_COLLECTION
```

Recommended collection:

```text
trailer_recommendations
```

## Research Description

This component implements an explainable recommendation layer. It identifies weak scene-level signals using emotional intensity, soundtrack energy, motion, object impact, and emotion confidence. Recommendations are ranked using an RPS score and include the exact time frame, problem, evidence, and suggested solution.
