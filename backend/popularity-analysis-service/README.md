
# AI-Powered Movie Trailer Analyzer — Popularity Metrics FastAPI Microservice

This project is a **separate FastAPI backend microservice** for the **Popularity Metrics Analysis** component of the AI-Powered Movie Trailer Analyzer research project.

It is ready to start development with:

- FastAPI backend structure
- Firebase Firestore integration
- YouTube trailer URL parsing
- Optional YouTube Data API support
- Simulated trailer metrics when no API key is configured
- Feature engineering for popularity metrics
- Simulated ML prediction service
- Firestore collections for trailers, metrics, features, predictions, history, and model evaluations
- Placeholder training/integration files for future real ML models

The current ML logic is intentionally simulated. You can later replace the simulated predictor with your trained Logistic Regression, Random Forest, or SVM model files.

---

## 1. Project Structure

```text
movie-trailer-popularity-service/
│
├── app/
│   ├── main.py
│   ├── dependencies.py
│   │
│   ├── api/v1/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── analysis.py
│   │       ├── health.py
│   │       ├── model.py
│   │       └── trailers.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── exceptions.py
│   │
│   ├── firebase/
│   │   └── firebase_app.py
│   │
│   ├── repositories/
│   │   ├── base.py
│   │   ├── firestore_repository.py
│   │   └── memory_repository.py
│   │
│   ├── schemas/
│   │   ├── analysis.py
│   │   ├── common.py
│   │   ├── evaluation.py
│   │   ├── features.py
│   │   ├── metrics.py
│   │   ├── prediction.py
│   │   └── trailer.py
│   │
│   ├── services/
│   │   ├── analysis_service.py
│   │   ├── feature_engineering_service.py
│   │   ├── prediction_service.py
│   │   ├── report_service.py
│   │   └── youtube_service.py
│   │
│   ├── ml/
│   │   ├── model_registry.py
│   │   ├── simulated_model.py
│   │   └── train_placeholder.py
│   │
│   └── utils/
│       └── youtube.py
│
├── firebase/
│   ├── firestore.rules
│   ├── indexes.json
│   └── serviceAccountKey.example.json
│
├── scripts/
│   ├── create_dummy_model_files.py
│   └── seed_firestore.py
│
├── tests/
│   ├── test_feature_engineering.py
│   └── test_youtube_parser.py
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── instruction.txt
├── requirements.txt
└── sample_requests/
    └── postman_examples.json
```

---

## 2. Create and Activate Python Virtual Environment

### Windows CMD

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Copy the example file:

```bash
cp .env.example .env
```

For first local testing, keep:

```env
FIREBASE_MOCK_MODE=true
```

This lets the backend run without a real Firebase service account.

For real Firestore integration:

1. Create a Firebase project.
2. Enable Cloud Firestore.
3. Generate a Firebase Admin SDK service account JSON file.
4. Put it in the project root as `serviceAccountKey.json`.
5. Update `.env`:

```env
FIREBASE_MOCK_MODE=false
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
```

Optional YouTube API support:

```env
YOUTUBE_API_KEY=your_youtube_data_api_key
```

If `YOUTUBE_API_KEY` is empty, the backend generates simulated trailer metrics for testing.

---

## 5. Run the FastAPI Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## 6. Main API Endpoint

### Analyze Trailer

```http
POST /api/v1/analyze
```

Request body:

```json
{
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

Response example:

```json
{
  "status": "success",
  "message": "Trailer analyzed successfully.",
  "data": {
    "video_id": "dQw4w9WgXcQ",
    "trailer": {
      "id": "dQw4w9WgXcQ",
      "youtube_video_id": "dQw4w9WgXcQ",
      "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "title": "Simulated Movie Trailer dQw4w9WgXcQ",
      "channel_name": "Simulated Studio",
      "published_at": "2026-01-01T00:00:00Z",
      "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
      "created_at": "2026-05-07T00:00:00Z",
      "updated_at": "2026-05-07T00:00:00Z"
    },
    "metrics": {
      "id": "dQw4w9WgXcQ",
      "trailer_id": "dQw4w9WgXcQ",
      "view_count": 1500000,
      "like_count": 78000,
      "comment_count": 4200,
      "favorite_count": 0,
      "collected_at": "2026-05-07T00:00:00Z",
      "source": "simulated"
    },
    "features": {
      "id": "dQw4w9WgXcQ",
      "trailer_id": "dQw4w9WgXcQ",
      "video_age_days": 126,
      "engagement_rate": 0.0548,
      "like_ratio": 0.052,
      "comment_rate": 0.0028,
      "comments_per_1000_views": 2.8,
      "views_per_day": 11904.76,
      "growth_rate": 11904.76,
      "popularity_score": 72.44,
      "created_at": "2026-05-07T00:00:00Z"
    },
    "prediction": {
      "id": "dQw4w9WgXcQ",
      "trailer_id": "dQw4w9WgXcQ",
      "predicted_reaction": "HIGH_REACTION",
      "confidence_score": 0.86,
      "model_name": "SimulatedPopularityClassifier",
      "model_version": "v0.1-simulated",
      "probabilities": {
        "LOW_REACTION": 0.05,
        "MEDIUM_REACTION": 0.23,
        "HIGH_REACTION": 0.72
      },
      "recommendation": "Audience engagement is strong. Consider increasing trailer promotion and retargeting campaigns.",
      "created_at": "2026-05-07T00:00:00Z"
    }
  }
}
```

---

## 7. Useful Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/api/v1/health` | Versioned health check |
| POST | `/api/v1/analyze` | Analyze one YouTube trailer |
| POST | `/api/v1/batch-analyze` | Analyze multiple YouTube trailers |
| GET | `/api/v1/trailers/{video_id}` | Get trailer details |
| GET | `/api/v1/trailers/{video_id}/metrics` | Get latest metrics |
| GET | `/api/v1/trailers/{video_id}/features` | Get calculated features |
| GET | `/api/v1/trailers/{video_id}/prediction` | Get prediction output |
| GET | `/api/v1/history` | Get latest analysis history |
| GET | `/api/v1/model/performance` | Get simulated model performance |
| POST | `/api/v1/model/train-simulated` | Create simulated model evaluation record |

---

## 8. Firestore Collections

When `FIREBASE_MOCK_MODE=false`, the service writes to these Firestore collections:

```text
trailers
trailer_metrics
trailer_features
predictions
analysis_history
model_evaluations
```

Recommended Firestore document pattern:

```text
trailers/{video_id}
trailer_metrics/{video_id}
trailer_features/{video_id}
predictions/{video_id}
analysis_history/{uuid}
model_evaluations/{uuid}
```

---

## 9. Replacing Simulated ML Later

Currently the backend uses:

```text
app/ml/simulated_model.py
```

Later, after training your real model, add your files into:

```text
app/ml/artifacts/
```

Suggested real model files:

```text
app/ml/artifacts/preprocessor.pkl
app/ml/artifacts/random_forest_model.pkl
app/ml/artifacts/logistic_regression_model.pkl
app/ml/artifacts/svm_model.pkl
```

Then update:

```text
app/services/prediction_service.py
```

Replace this:

```python
self.model = SimulatedPopularityModel()
```

with your real model loading logic.

---

## 10. Docker Run

```bash
docker build -t popularity-metrics-service .
docker run --env-file .env -p 8000:8000 popularity-metrics-service
```

Or:

```bash
docker compose up --build
```

---

## 11. Development Notes

- Do not commit the real Firebase service account JSON file.
- Use `.env` for API keys and Firebase paths.
- Keep `FIREBASE_MOCK_MODE=true` during early development.
- Set `FIREBASE_MOCK_MODE=false` only after Firebase Firestore is configured.
- The simulated prediction output is suitable for frontend integration and thesis demonstration, not final research evaluation.
