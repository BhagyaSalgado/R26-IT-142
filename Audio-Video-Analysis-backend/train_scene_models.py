import os
import sys
import json
import joblib
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath("."))

from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score, f1_score, precision_score, recall_score, confusion_matrix

from app.ml.feature_assembly import assemble_features, build_object_vocab, FACE_EMOTIONS, AUDIO_EMOTIONS

TARGET_CLASSES = ["Action", "Adventure", "Comedy", "Dialogue", "Drama", "Emotional", "Romance", "Suspense", "Thriller", "Unknown"]

def load_ground_truth_with_real_features():
    gt_path = Path("ground_truth_shots.csv")
    if not gt_path.exists():
        raise FileNotFoundError("ground_truth_shots.csv not found.")

    gt_df = pd.read_csv(gt_path)
    print(f"[Train] Loaded {len(gt_df)} shots from {gt_path} across {gt_df['trailer_id'].nunique()} trailers")

    outputs_dir = Path("storage/outputs")
    feature_rows = []
    
    for csv_file in outputs_dir.glob("*/final_system_output.csv"):
        try:
            df = pd.read_csv(csv_file)
            if not df.empty and "scene" in df.columns:
                tid = csv_file.parent.name
                df["trailer_id_raw"] = tid
                feature_rows.append(df)
        except Exception:
            continue

    if not feature_rows:
        raise ValueError("No feature files found in storage/outputs.")

    all_feats_df = pd.concat(feature_rows, ignore_index=True)
    print(f"[Train] Found {len(all_feats_df)} real analyzed shot feature records in storage/outputs")

    # Match ground truth shots with real analyzed visual & audio feature rows
    valid_samples = []
    for _, row in gt_df.iterrows():
        tid = str(row["trailer_id"])
        sid = int(row["scene_id"])
        
        matching = all_feats_df[(all_feats_df["trailer_id_raw"].str.contains(tid[:15])) & (all_feats_df["scene"] == sid)]
        if not matching.empty:
            match_row = matching.iloc[0].to_dict()
            match_row["trailer_id"] = tid
            match_row["human_scene_type"] = row["human_scene_type"]
            valid_samples.append(match_row)

    valid_df = pd.DataFrame(valid_samples)
    print(f"[Train] Successfully matched {len(valid_df)} shots with 100% real visual & audio feature vectors")
    return valid_df

def train_and_evaluate_scene_models():
    df_train = load_ground_truth_with_real_features()

    # Build object vocabulary from dataset
    vocab = build_object_vocab(df_train)
    vocab_path = Path("app/models/trained/object_vocab.json")
    vocab_path.parent.mkdir(parents=True, exist_ok=True)
    vocab_path.write_text(json.dumps(vocab, indent=2), encoding="utf-8")
    print(f"[Train] Saved object vocabulary ({len(vocab)} items) to {vocab_path}")

    # Generate feature matrix
    X_df = assemble_features(df_train, vocab)
    
    # Save feature schema
    schema = list(X_df.columns)
    schema_path = Path("app/models/trained/scene_feature_schema.json")
    schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"[Train] Saved feature schema ({len(schema)} features) to {schema_path}")

    # Encode target labels
    le = LabelEncoder()
    le.fit(TARGET_CLASSES)
    y = le.transform(df_train["human_scene_type"].values)

    groups = df_train["trailer_id"].values

    print("\n[Train] Starting 5-Fold GroupKFold Cross-Validation by trailer_id (Zero Leakage)...")
    gkf = GroupKFold(n_splits=min(5, len(np.unique(groups))))

    y_true_all = []
    y_pred_all = []
    y_prob_all = []

    base_rf = RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=2, random_state=42, n_jobs=-1, class_weight="balanced")

    for fold, (train_idx, val_idx) in enumerate(gkf.split(X_df, y, groups=groups), start=1):
        X_train, y_train = X_df.iloc[train_idx], y[train_idx]
        X_val, y_val = X_df.iloc[val_idx], y[val_idx]
        val_trailers = np.unique(groups[val_idx])

        clf = CalibratedClassifierCV(estimator=base_rf, cv=3)
        clf.fit(X_train, y_train)

        preds = clf.predict(X_val)
        probs = clf.predict_proba(X_val)

        y_true_all.extend(y_val)
        y_pred_all.extend(preds)
        y_prob_all.extend(probs)

        fold_acc = accuracy_score(y_val, preds)
        fold_f1 = f1_score(y_val, preds, average="macro", zero_division=0)
        print(f"  Fold {fold} ({len(val_trailers)} test trailers, {len(val_idx)} shots): Acc = {fold_acc:.4f}, Macro F1 = {fold_f1:.4f}")

    # Global Validation Metrics
    y_true_all = np.array(y_true_all)
    y_pred_all = np.array(y_pred_all)

    acc = accuracy_score(y_true_all, y_pred_all)
    macro_f1 = f1_score(y_true_all, y_pred_all, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true_all, y_pred_all, average="weighted", zero_division=0)
    macro_prec = precision_score(y_true_all, y_pred_all, average="macro", zero_division=0)
    macro_rec = recall_score(y_true_all, y_pred_all, average="macro", zero_division=0)

    print("\n==================================================")
    print("5-FOLD HELD-OUT TRAILER CROSS-VALIDATION RESULTS")
    print("==================================================")
    print(f"Accuracy:          {acc:.4f}")
    print(f"Macro Precision:   {macro_prec:.4f}")
    print(f"Macro Recall:      {macro_rec:.4f}")
    print(f"Macro F1:          {macro_f1:.4f}")
    print(f"Weighted F1:       {weighted_f1:.4f}")
    print("\nPer-Class Performance:")
    target_names = le.inverse_transform(np.unique(y_true_all))
    print(classification_report(y_true_all, y_pred_all, target_names=target_names, zero_division=0))

    # Confusion Matrix
    cm = confusion_matrix(y_true_all, y_pred_all)
    cm_df = pd.DataFrame(cm, index=target_names, columns=target_names)
    print("\nConfusion Matrix:")
    print(cm_df)

    # Train final production model on full dataset
    print(f"\n[Train] Fitting final production model on {len(df_train)} real shot dataset...")
    final_clf = CalibratedClassifierCV(estimator=base_rf, cv=3)
    final_clf.fit(X_df, y)

    # Save production artifacts
    model_path = Path("app/models/trained/scene_type_clf.pkl")
    le_path = Path("app/models/trained/label_encoder_scene_type.pkl")

    joblib.dump(final_clf, model_path)
    joblib.dump(le, le_path)

    print(f"[Train] Production model saved to {model_path}")
    print(f"[Train] Label encoder saved to {le_path}")

if __name__ == "__main__":
    train_and_evaluate_scene_models()
