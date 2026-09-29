import json
from pathlib import Path # Import Path for handling file and directory paths
import joblib # Import Path for handling file and directory paths
import tensorflow as tf # Import TensorFlow for loading the trained deep-learning video model
from app.core.config import settings
# Class responsible for loading and managing all AI/ML models used by the system
class ModelManager:
    def __init__(self):
        self.model_dir: Path = settings.MODEL_DIR # Define the main directory containing the models
        self.trained_dir: Path = settings.MODEL_DIR / "trained"  # Define the directory containing trained models
        # VIDEO MODEL
        self.video_model = None
        self.video_label_names = {}
        # METADATA MODEL
        self.metadata_bundle = None
        self.metadata_model = None
        self.metadata_feature_cols = []
        # YOLO OBJECT DETECTION
        self.yolo_model = None
        self.deepface = None

        # Real face emotion pipeline (YuNet + HSEmotion)
        self.face_detector = None # Face detector using YuNet
        self.emotion_recognizer = None  # Facial emotion recognizer using HSEmotion

        # CLIP zero-shot scene type classifier      # CLIP SCENE CLASSIFICATION
        self.clip_model = None # Stores the CLIP model used for zero-shot scene classification
        self.clip_processor = None # Stores the CLIP processor used to preprocess images/text for CLIP

        # Zero-Shot Scene Type Classifier (legacy)
        self.zero_shot_classifier = None
        self.audio_emotion_classifier = None
        self.loaded = False
# LOAD ALL MODELS
    def load_models(self):
        if self.loaded:
            return self
# DEFINE REQUIRED MODEL FILE PATHS
        
        video_model_path = self.model_dir / "video_emotion_mobilenet.keras" # Path to the trained MobileNet video emotion model
        video_labels_path = self.model_dir / "video_label_names.json" # Path to the video emotion label names
        metadata_path = self.model_dir / "metadata_favorability_model.pkl" # Path to the metadata favorability model
        # Check whether the required video model files exist
        missing = [str(p) for p in [video_model_path, video_labels_path] if not p.exists()]
        if missing:  # If required files are missing,stop execution and report the missing files
            raise FileNotFoundError("Missing required model files: " + ", ".join(missing))
 # LOAD VIDEO EMOTION MODEL
        self.video_model = tf.keras.models.load_model(video_model_path)    # Load the trained MobileNet-based video model

        labels_raw = json.loads(video_labels_path.read_text(encoding="utf-8"))  # Read the video emotion labels from JSON
        self.video_label_names = {int(k): v for k, v in labels_raw.items()} # Convert JSON keys to integers and store the emotion label names
# LOAD METADATA MODEL
        if metadata_path.exists(): # Check whether the metadata model file exists
            self.metadata_bundle = joblib.load(metadata_path) # Load the trained metadata model bundle
            self.metadata_model = self.metadata_bundle.get("model")
            self.metadata_feature_cols = self.metadata_bundle.get("feature_cols", [])

        # Load Local Fast Audio Emotion Classifier (Trained Random Forest)
        audio_rf_path = self.model_dir / "audio_emotion_rf.pkl" # Path to the trained Random Forest audio emotion model
        audio_scaler_path = self.model_dir / "audio_scaler.pkl"  # Path to the audio feature scaler
        audio_le_path = self.model_dir / "audio_label_encoder.pkl" # Path to the audio emotion label encoder
   # Check whether all three audio model files exist
        if audio_rf_path.exists() and audio_scaler_path.exists() and audio_le_path.exists():
            try:
                self.audio_emotion_model = joblib.load(audio_rf_path)
                self.audio_scaler = joblib.load(audio_scaler_path)
                self.audio_label_encoder = joblib.load(audio_le_path)
                print("[ModelManager] Local Audio Emotion ML Model loaded successfully.")  # Display a successful loading message
            except Exception as e:  # Handle errors while loading the audio model
                # Display a warning message
                print(f"[ModelManager] Warning: Failed to load Audio Emotion model ({e})")
                self.audio_emotion_model = None
                self.audio_scaler = None
                self.audio_label_encoder = None
        else:
            self.audio_emotion_model = None
            self.audio_scaler = None
            self.audio_label_encoder = None
# LOAD SCENE CLASSIFICATION MODEL
        # Load Local Fast Production Scene Classifier (Trained Calibrated Random Forest)
        scene_clf_path = self.trained_dir / "scene_type_clf.pkl"
        scene_le_path = self.trained_dir / "label_encoder_scene_type.pkl"
        scene_vocab_path = self.trained_dir / "object_vocab.json"
        scene_schema_path = self.trained_dir / "scene_feature_schema.json"

        if scene_clf_path.exists() and scene_le_path.exists():
            try:
                self.scene_classifier = joblib.load(scene_clf_path)
                self.scene_label_encoder = joblib.load(scene_le_path)
                self.object_vocab = json.loads(scene_vocab_path.read_text(encoding="utf-8")) if scene_vocab_path.exists() else []
                self.scene_feature_schema = json.loads(scene_schema_path.read_text(encoding="utf-8")) if scene_schema_path.exists() else []
                print("[ModelManager] Production Scene Classifier loaded successfully.")
            except Exception as e:
                print(f"[ModelManager] Warning: Failed to load Scene Classifier ({e})")
                self.scene_classifier = None
                self.scene_label_encoder = None
                self.object_vocab = []
                self.scene_feature_schema = []
        else:
            self.scene_classifier = None
            self.scene_label_encoder = None
            self.object_vocab = []
            self.scene_feature_schema = []
 # LOAD YOLO OBJECT DETECTION MODEL
        if settings.USE_YOLO: # Check whether YOLO is enabled in the system settings
            try:
                from ultralytics import YOLO
                self.yolo_model = YOLO("yolov8s.pt")
            except Exception:
                self.yolo_model = None
 # LOAD DEEPFACE  # Check whether DeepFace is enabled
        if settings.USE_DEEPFACE:
            try:
                from deepface import DeepFace
                self.deepface = DeepFace
            except Exception:
                self.deepface = None

        # ── Real face detection + emotion pipeline (YuNet + HSEmotion ONNX) ──────
        try:      # Try to load the real face detection and emotion recognition pipeline
            from app.ml.face_detector import FaceDetector
            from app.ml.emotion_recognizer import EmotionRecognizer
            self.face_detector = FaceDetector(score_threshold=0.45, nms_threshold=0.30)
            self.emotion_recognizer = EmotionRecognizer()
            print("[ModelManager] YuNet + HSEmotion face emotion pipeline loaded successfully.")
        except Exception as e:
            print(f"[ModelManager] Warning: Face emotion pipeline unavailable ({e}) — DeepFace fallback active.")
            self.face_detector = None
            self.emotion_recognizer = None
# LOAD CLIP SCENE CLASSIFIER
        # ── CLIP zero-shot scene type classifier ────────────────────────────────
        try:  # Try to load CLIP for zero-shot scene classification
            from transformers import CLIPProcessor, CLIPModel
            import torch            # Import PyTorch because CLIP uses it
            print("[ModelManager] Loading CLIP (openai/clip-vit-base-patch32) for scene classification...")   # Display a message before loading CLIP
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")  # Load the pre-trained CLIP model
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model.eval()
            print("[ModelManager] CLIP scene classifier loaded successfully.")
        except Exception as e:
            print(f"[ModelManager] Warning: CLIP unavailable ({e}) — rule-based scene fallback active.")
            self.clip_model = None
            self.clip_processor = None

        self.loaded = True
        return self

model_manager = ModelManager()
