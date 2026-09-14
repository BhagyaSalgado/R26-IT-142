# R26-IT-142

AI-Powered Movie Trailer Analyzer — research project monorepo.

## Repository Structure

Each team module lives on its own branch (`Comment-Sentiment`, `Popularity-Metrics-Analysis`,
`Recommendation-Engine`, `Video-And-Audio-Analysis`) and is merged into `dev`/`main` under a
namespaced subfolder to avoid collisions between services:

```text
R26-IT-142/
├── README.md
├── frontend/
│   └── movie-trailer-analyzer/        # shared React/TypeScript frontend
└── backend/
    ├── sentiment-analysis-service/    # Comment-Sentiment module
    ├── popularity-analysis-service/   # Popularity-Metrics-Analysis module
    ├── recommendation-service/        # Recommendation-Engine module
    └── video-audio-analysis-service/  # Video-And-Audio-Analysis module
```

## Popularity Metrics Analysis Service

This branch adds the **Popularity Metrics Analysis** FastAPI microservice under
[`backend/popularity-analysis-service`](backend/popularity-analysis-service), covering
YouTube trailer metric collection, feature engineering, and popularity prediction. See
that folder's own README for setup and API details.
