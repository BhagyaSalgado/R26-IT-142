"""
Facial Emotion Recognition Engine using HSEmotion (EfficientNet-B0 on AffectNet/RAF-DB).
Provides per-frame emotion probability distributions and batch inference.
"""

import os
from pathlib import Path    # Import Path for handling file and folder paths
import urllib.request      # Import urllib for downloading the emotion recognition model
import numpy as np
import onnxruntime as ort  # Import ONNX Runtime to run the trained ONNX emotion recognition model
import cv2

# Standard project emotion labels (7 categorical emotions)# Define the standard seven emotion categories used by the system
TARGET_EMOTIONS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
# URL of the pre-trained HSEmotion ONNX model
HSEMOTION_MODEL_URL = "https://github.com/HSE-asavchenko/face-emotion-recognition/blob/main/models/affectnet_emotions/onnx/enet_b0_8_best_vgaf.onnx?raw=true"
DEFAULT_WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"     # Define the default directory where the model weights will be stored

# Create the Facial Emotion Recognition class
class EmotionRecognizer:      # Constructor for the EmotionRecognizer
    def __init__(self, model_name: str = "enet_b0_8_best_vgaf", weights_dir: Path | None = None):
        self.model_name = model_name  # model_name = name of the ONNX emotion model  # Store the selected model name
        self.weights_dir = weights_dir or DEFAULT_WEIGHTS_DIR   # weights_dir = optional directory for storing model weights   # Use the provided weights directory
        self.weights_dir.mkdir(parents=True, exist_ok=True)   # Create the weights directory if it does not already exist
        self.model_path = self.weights_dir / f"{model_name}.onnx"  # Create the complete path to the ONNX model
        self._ensure_model()
        
        #  Create ONNX Runtime Session on CPU
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 2  # Set the number of threads for independent operations
        opts.intra_op_num_threads = 2   # Set the number of threads used inside individual operations
        self.session = ort.InferenceSession(str(self.model_path), sess_options=opts, providers=["CPUExecutionProvider"])  # Load the ONNX emotion recognition model
        self.input_name = self.session.get_inputs()[0].name   # Get the input name expected by the ONNX model
        
        # Image normalization constants (ImageNet standard) # ImageNet normalization mean values
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 3, 1, 1)  # Used to normalize RGB image channels
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1) # ImageNet normalization standard deviation values

    def _ensure_model(self):  # Check whether the HSEmotion model exists
        # Also check user home cache from hsemotion-onnx
        user_home_cache = Path.home() / ".hsemotion" / f"{self.model_name}.onnx"  # Check the user's HSEmotion cache directory
        if user_home_cache.exists() and user_home_cache.stat().st_size > 1000000:  # Check whether a valid cached model exists
            if not self.model_path.exists():     # If the project model does not exist,# copy the cached model into the project weights folder
                import shutil  # Import shutil for copying files
                shutil.copy2(str(user_home_cache), str(self.model_path))
            return

        if not self.model_path.exists() or self.model_path.stat().st_size < 1000000:  # Download the model if: # 1. It does not exist, OR  # 2. The file size is less than 1 MB
            print(f"[EmotionRecognizer] Downloading HSEmotion model to {self.model_path}...")   # Display a message showing where the model will be downloaded
            urllib.request.urlretrieve(HSEMOTION_MODEL_URL, str(self.model_path))   # Download the ONNX model from the specified URL

    def preprocess_crop(self, img_bgr: np.ndarray, target_size: int = 224) -> np.ndarray:  # Preprocess a face image before sending it to the AI model
        """Preprocesses BGR image crop into normalized PyTorch/ONNX tensor format (1, 3, H, W)."""
        if img_bgr is None or img_bgr.size == 0:  # Check whether the image is missing or empty
            return np.zeros((1, 3, target_size, target_size), dtype=np.float32)  # Return an empty tensor with the expected shape

        if img_bgr.shape[0] != target_size or img_bgr.shape[1] != target_size:  # Check whether the image is already the required size
            img_bgr = cv2.resize(img_bgr, (target_size, target_size), interpolation=cv2.INTER_LINEAR)  # Resize the face image to 224 × 224

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)  # Convert OpenCV's BGR image format to RGB
        tensor = img_rgb.astype(np.float32) / 255.0  # (H, W, 3) # Convert pixel values from 0–255 to 0–1
        tensor = np.transpose(tensor, (2, 0, 1))      # (3, H, W) # Change image shape:
        tensor = np.expand_dims(tensor, axis=0)       # (1, 3, H, W)  # Add batch dimension
        tensor = (tensor - self.mean) / self.std  # Apply ImageNet normalization # Normalized = (pixel - mean) / standard deviation
        return tensor.astype(np.float32)   # Return the processed image tensor

    @staticmethod  # Static method for converting model logits into probabilities
    def _softmax(x: np.ndarray) -> np.ndarray:
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / np.sum(e_x, axis=-1, keepdims=True)

    def _map_8class_to_7class(self, probs8: np.ndarray) -> dict[str, float]:  # Convert the model's 8 emotion classes # into the application's standard 7 emotion classes
        """
        Maps AffectNet 8 classes:
        [0: Anger, 1: Contempt, 2: Disgust, 3: Fear, 4: Happiness, 5: Neutral, 6: Sadness, 7: Surprise]
        to standard 7 target emotions:
        {"angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"}.
        """
        anger = float(probs8[0])  # Get the probability for Anger
        contempt = float(probs8[1]) # Get the probability for Contempt
        disgust = float(probs8[2])
        fear = float(probs8[3])
        happy = float(probs8[4])
        neutral = float(probs8[5])
        sad = float(probs8[6])
        surprise = float(probs8[7])

        # Merge contempt with disgust (standard in 7-class FER literature)
        combined_disgust = disgust + contempt

        mapped = {    # Create the final seven-class emotion dictionary
            "angry": anger,
            "disgust": combined_disgust,
            "fear": fear,
            "happy": happy,
            "neutral": neutral,
            "sad": sad,
            "surprise": surprise,
        }

        # Normalize so sum equals 1.0
        total = sum(mapped.values()) or 1.0   # Calculate the total probability
        return {k: float(v / total) for k, v in mapped.items()} # Normalize the probabilities so that # their total is equal to 1.0
        # Predict emotion for a single face image
    def predict_crop(self, face_crop_bgr: np.ndarray) -> tuple[str, float, dict[str, float]]:
        """
        Runs inference on a single aligned face crop.
        Returns: (dominant_emotion, confidence, probability_dict)
        """
        tensor = self.preprocess_crop(face_crop_bgr, target_size=224)  # Preprocess the face image
        logits = self.session.run(None, {self.input_name: tensor})[0][0]   # Run the ONNX model # The output contains raw prediction values (logits)
        probs8 = self._softmax(logits) # Convert raw logits into probabilities
        prob_dict = self._map_8class_to_7class(probs8)   # Convert eight model classes into seven application classes

        dominant_emo = max(prob_dict, key=prob_dict.get)   # Find the emotion with the highest probability
        confidence = float(prob_dict[dominant_emo]) # Get the probability of the dominant emotion
        return dominant_emo, confidence, prob_dict # Return:# dominant emotion,# confidence,# all emotion probabilities
   # Predict emotions for multiple face images at once
    def predict_batch(self, face_crops_bgr: list[np.ndarray]) -> list[tuple[str, float, dict[str, float]]]:
        """
        Runs batch inference across multiple face crops simultaneously.
        """
        if not face_crops_bgr:   # If there are no face crops,# return an empty result
            return []

        tensors = [self.preprocess_crop(crop, target_size=224) for crop in face_crops_bgr]   # Preprocess every face crop
        batch_tensor = np.concatenate(tensors, axis=0) # Combine all individual tensors into one batch # at the same time

        batch_logits = self.session.run(None, {self.input_name: batch_tensor})[0]  # Run emotion recognition on all faces
        batch_probs8 = self._softmax(batch_logits)

        results = []
        for i in range(len(face_crops_bgr)):
            prob_dict = self._map_8class_to_7class(batch_probs8[i])
            dominant_emo = max(prob_dict, key=prob_dict.get)
            confidence = float(prob_dict[dominant_emo])
            results.append((dominant_emo, confidence, prob_dict))

        return results
