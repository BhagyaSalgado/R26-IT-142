import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer

FACE_EMOTIONS = ["happy", "sad", "angry", "fear", "surprise", "disgust", "neutral", "unknown"]# List of facial emotion categories used by the system
AUDIO_EMOTIONS = ["happy", "sad", "angry", "fear", "surprise", "disgust", "neutral"] # List of audio emotion categories used by the system

def build_object_vocab(df: pd.DataFrame) -> list[str]:   # Build the object vocabulary from objects that actually appear in the input dataset
    """Derive the multi-hot object vocabulary from the data actually seen."""
    vocab = set()
    for objs in df["objects"].fillna(""):  # Read the "objects" column. fillna("") replaces missing values with an empty string.
        for o in str(objs).split(","): # Convert the object value to a string and split multiple objects using commas
            o = o.strip().lower() # Remove extra spaces and convert the object name to lowercase
            if o:  # Add the object to the vocabulary if it is not empty
                vocab.add(o)
    return sorted(vocab) # Sort the vocabulary alphabetically and return it as a list
# Convert the raw scene-level pipeline output into a numerical feature matrix
def assemble_features(df: pd.DataFrame, object_vocab: list[str]) -> pd.DataFrame:
    """Turn raw per-scene pipeline output into a numeric feature matrix."""
    feats = pd.DataFrame(index=df.index) # Create an empty DataFrame using the same index as the original input DataFrame

    # Continuous signals
    for col in ["M", "A", "O", "F", "tempo_bpm", "mfcc_mean", "spectral_centroid"]:
        if col in df.columns:  # Check whether the column exists in the input data
            feats[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:  # If the column does not exist,create it with a default value of 0
            feats[col] = 0.0

# One-hot face emotion # Get the face emotion column.If "face_emotion" does not exist,use "unknown" for every row.
    face = df.get("face_emotion", pd.Series(["unknown"] * len(df))).fillna("unknown").astype(str).str.lower()
    for e in FACE_EMOTIONS:   # Create one binary feature for each facial emotion
        feats[f"face_{e}"] = (face == e).astype(int)   # If the face emotion matches the current emotion,assign 1.

# One-hot audio emotion
    audio = df.get("audio_emotion", pd.Series(["neutral"] * len(df))).fillna("neutral").astype(str).str.lower()
    for e in AUDIO_EMOTIONS:  # Create one binary feature for each audio emotion
        feats[f"audio_{e}"] = (audio == e).astype(int) # Assign 1 when the current audio emotion matches  the emotion being processed.Otherwise assign 0.

 # Multi-hot objects over the learned vocabulary- MULTI-HOT ENCODING FOR DETECTED OBJECTS
    obj_lists = df.get("objects", pd.Series([""] * len(df))).fillna("").apply(  # Get the detected objects from the "objects" column.If the column does not exist,use an empty string for every row.
        lambda s: [o.strip().lower() for o in str(s).split(",") if o.strip()]
    )
    # Check whether an object vocabulary was created
    if object_vocab:  # Create a MultiLabelBinarizer using the learned object vocabulary
        mlb = MultiLabelBinarizer(classes=object_vocab)
        obj_matrix = mlb.fit_transform(obj_lists)  # Convert the list of detected objects into binary 0/1 features.
        obj_df = pd.DataFrame(obj_matrix, columns=[f"obj_{c}" for c in object_vocab], index=df.index)  # Convert the binary object matrix into a Pandas DataFrame.
        feats = pd.concat([feats, obj_df], axis=1) # Combine the object features with the other features

    return feats      # Return the complete numerical feature matrix
