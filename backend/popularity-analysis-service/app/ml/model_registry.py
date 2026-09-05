from __future__ import annotations

from pathlib import Path
from typing import Dict


class ModelRegistry:
    """Checks whether real trained model artifacts exist."""

    def __init__(self, artifacts_dir: str = "app/ml") -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def expected_artifacts(self) -> Dict[str, str]:
        return {
            "preprocessor": str(self.artifacts_dir / "preprocessor.pkl"),
            "feature_columns": str(self.artifacts_dir / "feature_columns.json"),
            "model_evaluation": str(self.artifacts_dir / "model_evaluation.json"),
            "random_forest": str(self.artifacts_dir / "random_forest_model.pkl"),
            "logistic_regression": str(self.artifacts_dir / "logistic_regression_model.pkl"),
            "svm": str(self.artifacts_dir / "svm_model.pkl"),
        }

    def artifact_status(self) -> Dict[str, bool]:
        return {name: Path(path).exists() for name, path in self.expected_artifacts().items()}
