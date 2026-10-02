# Movie Trailer Recommendation Engine

Backend for the **Recommendation and Insight** component of the movie-trailer analyser.

The service consumes scene-level outputs produced by the audio/video backend. It builds a trailer baseline, infers genre and structure, detects editorial problems, and returns ranked, evidence-based recommendations for the frontend. It does not modify or re-edit uploaded trailers.

## Main capabilities

- Genre-sensitive trailer profiling and empirical genre norms
- Dynamic trailer-phase and pacing analysis
- Supervised editorial-defect classification
- Within-trailer anomaly and visual-integrity checks
- Explainable recommendations with scenes, timeframes, evidence, severity, and actions
- Firebase token verification and user-scoped Firestore history
- Optional popularity and sentiment context
- Deterministic local recommendation wording with optional language-model enhancement

## Project structure

```text
recommendation-backend/
├── app/
│   ├── api/routes.py
│   ├── core/config.py
│   ├── firebase/firebase_config.py
│   ├── repositories/recommendation_repository.py
│   ├── schemas/recommendation_schema.py
│   └── services/
├── artifacts/
│   ├── genre_norms/
│   ├── magnitude_bands.json
│   └── problem_model.joblib
├── scripts/
├── tests/
├── .env.example
└── requirements.txt
```

## Requirements

- Python 3.11 recommended
- Audio/video backend at `http://127.0.0.1:8000`
- Popularity backend at `http://127.0.0.1:8001` when popularity context is required
- Firebase credentials for authenticated access and Firestore history

## Installation

```powershell
cd recommendation-backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `FIREBASE_CREDENTIALS_PATH` in `.env` to a local service-account file. Never commit `.env` or the service-account JSON file.

## Authentication

Recommendation and history endpoints require a Firebase ID token by default:

```http
Authorization: Bearer <firebase-id-token>
```

For isolated local development only, authentication can be disabled explicitly:

```env
ALLOW_ANONYMOUS_ACCESS=true
```

Keep `ALLOW_ANONYMOUS_ACCESS=false` in shared and production environments. The health endpoint remains public.

## Run

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

Open the API documentation at `http://127.0.0.1:8010/docs`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service metadata |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/recommendations/generate` | Generate recommendations from supplied analysis data |
| GET | `/api/v1/recommendations/latest` | Generate recommendations for the latest saved analysis |
| GET | `/api/v1/recommendations/prediction/{prediction_id}` | Generate recommendations for a selected prediction |
| GET | `/api/v1/recommendations/history` | List the authenticated user's history |
| GET | `/api/v1/recommendations/history/{recommendation_id}` | Load one user-scoped result |

## Configuration

The environment variables are documented in `.env.example`. The principal settings are:

- `EMOTION_API_BASE_URL`
- `POPULARITY_API_BASE_URL`
- `CORS_ORIGINS`
- `ALLOW_ANONYMOUS_ACCESS`
- `FIREBASE_CREDENTIALS_PATH`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_COLLECTION`
- `FIRESTORE_TIMEOUT_SECONDS`
- `OMDB_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

The OMDb and language-model keys are optional. Without them, the service uses available scene evidence and deterministic local recommendation text.

## Tests

Run the complete suite without creating local cache files:

```powershell
python -B -m pytest -p no:cacheprovider -q
```

The tests cover recommendation quality, genre-sensitive behaviour, authentication, user-scoped persistence, API routes, deduplication, and response structure. GitHub Actions runs this command for recommendation-backend changes on `Recommendation-Engine`.

## Research and training utilities

- `scripts/build_genre_norms.py` builds empirical genre trajectories.
- `scripts/build_magnitude_bands.py` derives calibrated magnitude bands.
- `scripts/train_problem_model.py` trains the editorial-defect classifier.
- `scripts/validate_genre_norms.py` validates stored norm artefacts.
- `scripts/collect_genre_trailers.py`, `extract_colour_features.py`, and `retry_failed_chunked.py` support corpus preparation.

Trained runtime artefacts are committed under `artifacts/` so the service can run without retraining.

## Security and deployment notes

- Keep authentication enabled outside isolated local development.
- Store service-account and API credentials outside Git.
- Use HTTPS and a managed secret store in production.
- Restrict CORS origins to deployed frontend URLs.
- Apply request-size, timeout, and retention limits at the gateway and upstream analysis service.
- Treat recommendations as decision support; the editor retains final creative control.
