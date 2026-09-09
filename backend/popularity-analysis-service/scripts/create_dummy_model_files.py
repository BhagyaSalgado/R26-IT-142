from pathlib import Path

ARTIFACTS = [
    "preprocessor.pkl",
    "random_forest_model.pkl",
    "logistic_regression_model.pkl",
    "svm_model.pkl",
]


def main():
    artifacts_dir = Path("app/ml/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACTS:
        path = artifacts_dir / name
        if not path.exists():
            path.write_text("This is a placeholder. Replace with a real trained model file.\n", encoding="utf-8")
            print(f"Created {path}")
        else:
            print(f"Already exists {path}")


if __name__ == "__main__":
    main()
