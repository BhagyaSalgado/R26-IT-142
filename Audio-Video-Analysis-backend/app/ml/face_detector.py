"""
Face detection and alignment module using OpenCV YuNet (cv2.FaceDetectorYN).
Extracts bounding boxes, detection confidence, 5-point facial landmarks,
sharpness / motion-blur scores, and performs canonical affine landmark alignment.
"""

import os
from pathlib import Path
import urllib.request
import cv2 # Import OpenCV for face detection, image processing,# resizing, color conversion, and affine transformation
import numpy as np

# Standard reference points for 224x224 canonical facial alignment (5 landmarks: RE, LE, Nose, RM, LM)
CANONICAL_5_LANDMARKS_224 = np.array([  # Define five standard facial landmark positions
    [70.0, 78.0],    # Right eye
    [154.0, 78.0],   # Left eye
    [112.0, 118.0],  # Nose tip   # These points are used to align faces into a common orientation.
    [76.0, 160.0],   # Right mouth corner
    [148.0, 160.0],  # Left mouth corner
], dtype=np.float32)
  # URL of the pre-trained OpenCV YuNet face detection model
YUNET_MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
DEFAULT_WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"   # Define the default directory where the YuNet model  will be stored

# Create a class responsible for face detection # and face alignment
class FaceDetector:
    def __init__(self, score_threshold: float = 0.50, nms_threshold: float = 0.30, weights_dir: Path | None = None): # Optional directory for storing the YuNet model.
        self.score_threshold = score_threshold   # Store the minimum face detection confidence
        self.nms_threshold = nms_threshold # Store the NMS threshold
        self.weights_dir = weights_dir or DEFAULT_WEIGHTS_DIR # Use the provided weights directory or use the default weights directory
        self.weights_dir.mkdir(parents=True, exist_ok=True)  # Create the weights directory if it does not exist
        self.model_path = self.weights_dir / "face_detection_yunet_2023mar.onnx"  # Define the complete path of the YuNet model
        self._ensure_model() # Check whether the model exists.If it does not exist, download it.
        
        # Initialize detector with default size; updated dynamically per frame
        self.detector = cv2.FaceDetectorYN.create(
            str(self.model_path),
            "",
            (320, 320), # Initial input image size
            score_threshold=self.score_threshold,  # Minimum detection confidence
            nms_threshold=self.nms_threshold, # Non-Maximum Suppression threshold
            top_k=5000, # Maximum number of detections to keep
        )
 # ENSURE YUNET MODEL EXISTS
    def _ensure_model(self): # Check whether the YuNet model exists # and download it if necessary
        if not self.model_path.exists() or self.model_path.stat().st_size < 10000:  # Check whether the model file does not exist # or is suspiciously small
            print(f"[FaceDetector] Downloading YuNet model to {self.model_path}...")  # Display a message showing the download location
            urllib.request.urlretrieve(YUNET_MODEL_URL, str(self.model_path))
 # CALCULATE FACE SHARPNESS
    @staticmethod
    def calculate_sharpness(img_bgr: np.ndarray) -> float:
        """Computes variance of the Laplacian as a measure of focus/motion blur."""
        if img_bgr is None or img_bgr.size == 0:  # Check whether the image is missing or empty
            return 0.0
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if len(img_bgr.shape) == 3 else img_bgr # Convert a color image from BGR to grayscale. # If the image is already grayscale, use it directly.
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    @staticmethod
    def calculate_frame_difference(prev_frame_gray: np.ndarray, curr_frame_gray: np.ndarray) -> float: # Calculate the difference between two consecutive frames
        """Computes mean absolute pixel difference between consecutive grayscale frames for de-duplication."""
        if prev_frame_gray is None or curr_frame_gray is None:
            return 255.0 # If either frame is missing, return a high difference value
        if prev_frame_gray.shape != curr_frame_gray.shape:  # If the two frames have different dimensions,they cannot be compared directly
            return 255.0
        return float(cv2.absdiff(prev_frame_gray, curr_frame_gray).mean())
 # ALIGN AND CROP FACE
    def align_crop_face(self, frame: np.ndarray, bbox: list | np.ndarray, landmarks: np.ndarray | None, target_size: int = 224) -> np.ndarray:
        """
        Aligns and crops a face image using 5-point similarity transformation if landmarks are available,
        or margin-expanded bounding-box crop with fallback.
        """
        h, w = frame.shape[:2]
        bx, by, bw, bh = [int(v) for v in bbox[:4]]
# LANDMARK-BASED FACE ALIGNMENT
        if landmarks is not None and len(landmarks) == 5:  # Check whether five facial landmarks are available
            try:
                src_pts = landmarks.astype(np.float32) # Convert detected landmarks to float32
                dst_pts = (CANONICAL_5_LANDMARKS_224 * (target_size / 224.0)).astype(np.float32)
                M, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts)
                if M is not None:
                    aligned = cv2.warpAffine(frame, M, (target_size, target_size), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                    return aligned
            except Exception:
                pass
# FALLBACK FACE CROP
        # Fallback: Margin-expanded bounding box crop (15% contextual margin)
        margin_x = int(bw * 0.15)   # Add a 15% horizontal margin around the face
        margin_y = int(bh * 0.15)   # Add a 15% vertical margin around the face
        x1 = max(0, bx - margin_x)  # Calculate the top-left crop coordinates # max() prevents coordinates from going below zero
        y1 = max(0, by - margin_y)
        x2 = min(w, bx + bw + margin_x) # Calculate the bottom-right crop coordinates # min() prevents coordinates from going
        y2 = min(h, by + bh + margin_y)

        crop = frame[y1:y2, x1:x2] # Crop the face from the original frame
        if crop.size == 0:
            crop = frame[max(0, by):min(h, by + bh), max(0, bx):min(w, bx + bw)]
        if crop.size == 0: # If the crop is still empty,# return a black 224x224 image
            return np.zeros((target_size, target_size, 3), dtype=np.uint8)
     # Resize the cropped face to 224x224
        return cv2.resize(crop, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
# DETECT FACES
    def detect_faces(self, frame: np.ndarray, min_conf: float = 0.50, min_rel_area: float = 0.001) -> list[dict]:
        """
        Detects all valid faces in a single frame using YuNet.
        Returns a list of dicts:
        [{
            'bbox': [x, y, w, h],
            'confidence': float,
            'landmarks': np.ndarray (5x2),
            'area_ratio': float,
            'sharpness': float,
            'aligned_crop': np.ndarray (224x224 BGR)
        }]
        """
        if frame is None or frame.size == 0:   # Check whether the frame is missing or empty  
            return []

        frame_h, frame_w = frame.shape[:2]  # Get frame height and width
        frame_area = max(1.0, float(frame_h * frame_w)) # Calculate the total frame area

        # Dynamically set input size
        self.detector.setInputSize((frame_w, frame_h))   # Tell YuNet the actual size of the current frame
        _, detections = self.detector.detect(frame)  # Run face detection

        if detections is None or len(detections) == 0: # If no faces were detected, # return an empty list
            return []

        valid_faces = []  # Create a list for valid detected faces
        for det in detections:
            # YuNet output format: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score]
            bx, by, bw, bh = float(det[0]), float(det[1]), float(det[2]), float(det[3])
            score = float(det[14])
 # CONFIDENCE FILTER
            if score < min_conf:  # Ignore faces with confidence below the minimum required confidence
                continue

            area_ratio = (bw * bh) / frame_area # Calculate how much of the frame is occupied by the detected face
            if area_ratio < min_rel_area:
                continue
# EXTRACT FIVE FACIAL LANDMARKS
            # Extract 5 landmarks: right eye, left eye, nose, right mouth, left mouth
            landmarks = np.array([
                [det[4], det[5]],   # RE
                [det[6], det[7]],   # LE
                [det[8], det[9]],   # Nose
                [det[10], det[11]], # R-mouth
                [det[12], det[13]]  # L-mouth
            ], dtype=np.float32)
# Align and crop the detected face into a standard 224x224 image
            aligned_crop = self.align_crop_face(frame, [bx, by, bw, bh], landmarks, target_size=224)
            sharpness = self.calculate_sharpness(aligned_crop) # Calculate the sharpness of the aligned face
# Store all information about this face
            valid_faces.append({ # Store all information about this face
                "bbox": [bx, by, bw, bh],
                "confidence": score,
                "landmarks": landmarks,
                "area_ratio": area_ratio,
                "sharpness": sharpness,
                "aligned_crop": aligned_crop,
            })
# SORT DETECTED FACES
        # Sort faces by area descending (largest face first)
        valid_faces.sort(key=lambda x: x["area_ratio"], reverse=True)
        return valid_faces
