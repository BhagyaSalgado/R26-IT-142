"""Seed the backend with sample trailer analysis data.

Run with:
    python scripts/seed_firestore.py

If FIREBASE_MOCK_MODE=true, this seeds only the process memory and is mainly useful
when imported from a running process. For real Firestore seeding, set FIREBASE_MOCK_MODE=false.
"""

from app.core.config import get_settings
from app.dependencies import get_repository
from app.services.analysis_service import AnalysisService

SAMPLE_TRAILERS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/aqz-KE-bpKQ",
    "https://www.youtube.com/watch?v=ysz5S6PUM-U",
]


def main():
    settings = get_settings()
    repo = get_repository()
    service = AnalysisService(settings=settings, repository=repo)
    for url in SAMPLE_TRAILERS:
        result = service.analyze(url)
        print(f"Seeded {result.video_id}: {result.prediction.predicted_reaction}")


if __name__ == "__main__":
    main()
