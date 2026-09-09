from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd

REACTION_CLASSES = ["LOW_REACTION", "MEDIUM_REACTION", "HIGH_REACTION"]


class TrainedPopularityModel:
    """Loads the real Colab-trained model artifacts and predicts audience reaction.

    Required files inside artifacts_dir:
      - preprocessor.pkl
      - feature_columns.json
      - one of: random_forest_model.pkl, logistic_regression_model.pkl, svm_model.pkl
    """

    MODEL_FILES = {
        "random_forest": "random_forest_model.pkl",
        "logistic_regression": "logistic_regression_model.pkl",
        "svm": "svm_model.pkl",
    }

    DISPLAY_NAMES = {
        "random_forest": "RandomForestClassifier",
        "logistic_regression": "LogisticRegression",
        "svm": "SVM",
    }

    def __init__(self, artifacts_dir: str = "app/ml", model_type: str = "random_forest") -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.model_type = model_type

        if self.model_type not in self.MODEL_FILES:
            raise ValueError(
                f"Unsupported MODEL_TYPE={self.model_type}. "
                f"Use one of: {', '.join(self.MODEL_FILES.keys())}"
            )

        self.preprocessor_path = self.artifacts_dir / "preprocessor.pkl"
        self.feature_columns_path = self.artifacts_dir / "feature_columns.json"
        self.model_path = self.artifacts_dir / self.MODEL_FILES[self.model_type]

        self._validate_files()

        self.preprocessor = joblib.load(self.preprocessor_path)
        self.model = joblib.load(self.model_path)
        self.feature_columns = self._load_feature_columns()
        self.model_name = self.DISPLAY_NAMES[self.model_type]

    def _validate_files(self) -> None:
        missing = [
            str(path)
            for path in [self.preprocessor_path, self.feature_columns_path, self.model_path]
            if not path.exists()
        ]
        if missing:
            raise FileNotFoundError("Missing trained model artifact(s): " + ", ".join(missing))

    def _load_feature_columns(self) -> list[str]:
        with open(self.feature_columns_path, "r", encoding="utf-8") as file:
            columns = json.load(file)
        if not isinstance(columns, list) or not columns:
            raise ValueError("feature_columns.json must contain a non-empty JSON list.")
        return [str(col) for col in columns]

    def predict(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        row = {}
        for col in self.feature_columns:
            value = features.get(col, 0)
            try:
                row[col] = float(value)
            except (TypeError, ValueError):
                row[col] = 0.0

        input_df = pd.DataFrame([row], columns=self.feature_columns)
        processed = self.preprocessor.transform(input_df)

        predicted = str(self.model.predict(processed)[0])
        probabilities = self._predict_probabilities(processed, predicted)
        confidence = max(probabilities.values()) if probabilities else 0.0

        return predicted, round(float(confidence), 4), probabilities

    def _predict_probabilities(self, processed, predicted: str) -> Dict[str, float]:
        # Logistic Regression, Random Forest, and SVC(probability=True) support predict_proba.
        if hasattr(self.model, "predict_proba"):
            prob_values = self.model.predict_proba(processed)[0]
            classes = [str(item) for item in self.model.classes_]
            return {label: round(float(prob), 4) for label, prob in zip(classes, prob_values)}

        # Fallback for models without probability support.
        return {label: 1.0 if label == predicted else 0.0 for label in REACTION_CLASSES}
