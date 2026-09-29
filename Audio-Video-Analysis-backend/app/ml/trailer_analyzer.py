import json
import re
import uuid
import os
import threading
from pathlib import Path
from collections import Counter
# OPENCV CONFIGURATION
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp' # Configure OpenCV FFmpeg to use TCP transport # This can help with reliable video stream handling
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR' # Reduce unnecessary OpenCV log messages
import cv2
import numpy as np
import pandas as pd
import librosa
import soundfile as sf
from moviepy.editor import VideoFileClip
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from app.core.config import settings
from app.ml.face_tracker import ShotFaceTracker
# AUDIO CONFIGURATION
TARGET_AUDIO_SR = 22050  # Standard sampling rate used for audio processing
MOTION_REFERENCE_MAX = 10.0  # Optical flow velocity reference at 480px width

# Object detection rules with lower thresholds for deeper capture
DEFAULT_FALLBACK_RULES = {
    'person': {'min_conf': 0.30, 'min_area_ratio': 0.001, 'weight': 0.35},
    'knife': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.85},
    'scissors': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.80},
    'baseball bat': {'min_conf': 0.35, 'min_area_ratio': 0.002, 'weight': 0.80},
    'tie': {'min_conf': 0.40, 'min_area_ratio': 0.001, 'weight': 0.15},
    'handbag': {'min_conf': 0.35, 'min_area_ratio': 0.002, 'weight': 0.25},
    'backpack': {'min_conf': 0.35, 'min_area_ratio': 0.003, 'weight': 0.25},
    'umbrella': {'min_conf': 0.35, 'min_area_ratio': 0.002, 'weight': 0.20},
    'suitcase': {'min_conf': 0.35, 'min_area_ratio': 0.003, 'weight': 0.35},
    'bottle': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.20},
    'wine glass': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.25},
    'cup': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.15},
    'fork': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.15},
    'chair': {'min_conf': 0.35, 'min_area_ratio': 0.003, 'weight': 0.10},
    'couch': {'min_conf': 0.35, 'min_area_ratio': 0.005, 'weight': 0.15},
    'bed': {'min_conf': 0.40, 'min_area_ratio': 0.010, 'weight': 0.20},
    'dining table': {'min_conf': 0.35, 'min_area_ratio': 0.005, 'weight': 0.15},
    'laptop': {'min_conf': 0.35, 'min_area_ratio': 0.003, 'weight': 0.20},
    'tv': {'min_conf': 0.35, 'min_area_ratio': 0.005, 'weight': 0.15},
    'cell phone': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.20},
    'book': {'min_conf': 0.35, 'min_area_ratio': 0.002, 'weight': 0.15},
    'clock': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.10},
    'bench': {'min_conf': 0.35, 'min_area_ratio': 0.003, 'weight': 0.15},
    'car': {'min_conf': 0.40, 'min_area_ratio': 0.005, 'weight': 0.60},
    'motorcycle': {'min_conf': 0.40, 'min_area_ratio': 0.005, 'weight': 0.60},
    'bicycle': {'min_conf': 0.40, 'min_area_ratio': 0.005, 'weight': 0.45},
    'bus': {'min_conf': 0.45, 'min_area_ratio': 0.010, 'weight': 0.65},
    'truck': {'min_conf': 0.45, 'min_area_ratio': 0.010, 'weight': 0.65},
    'boat': {'min_conf': 0.45, 'min_area_ratio': 0.010, 'weight': 0.70},
    'airplane': {'min_conf': 0.45, 'min_area_ratio': 0.010, 'weight': 0.75},
    'train': {'min_conf': 0.45, 'min_area_ratio': 0.010, 'weight': 0.70},
    'horse': {'min_conf': 0.40, 'min_area_ratio': 0.005, 'weight': 0.60},
    'elephant': {'min_conf': 0.45, 'min_area_ratio': 0.010, 'weight': 0.65},
    'bear': {'min_conf': 0.45, 'min_area_ratio': 0.010, 'weight': 0.70},
    'dog': {'min_conf': 0.35, 'min_area_ratio': 0.003, 'weight': 0.30},
    'cat': {'min_conf': 0.35, 'min_area_ratio': 0.003, 'weight': 0.25},
    'sports ball': {'min_conf': 0.35, 'min_area_ratio': 0.001, 'weight': 0.30},
    'skateboard': {'min_conf': 0.35, 'min_area_ratio': 0.002, 'weight': 0.35},
    'surfboard': {'min_conf': 0.40, 'min_area_ratio': 0.005, 'weight': 0.45},
    'skis': {'min_conf': 0.40, 'min_area_ratio': 0.005, 'weight': 0.45},
    'snowboard': {'min_conf': 0.40, 'min_area_ratio': 0.005, 'weight': 0.45},
    'fire hydrant': {'min_conf': 0.40, 'min_area_ratio': 0.002, 'weight': 0.20},
}
# Default rule used when an object is detected but does not have a specific rule above
DEFAULT_OBJECT_FALLBACK = {'min_conf': 0.40, 'min_area_ratio': 0.003, 'weight': 0.20}

# CLIP zero-shot scene classification — one-to-one label ↔ prompt mapping
CLIP_SCENE_CATEGORIES = [  # List of scene categories that CLIP can classify
    "Action", "Horror", "Comedy", "Romance",
    "Thriller", "Drama", "Adventure", "Emotional",
]
CLIP_SCENE_TEXT_PROMPTS = [  # Text descriptions used as prompts for CLIP.
    "an action fight scene with combat, explosions or car chases",
    "a terrifying horror scene with darkness, monsters or jump scares",
    "a funny comedic scene with humor and laughter",
    "a romantic love scene between two people",
    "a tense suspenseful thriller scene with psychological tension",
    "a dramatic dialogue scene with serious emotional conversation",
    "an outdoor adventure scene with epic landscapes or exploration",
    "a deeply emotional or tearful scene with sadness or grief",
]

# Arousal score by facial emotion class
EMOTION_AROUSAL = {
    'surprise': 0.88,
    'angry': 0.85,
    'fear': 0.82,
    'happy': 0.75,
    'sad': 0.68,
    'disgust': 0.65,
    'neutral': 0.35,
    'unknown': 0.35,
}
# LOAD OBJECT DETECTION RULES
def load_object_rules():
    config_path = settings.MODEL_DIR / "object_weights.json"
    if config_path.exists(): # Check whether the configuration file exists
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))  # Read and convert the JSON configuration into a Python dictionary
            rules = data.get("rules", DEFAULT_FALLBACK_RULES) # Get custom object rules from the configuration.# If not available, use the default rules.
            default_rule = data.get("default_rule", DEFAULT_OBJECT_FALLBACK)
            return rules, default_rule
        except Exception:
            pass
    return DEFAULT_FALLBACK_RULES, DEFAULT_OBJECT_FALLBACK

# TIME CONVERSION FUNCTION
def seconds_to_mmss(sec: float) -> str:
    sec = float(sec) # Convert the input value to a floating-point number
    m = int(sec // 60)
    s = sec % 60 # Calculate the remaining seconds
    return f"{m:02d}:{s:05.2f}"
# TRAILER ANALYZER CLASS
class TrailerAnalyzer:
    def __init__(self, model_manager):  # Constructor for the TrailerAnalyzer class
        self.mm = model_manager.load_models()
        self.object_rules, self.default_object_rule = load_object_rules()
        # Lock for YuNet FaceDetector (setInputSize is not thread-safe)
        self._face_det_lock = threading.Lock()

 # MAIN TRAILER ANALYSIS FUNCTION
    def analyze(self, video_path: str, movie_name: str | None = None) -> dict:
        video_path = Path(video_path)  # Convert the video path into a Path object
        safe_name = re.sub(r'[^a-zA-Z0-9_]+', '_', movie_name or video_path.stem)
        run_id = f"{safe_name}_{uuid.uuid4().hex[:8]}" # Generate a unique ID for this analysis run
        run_dir = settings.OUTPUT_DIR / run_id
        frames_dir = run_dir / "frames"
        run_dir.mkdir(parents=True, exist_ok=True)
        frames_dir.mkdir(parents=True, exist_ok=True)

        scenes = self.create_scene_segments(video_path)
        audio_path = run_dir / f"{safe_name}_audio.wav"
        self.extract_audio_from_video(video_path, audio_path)

 # AUDIO ANALYSIS
        audio_df = self.extract_audio_scene_features(str(audio_path), scenes, run_dir)
        visual_df = self.extract_visual_features(str(video_path), scenes, frames_dir)

        # MULTIMODAL FUSION
        canonical_records, final_df, visual_clean_df = self.calculate_canonical_fusion(audio_df, visual_df)
        # TRAILER GENRE CLASSIFICATION
        # Whole-Trailer Statistical Multimodal Genre Classifier
        genre_report = self.classify_trailer_genre(final_df)
        insights = self.generate_insights(final_df, genre_report)
        insights["source_filename"] = video_path.name

# DEFINE OUTPUT FILES
        audio_csv = run_dir / "audio_feature_output.csv"  # CSV containing extracted audio features
        visual_csv = run_dir / "visual_feature_output.csv" # CSV containing extracted visual features
        final_csv = run_dir / "final_system_output.csv" # CSV containing the final multimodal output
        insights_json = run_dir / "insights.json"
# SAVE ANALYSIS RESULTS
        audio_df.to_csv(audio_csv, index=False)  # Save audio features as CSV
        visual_clean_df.to_csv(visual_csv, index=False)  # Save cleaned visual features as CSV
        final_df.to_csv(final_csv, index=False) # Save final multimodal results as CSV
        insights_json.write_text(json.dumps(insights, indent=2), encoding="utf-8")
# RETURN FINAL ANALYSIS RESULT # Return all important results to the application
        return {
            "filename": video_path.name,
            "run_id": run_id,
            "total_scenes": int(len(final_df)), # Total number of analyzed scenes
            "dominant_genre": genre_report.get("dominant_genre", "Action"),
            "secondary_genre": genre_report.get("secondary_genre"),
            "genre_mixture": genre_report.get("genre_mixture", {}),
            "insights": insights,
            "final_system_output": self.clean_records(final_df),
            "audio_feature_output": self.clean_records(audio_df),
            "visual_feature_output": self.clean_records(visual_clean_df),
            "saved_files": {
                "audio_csv": str(audio_csv),
                "visual_csv": str(visual_csv),
                "final_csv": str(final_csv),
                "insights_json": str(insights_json),
            },
        }
 # CREATE SCENE SEGMENTS
    def create_scene_segments(self, video_path: Path):
        if settings.USE_SHOT_BOUNDARY_DETECTION:
            try:
                from scenedetect import open_video, SceneManager, AdaptiveDetector, ContentDetector
                video = open_video(str(video_path))
                scene_manager = SceneManager() # Create a scene manager to manage detected scenes
                scene_manager.add_detector(AdaptiveDetector())
                try:
                    scene_manager.detect_scenes(video=video) 
                    scene_list = scene_manager.get_scene_list()
                except Exception as e:
                    print(f"[ShotDetection] AdaptiveDetector failed ({e}), falling back to ContentDetector")
                    video.seek(0)
                    scene_manager = SceneManager()
                    scene_manager.add_detector(ContentDetector())
                    scene_manager.detect_scenes(video=video)
                    scene_list = scene_manager.get_scene_list()

                raw_cuts = [(s[0].get_seconds(), s[1].get_seconds()) for s in scene_list if s[1].get_seconds() > s[0].get_seconds()]
                
                # Apply duration filtering rules
                processed_cuts = []  # List used to store the processed scene segments
                for st, et in raw_cuts: # Process every detected scene
                    dur = et - st  # Calculate the duration of the detected scene
                    if dur < settings.MIN_SHOT_DURATION_SEC: # If the scene is shorter than the minimum allowed shot duration
                        if processed_cuts:
                            prev_st, prev_et = processed_cuts.pop() # Remove the previous scene
                            processed_cuts.append((prev_st, et)) # Extend the previous scene to the end of the current short scene
                        else:
                            processed_cuts.append((st, et)) # If there is no previous scene,# keep the short scene
                    elif dur > settings.MAX_SHOT_DURATION_SEC:  # If the detected scene is longer than the maximum allowed shot duration
                        curr = st
                        while curr < et:
                            next_end = min(curr + settings.MAX_SHOT_DURATION_SEC, et)
                            if (et - next_end) < settings.MIN_SHOT_DURATION_SEC and next_end < et:
                                next_end = et
                            processed_cuts.append((curr, next_end))
                            curr = next_end
                    else:
                        processed_cuts.append((st, et))
# CREATE FINAL SCENE RECORDS
                if processed_cuts:  # Continue only if valid processed scenes exist
                    scenes = []
                    for idx, (st, et) in enumerate(processed_cuts, start=1):
                        dur = round(et - st, 2) # Calculate and round scene duration
                        scenes.append({ # Store scene information as a dictionary
                            "scene": idx,  # Scene number
                            "start_time": float(st), # Scene starting time in seconds
                            "end_time": float(et),  # Scene ending time in seconds
                            "duration": dur,  # Scene duration in seconds
                            "time": f"{seconds_to_mmss(st)}-{seconds_to_mmss(et)}",
                        })
                    print(f"[ShotDetection] PySceneDetect extracted {len(scenes)} smart shot segments")
                    return scenes

            except Exception as e:
                print(f"[ShotDetection] WARNING: PySceneDetect failed ({e}) - using fixed-duration fallback")
 # FIXED-DURATION FALLBACK
        # Fallback to fixed 8-second segmentation
        clip = VideoFileClip(str(video_path))
        total_duration = int(clip.duration or 0)  # Get the total video duration in seconds
        clip.close() # Close the video after getting its duration
        scenes = [] # Create an empty list for storing scenes
        scene_no = 1 # Start scene numbering from 1
        for start in range(0, total_duration, settings.SCENE_DURATION_SECONDS):
            end = min(start + settings.SCENE_DURATION_SECONDS, total_duration) # Calculate the end time of the current segment# without exceeding the total video duration
            if end <= start:
                continue
            scenes.append({  # Store the fixed-duration scene information
                "scene": scene_no, # Scene number
                "start_time": float(start), # Scene start time
                "end_time": float(end), # Scene end time
                "duration": float(end - start),  # Scene duration
                "time": f"{seconds_to_mmss(start)}-{seconds_to_mmss(end)}",
            })
            scene_no += 1
        return scenes
# EXTRACT AUDIO FROM VIDEO
    # Extract the audio track from the input movie trailer
    def extract_audio_from_video(self, video_path: Path, audio_path: Path):
        clip = VideoFileClip(str(video_path))   # Open the video using MoviePy
        if clip.audio is None:  # Check whether the video contains an audio track
            clip.close()
            raise ValueError("This video has no audio track.")
        clip.audio.write_audiofile(str(audio_path), fps=TARGET_AUDIO_SR, verbose=False, logger=None) # Extract the audio and save it as a WAV file.# fps=TARGET_AUDIO_SR sets the audio sampling rate
        clip.close()

# EXTRACT AUDIO FEATURES FOR EACH SCENE
    def extract_audio_scene_features(self, audio_path: str, scenes: list, run_dir: Path) -> pd.DataFrame: # Extract audio features separately for every detected scene
        y, sr = librosa.load(audio_path, sr=TARGET_AUDIO_SR)  # Load the complete audio file using Librosa  # sr=TARGET_AUDIO_SR ensures the audio is loaded
        rows = []  # Create an empty list to store the feature information of each scene
# CALCULATE GLOBAL TEMPO
        try:
            global_tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)  # Calculate the overall tempo of the complete trailer
            global_tempo = float(np.asarray(global_tempo_arr).reshape(-1)[0]) if np.size(global_tempo_arr) > 0 else 120.0 
        except Exception:     # If global tempo detection fails,use 120 BPM as the fallback
            global_tempo = 120.0
# PROCESS EACH SCENE
        for scene in scenes:  # Analyze each scene independently
            start_sample = int(scene["start_time"] * sr) # Convert scene start time from seconds into an audio sample index
            end_sample = int(scene["end_time"] * sr) # Convert scene end time from seconds into an audio sample index
            if len(segment) == 0:  # If the audio segment is empty,skip this scene
                continue
# CALCULATE SCENE TEMPO
            if len(segment) >= int(3.0 * sr): # If the scene has at least 3 seconds of audio,calculate its own tempo
                try:
                    tempo, _ = librosa.beat.beat_track(y=segment, sr=sr)   # Detect tempo for this individual scene
                    tempo_val = float(np.asarray(tempo).reshape(-1)[0]) if np.size(tempo) > 0 else global_tempo  # Convert the tempo to a single numerical value If detection fails to produce a value,use the global trailer tempo.
                except Exception:
                    tempo_val = global_tempo # If scene-level tempo calculation fails,use the global trailer tempo
            else:
                tempo_val = global_tempo  # For scenes shorter than 3 seconds,use the global trailer tempo
# AUDIO FEATURE EXTRACTION
            rms = librosa.feature.rms(y=segment)  # Calculate RMS (Root Mean Square) energy.RMS represents the strength/energy level of the audio.
            audio_energy_raw = float(np.mean(rms))  # Calculate the raw average audio energy
            mfcc = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=13)
            spectral_centroid = librosa.feature.spectral_centroid(y=segment, sr=sr)  # Calculate spectral centroid. It represents the approximate "brightness"or center of mass of the audio spectrum.
            zcr = librosa.feature.zero_crossing_rate(segment) # Calculate Zero Crossing Rate (ZCR).

            mfcc_mean_val = float(np.mean(mfcc)) # Calculate the mean MFCC value
            centroid_val = float(np.mean(spectral_centroid)) # Calculate the average spectral centroid
            zcr_val = float(np.mean(zcr))

            # Calibrate energy: [0.0, 0.15] mapped to [0.0, 1.0]
            calibrated_a = float(np.clip(audio_energy_raw / 0.15, 0.0, 1.0))

            # Fast in-memory ML audio emotion classification (137 features)
            audio_emotion = "neutral"
            audio_confidence = 0.50
            if getattr(self.mm, 'audio_emotion_model', None) is not None and getattr(self.mm, 'audio_scaler', None) is not None and getattr(self.mm, 'audio_label_encoder', None) is not None and len(segment) >= int(0.3 * sr):
                try:
                    mfcc_full = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=40)
                    chroma = librosa.feature.chroma_stft(y=segment, sr=sr)
                    mel = librosa.feature.melspectrogram(y=segment, sr=sr)
                    rolloff = librosa.feature.spectral_rolloff(y=segment, sr=sr)
                    
                    feats_137 = []
                    feats_137.extend(np.mean(mfcc_full, axis=1))
                    feats_137.extend(np.std(mfcc_full, axis=1))
                    feats_137.extend(np.mean(chroma, axis=1))
                    feats_137.extend(np.mean(mel, axis=1)[:40])
                    feats_137.append(float(centroid_val))
                    feats_137.append(float(np.mean(rolloff)))
                    feats_137.append(float(zcr_val))
                    feats_137.append(float(audio_energy_raw))
                    feats_137.append(float(tempo_val))
                    
                    feat_vec = np.array(feats_137, dtype=np.float32).reshape(1, -1)
                    feat_scaled = self.mm.audio_scaler.transform(feat_vec)
                    pred_cls = self.mm.audio_emotion_model.predict(feat_scaled)[0]
                    probs = self.mm.audio_emotion_model.predict_proba(feat_scaled)[0]
                    audio_emotion = self.mm.audio_label_encoder.inverse_transform([pred_cls])[0]
                    audio_confidence = round(float(np.max(probs)), 4)
                except Exception:
                    audio_emotion = "neutral"
                    audio_confidence = 0.50


            rows.append({
                "scene": scene["scene"],
                "time": scene["time"],
                "tempo_bpm": round(tempo_val, 2),
                "audio_energy_raw": round(audio_energy_raw, 6),
                "A": round(calibrated_a, 4),
                "mfcc_mean": round(mfcc_mean_val, 4),
                "spectral_centroid": round(centroid_val, 2),
                "zcr": round(zcr_val, 6),
                "audio_emotion": audio_emotion,
                "audio_confidence": audio_confidence,
                "audio_emotion_raw_score": audio_confidence,
            })

        audio_df = pd.DataFrame(rows)
        if audio_df.empty:
            return audio_df
        audio_df["audio_mood"] = audio_df.apply(self.audio_mood, axis=1)
        return audio_df

    @staticmethod
    def audio_mood(row):
        """
        Acoustic characteristic descriptor derived purely from energy and tempo.
        """
        a = float(row.get("A", 0.0))
        tempo = float(row.get("tempo_bpm", 120.0))
        if a >= 0.65 and tempo >= 115:
            return "intense"
        if a >= 0.50:
            return "emotional"
        if a < 0.30 and tempo < 95:
            return "suspense"
        if a < 0.45:
            return "calm"
        return "calm"

    def extract_scene_frames(self, video_path: str, scene: dict, output_folder: Path):
        """Adaptively samples 6–12 frames per scene with duplicate-frame filtering.
        Saves the sharpest frame as the representative thumbnail for CLIP and display."""
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        st, et = scene["start_time"], scene["end_time"]
        dur = max(1.0, et - st)

        # Adaptive sampling: 6–12 frames depending on scene duration
        num_samples = max(6, min(12, int(dur * 2.5)))
        timepoints = [st + (i + 0.5) * (dur / num_samples) for i in range(num_samples)]

        frames: list = []
        sharpness_scores: list[float] = []
        prev_gray_small = None

        for t in timepoints:
            frame_no = int(t * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # Deduplication: discard near-identical frames (diff < 3.0 on 160×90 grayscale)
            small = cv2.resize(frame, (160, 90))
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            if prev_gray_small is not None:
                diff = float(cv2.absdiff(prev_gray_small, gray_small).mean())
                if diff < 3.0:
                    continue
            prev_gray_small = gray_small

            # Sharpness via Laplacian variance (higher = clearer frame)
            sharpness = float(cv2.Laplacian(gray_small, cv2.CV_64F).var())
            frames.append(frame)
            sharpness_scores.append(sharpness)

        cap.release()

        # Save the sharpest frame as the scene thumbnail
        middle_frame_path = None
        if frames:
            best_idx = int(np.argmax(sharpness_scores)) if sharpness_scores else 0
            frame_path = output_folder / f"scene_{scene['scene']}.jpg"
            cv2.imwrite(str(frame_path), frames[best_idx])
            middle_frame_path = str(frame_path)

        return middle_frame_path, frames

    def predict_camera_angle(self, frame_path: str):
        try:
            img = cv2.imread(frame_path)
            img = cv2.resize(img, (settings.VIDEO_IMG_SIZE, settings.VIDEO_IMG_SIZE))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            arr = preprocess_input(np.expand_dims(img.astype(np.float32), axis=0))
            probs = self.mm.video_model.predict(arr, verbose=0)[0]
            idx = int(np.argmax(probs))
            return self.mm.video_label_names.get(idx, str(idx)), float(np.max(probs))
        except Exception:
            return "unknown", 0.0

    def detect_objects_multi_frame(self, frames):
        if self.mm.yolo_model is None or not frames:
            return "", 0.0
            
        detected_counts = Counter()
        detected_max_conf = {}
        total_frames = len(frames)
        
        for frame in frames:
            try:
                frame_h, frame_w = frame.shape[:2]
                frame_area = max(1.0, float(frame_h * frame_w))
                results = self.mm.yolo_model(frame, verbose=False)
                
                frame_seen_classes = set()
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        label = self.mm.yolo_model.names[cls_id].lower().strip()
                        
                        xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy[0], 'tolist') else list(box.xyxy[0])
                        box_w = max(0.0, xyxy[2] - xyxy[0])
                        box_h = max(0.0, xyxy[3] - xyxy[1])
                        box_area_ratio = (box_w * box_h) / frame_area
                        
                        rule = self.object_rules.get(label, self.default_object_rule)
                        if conf >= rule['min_conf'] and box_area_ratio >= rule['min_area_ratio']:
                            if label not in frame_seen_classes:
                                detected_counts[label] += 1
                                frame_seen_classes.add(label)
                            detected_max_conf[label] = max(detected_max_conf.get(label, 0.0), conf)
            except Exception:
                continue
                
        confirmed_objects = []
        semantic_score = 0.0
        
        for label, count in detected_counts.items():
            max_c = detected_max_conf.get(label, 0.0)
            # Accept object if: high confidence, or seen in multiple frames, or few frames available
            if max_c >= 0.55 or count >= 2 or total_frames <= 2:
                confirmed_objects.append(label)
                weight = self.object_rules.get(label, self.default_object_rule)['weight']
                semantic_score += weight * max_c
                
        confirmed_objects = sorted(set(confirmed_objects))
        return ", ".join(confirmed_objects), float(min(1.0, semantic_score))

    def detect_deepface_emotion(self, frames):
        if self.mm.deepface is None or not frames:
            return "unknown", 0.0, False, 0.0
            
        valid_predictions = []
        max_reliability = 0.0
        face_found_any = False
        
        for frame in frames:
            try:
                frame_h, frame_w = frame.shape[:2]
                frame_area = max(1.0, float(frame_h * frame_w))

                if max(frame_h, frame_w) > 480:
                    scale = 480.0 / max(frame_h, frame_w)
                    df_frame = cv2.resize(frame, (int(frame_w * scale), int(frame_h * scale)))
                else:
                    df_frame = frame
                
                result = self.mm.deepface.analyze(img_path=df_frame, actions=["emotion"], enforce_detection=False)
                if isinstance(result, list):
                    result = result[0]
                    
                region = result.get("region", {})
                box_w = region.get("w", 0)
                box_h = region.get("h", 0)
                
                df_h, df_w = df_frame.shape[:2]
                if box_w > df_w * 0.75 and box_h > df_h * 0.75:
                    continue
                if box_w < 10 or box_h < 10:
                    continue
                    
                face_found_any = True
                face_area_ratio = (box_w * box_h) / max(1.0, float(df_h * df_w))
                face_det_c = float(result.get("face_confidence", 0.90))
                
                scores = result.get("emotion", {})
                total_sum = sum(scores.values()) or 100.0
                norm_scores = {k.lower(): float(v) / total_sum for k, v in scores.items()}
                
                top_emo = max(norm_scores, key=norm_scores.get)
                top_emo_c = norm_scores[top_emo]
                
                # [FIX 1]: Adjusted penalty threshold for small faces. Faces in trailers are often small.
                # Lowered from 0.05 (5% of screen) to 0.01 (1% of screen).
                size_factor = min(1.0, face_area_ratio / 0.01)
                reliability = face_det_c * top_emo_c * size_factor
                
                if reliability > max_reliability:
                    max_reliability = reliability
                
                if reliability > 0.0:
                    valid_predictions.append((norm_scores, reliability, face_det_c, face_area_ratio))
            except Exception:
                continue
                
        # [FIX 2]: Lowered threshold from 0.08 to 0.02 to allow valid but smaller/weaker emotions to pass.
        if not face_found_any or not valid_predictions or max_reliability <= 0.02:
            return "unknown", 0.0, False, 0.0
            
        # [FIX 3]: Filter to only aggregate the most prominent faces (top 50% by area) across the sequence.
        # This prevents background characters or crowd noise from diluting the main character's emotion.
        valid_predictions.sort(key=lambda x: x[3], reverse=True)
        keep_count = max(1, len(valid_predictions) // 2)
        valid_predictions = valid_predictions[:keep_count]
            
        total_weight = sum(rel for _, rel, _, _ in valid_predictions)
        if total_weight <= 0:
            return "unknown", 0.0, False, 0.0

        all_emotions = set()
        for norm_scores, _, _, _ in valid_predictions:
            all_emotions.update(norm_scores.keys())

        averaged_scores = {}
        for emo in all_emotions:
            weighted_sum = sum(rel * norm_scores.get(emo, 0.0) for norm_scores, rel, _, _ in valid_predictions)
            averaged_scores[emo] = weighted_sum / total_weight

        best_emotion = max(averaged_scores, key=averaged_scores.get)
        best_emo_conf = averaged_scores[best_emotion]
        avg_det_conf = sum(rel * det_c for _, rel, det_c, _ in valid_predictions) / total_weight

        return best_emotion, float(best_emo_conf), True, float(avg_det_conf)

    def detect_face_emotion_real(self, frames: list) -> tuple:
        """Multi-frame face emotion detection using YuNet + HSEmotion EfficientNet-B0 ONNX.

        Pipeline:
          1. YuNet detects & aligns faces in every sampled frame (locked for thread-safety)
          2. ShotFaceTracker associates faces into persistent tracks across frames
          3. HSEmotion runs batch inference on all aligned face crops
          4. Results are aggregated via weighted voting:
             weight = track_length × area_ratio × detection_conf × sharpness_factor

        Falls back to DeepFace if the real pipeline hasn't loaded.
        """
        fd = getattr(self.mm, 'face_detector', None)
        er = getattr(self.mm, 'emotion_recognizer', None)

        if fd is None or er is None or not frames:
            return self.detect_deepface_emotion(frames)

        frame_detections: list = []

        # YuNet requires per-call setInputSize which is not thread-safe → lock
        with self._face_det_lock:
            for frame_idx, frame in enumerate(frames):
                try:
                    faces = fd.detect_faces(frame, min_conf=0.45, min_rel_area=0.0005)
                except Exception:
                    faces = []
                frame_detections.append((frame_idx, faces))

        face_found_any = any(len(f) > 0 for _, f in frame_detections)
        if not face_found_any:
            return "unknown", 0.0, False, 0.0

        # Associate faces into tracks across frames
        frame_shape = frames[0].shape[:2]
        tracker = ShotFaceTracker(iou_threshold=0.20, max_centroid_dist_norm=0.25)
        tracks = tracker.track_faces_in_shot(frame_detections, frame_shape)

        if not tracks:
            return "unknown", 0.0, False, 0.0

        # Collect aligned face crops from the top-3 most prominent tracks
        top_tracks = tracks[:3]
        all_crops: list = []
        crop_weights: list[float] = []

        for track in top_tracks:
            # Track importance combines persistence, size, and detection quality
            track_base_weight = track.track_length * track.avg_area_ratio * track.avg_confidence
            for det in track.detections:
                crop = det.get("aligned_crop")
                if crop is None or crop.size == 0:
                    continue
                # Boost weight for sharper (less motion-blurred) crops
                sharpness_norm = min(1.0, det.get("sharpness", 0.0) / 500.0)
                weight = track_base_weight * (0.5 + 0.5 * sharpness_norm)
                all_crops.append(crop)
                crop_weights.append(weight)

        if not all_crops:
            return "unknown", 0.0, False, 0.0

        # Batch emotion inference (EfficientNet-B0 ONNX via HSEmotion)
        batch_results = er.predict_batch(all_crops)

        # Weighted aggregation of per-class probability distributions
        total_weight = sum(crop_weights) or 1.0
        aggregated: dict = {}
        for (_, _, prob_dict), weight in zip(batch_results, crop_weights):
            for emotion, prob in prob_dict.items():
                aggregated[emotion] = aggregated.get(emotion, 0.0) + prob * weight / total_weight

        if not aggregated:
            return "unknown", 0.0, False, 0.0

        dominant = max(aggregated, key=aggregated.get)
        confidence = float(aggregated[dominant])
        avg_det_conf = float(np.mean([t.avg_confidence for t in top_tracks]))
        return dominant, round(confidence, 4), True, round(avg_det_conf, 4)

    def calculate_motion_intensity(self, video_path: str, scene: dict, frames: list | None = None):
        """
        Fast Farneback dense optical flow with camera motion compensation
        evaluated directly on sampled keyframe pairs.
        """
        if frames and len(frames) >= 2:
            prev = frames[0]
            curr = frames[len(frames) // 2]
        else:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            st, et = scene["start_time"], scene["end_time"]
            f1 = int((st + 0.25 * (et - st)) * fps)
            f2 = int((st + 0.75 * (et - st)) * fps)

            cap.set(cv2.CAP_PROP_POS_FRAMES, f1)
            ret1, prev = cap.read()
            cap.set(cv2.CAP_PROP_POS_FRAMES, f2)
            ret2, curr = cap.read()
            cap.release()

            if not ret1 or not ret2 or prev is None or curr is None:
                return 0.0

        try:
            target_width = 240
            h, w = prev.shape[:2]
            scale = target_width / max(1, w)
            target_height = int(h * scale)

            prev_gray = cv2.cvtColor(cv2.resize(prev, (target_width, target_height)), cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(cv2.resize(curr, (target_width, target_height)), cv2.COLOR_BGR2GRAY)

            flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            u_flow = flow[..., 0]
            v_flow = flow[..., 1]
            u_bg = float(np.median(u_flow))
            v_bg = float(np.median(v_flow))

            u_content = u_flow - u_bg
            v_content = v_flow - v_bg
            content_mag = np.sqrt(u_content**2 + v_content**2)
            return float(np.mean(content_mag))
        except Exception:
            return 0.0



    def process_single_scene_visual(self, video_path: str, scene: dict, frames_folder: Path):
        frame_path, frames = self.extract_scene_frames(video_path, scene, frames_folder)
        if frame_path is None or not frames:
            return None
        objects, object_score = self.detect_objects_multi_frame(frames)
        camera_angle, camera_conf = self.predict_camera_angle(frame_path)
        # Use real YuNet+HSEmotion pipeline; falls back to DeepFace if unavailable
        face_emotion, face_conf, face_found, face_det_conf = self.detect_face_emotion_real(frames)
        raw_motion = self.calculate_motion_intensity(video_path, scene, frames)
        return {
            "scene": scene["scene"],
            "time": scene["time"],
            "frame_path": frame_path,   # stored for CLIP scene classification
            "raw_motion": raw_motion,
            "O": object_score,
            "camera_angle": camera_angle,
            "camera_confidence": camera_conf,
            "face_emotion": face_emotion,
            "face_confidence": face_conf,
            "face_found": face_found,
            "face_det_confidence": face_det_conf,
            "F": face_conf if face_found else 0.0,
            "objects": objects,
        }

    def extract_visual_features(self, video_path: str, scenes: list, frames_folder: Path) -> pd.DataFrame:
        from concurrent.futures import ThreadPoolExecutor
        num_workers = min(4, max(1, os.cpu_count() or 2))
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(self.process_single_scene_visual, video_path, scene, frames_folder) for scene in scenes]
            rows = [f.result() for f in futures if f.result() is not None]

        rows = sorted(rows, key=lambda x: x["scene"])
        visual_df = pd.DataFrame(rows)
        if visual_df.empty:
            return visual_df
            
        # Calibrated global motion normalization: [0.0, MOTION_REFERENCE_MAX] mapped to [0.0, 1.0]
        visual_df["M"] = [float(np.clip(float(rm) / MOTION_REFERENCE_MAX, 0.0, 1.0)) for rm in visual_df["raw_motion"].values]
        return visual_df

    @staticmethod
    def get_intensity_level(ei):
        if ei >= 0.70:
            return "High"
        if ei >= 0.40:
            return "Medium"
        return "Low"

    def calculate_canonical_fusion(self, audio_df: pd.DataFrame, visual_df: pd.DataFrame):
        if audio_df.empty or visual_df.empty:
            return [], pd.DataFrame(), pd.DataFrame()
            
        merged = pd.merge(visual_df, audio_df, on=["scene", "time"], how="inner")
        canonical_records = []
        visual_clean_rows = []

        # Adaptive weight priors for EI fusion
        w_face_prior = 0.30
        w_audio_prior = 0.30
        w_motion_prior = 0.25
        w_object_prior = 0.15

        merged_df = merged
        ml_preds = self.classify_scene_type_multimodal(merged_df)

        for idx, row in merged_df.reset_index(drop=True).iterrows():
            pred_info = ml_preds[idx]
            scene_type = pred_info["scene_type"]
            scene_type_confidence = pred_info["confidence"]
            classification_reliable = pred_info["classification_reliable"]

            face_found = bool(row.get("face_found", False))
            raw_face_emo = str(row.get("face_emotion", "unknown")).lower()
            face_conf = float(row.get("face_confidence", 0.0))
            face_det_conf = float(row.get("face_det_confidence", 0.0))
            audio_mood = str(row.get("audio_mood", "calm")).lower()
            audio_emo = str(row.get("audio_emotion", "neutral")).lower()
            audio_conf = float(row.get("audio_confidence", 0.50))
            audio_energy = float(row.get("A", 0.50))
            tempo_bpm = float(row.get("tempo_bpm", 120.0))
            motion = float(row.get("M", 0.0))
            obj_score = float(row.get("O", 0.0))
            objects = str(row.get("objects", ""))

            # Compute adaptive reliability-weighted EI per scene
            if face_found and raw_face_emo != "unknown":
                r_face = face_conf * face_det_conf
            else:
                r_face = 0.0
            r_audio = audio_conf * float(np.clip(audio_energy, 0.20, 1.0))
            r_motion = float(np.clip(1.0 - abs(motion - 0.5) * 0.3, 0.40, 1.0))
            r_object = max(0.35, obj_score)

            weights_raw = {
                "face": w_face_prior * r_face,
                "audio": w_audio_prior * r_audio,
                "motion": w_motion_prior * r_motion,
                "object": w_object_prior * r_object,
            }
            w_sum = sum(weights_raw.values()) or 1.0
            w_norm = {k: v / w_sum for k, v in weights_raw.items()}

            ei = round(
                w_norm["motion"] * motion +
                w_norm["audio"] * audio_energy +
                w_norm["object"] * obj_score +
                w_norm["face"] * (face_conf if face_found else 0.0),
                2
            )
            level = self.get_intensity_level(ei)

            # Clean display emotion resolution
            display_face_emo = raw_face_emo if (face_found and raw_face_emo != "unknown") else "neutral"
            if face_found and raw_face_emo != "unknown":
                scene_emotion = raw_face_emo
            elif audio_emo in ["happy", "sad", "fear", "angry", "surprise", "disgust"]:
                scene_emotion = audio_emo
            elif audio_mood in ["suspense", "intense"]:
                scene_emotion = "fear" if audio_mood == "suspense" else "angry"
            elif audio_mood == "emotional":
                scene_emotion = "sad"
            else:
                scene_emotion = "neutral"

            camera_angle_str = str(row.get("camera_angle", "front"))
            if camera_angle_str.lower() in ["unknown", "none", ""]:
                camera_angle_str = "front"

            final_record = {
                "scene": int(row["scene"]),
                "time": str(row["time"]),
                "scene_type": scene_type,
                "scene_type_confidence": scene_type_confidence,
                "classification_reliable": classification_reliable,
                "M": round(motion, 4),
                "A": round(audio_energy, 4),
                "O": round(obj_score, 4),
                "F": round(face_conf if face_found else 0.0, 4),
                "EI": ei,
                "level": level,
                "audio_mood": audio_mood,
                "audio_emotion": audio_emo,
                "audio_confidence": round(audio_conf, 4),
                "audio_emotion_raw_score": round(audio_conf, 4),
                "camera_angle": camera_angle_str,
                "face_emotion": display_face_emo,
                "face_found": face_found,
                "objects": objects,
                "tempo_bpm": round(tempo_bpm, 2),
                "mfcc_mean": round(float(row.get("mfcc_mean", 0.0)), 4),
                "spectral_centroid": round(float(row.get("spectral_centroid", 0.0)), 2),
                "fusion_confidence": scene_type_confidence,
            }
            canonical_records.append(final_record)

            visual_clean_rows.append({
                "scene": int(row["scene"]),
                "time": str(row["time"]),
                "raw_motion": round(float(row.get("raw_motion", 0.0)), 4),
                "M": round(motion, 4),
                "O": round(obj_score, 4),
                "camera_angle": camera_angle_str,
                "camera_confidence": round(float(row.get("camera_confidence", 0.5)), 4),
                "face_emotion": display_face_emo,
                "face_confidence": round(face_conf if face_found else 0.0, 4),
                "face_found": face_found,
                "F": round(face_conf if face_found else 0.0, 4),
                "objects": objects,
                "emotion": scene_emotion,
                "scene_type": scene_type,
                "scene_type_confidence": scene_type_confidence,
                "classification_reliable": classification_reliable,
            })

        return canonical_records, pd.DataFrame(canonical_records), pd.DataFrame(visual_clean_rows)

    def classify_scene_type_multimodal(self, merged_df: pd.DataFrame) -> list[dict]:
        """Classify scene types using a 3-tier approach (per-scene):
          1. Trained Random Forest (per-scene confidence ≥ 0.35)
          2. CLIP zero-shot visual classification (fallback for low-confidence RF scenes)
          3. Audio/motion rule-based heuristics (last resort)
        """
        n = len(merged_df)

        # Per-scene results array: None means "needs fallback"
        results: list[dict | None] = [None] * n
        tier_log: list[str] = [""] * n  # track which tier each scene used

        # ── Tier 1: Trained Random Forest ──────────────────────────────────────
        if not settings.USE_TRAINED_SCENE_MODELS:
            print("[SceneModel] RF skipped (USE_TRAINED_SCENE_MODELS=False)")
        elif getattr(self.mm, 'scene_classifier', None) is not None and getattr(self.mm, 'scene_label_encoder', None) is not None and not merged_df.empty:
            try:
                from app.ml.feature_assembly import assemble_features
                vocab = getattr(self.mm, 'object_vocab', [])
                schema = getattr(self.mm, 'scene_feature_schema', [])

                X_df = assemble_features(merged_df, vocab)
                if schema:
                    for col in schema:
                        if col not in X_df.columns:
                            X_df[col] = 0.0
                    X_df = X_df[schema]

                preds = self.mm.scene_classifier.predict(X_df)
                probs = self.mm.scene_classifier.predict_proba(X_df)
                labels = self.mm.scene_label_encoder.inverse_transform(preds)

                # Per-scene decision: only accept RF result if this scene's confidence ≥ 0.35
                for idx, label in enumerate(labels):
                    conf = float(np.max(probs[idx]))
                    if conf >= 0.35:
                        results[idx] = {
                            "scene_type": label,
                            "confidence": round(conf, 4),
                            "classification_reliable": True
                        }
                        tier_log[idx] = "RF"
                    else:
                        tier_log[idx] = ""  # will be filled by CLIP or rules

                rf_accepted = sum(1 for r in results if r is not None)
                rf_fallback = n - rf_accepted
                print(f"[SceneModel] RF: {rf_accepted}/{n} scenes accepted (conf≥0.35), {rf_fallback} need fallback")
            except Exception as e:
                print(f"[SceneModel] RF inference error ({e}) — trying CLIP fallback")

        # ── Tier 2: CLIP zero-shot visual scene classification ──────────────────
        # Only run on scenes that don't yet have a result from Tier 1
        needs_clip = [i for i in range(n) if results[i] is None]
        clip_model = getattr(self.mm, 'clip_model', None)
        clip_processor = getattr(self.mm, 'clip_processor', None)

        if needs_clip and clip_model is not None and clip_processor is not None and not merged_df.empty:
            try:
                import torch
                from PIL import Image

                frame_paths = merged_df.get("frame_path", pd.Series([None] * n)).tolist() if "frame_path" in merged_df.columns else [None] * n
                # Only process scenes that still need classification
                valid_indices = [(i, frame_paths[i]) for i in needs_clip if frame_paths[i] and os.path.isfile(str(frame_paths[i]))]
                clip_scene_map: dict = {}
                batch_size = 8

                for batch_start in range(0, len(valid_indices), batch_size):
                    batch = valid_indices[batch_start:batch_start + batch_size]
                    images, indices = [], []
                    for i, p in batch:
                        try:
                            img_bgr = cv2.imread(str(p))
                            if img_bgr is not None:
                                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                                images.append(Image.fromarray(img_rgb))
                                indices.append(i)
                        except Exception:
                            continue

                    if not images:
                        continue

                    try:
                        inputs = clip_processor(
                            text=CLIP_SCENE_TEXT_PROMPTS,
                            images=images,
                            return_tensors="pt",
                            padding=True
                        )
                        with torch.no_grad():
                            outputs = clip_model(**inputs)
                            probs = outputs.logits_per_image.softmax(dim=-1).cpu().numpy()

                        for local_idx, global_idx in enumerate(indices):
                            best_cat_idx = int(np.argmax(probs[local_idx]))
                            best_conf = float(probs[local_idx][best_cat_idx])
                            clip_scene_map[global_idx] = (CLIP_SCENE_CATEGORIES[best_cat_idx], best_conf)
                    except Exception as clip_e:
                        print(f"[CLIP] Batch error: {clip_e}")
                        continue

                for row_idx in needs_clip:
                    if row_idx in clip_scene_map:
                        clip_label, clip_conf = clip_scene_map[row_idx]
                        row = merged_df.iloc[row_idx]
                        motion = float(row.get("M", 0.0))
                        audio_energy = float(row.get("A", 0.0))
                        # When CLIP is uncertain, fuse with audio/motion signal
                        if clip_conf < 0.20:
                            if motion >= 0.55 or (motion >= 0.40 and audio_energy >= 0.60):
                                clip_label, clip_conf = "Action", 0.55
                            elif audio_energy >= 0.60:
                                clip_label, clip_conf = "Thriller", 0.50
                            else:
                                clip_label, clip_conf = "Drama", 0.45
                        results[row_idx] = {
                            "scene_type": clip_label,
                            "confidence": round(clip_conf, 4),
                            "classification_reliable": clip_conf >= 0.20
                        }
                        tier_log[row_idx] = "CLIP"
            except Exception as e:
                print(f"[CLIP] Scene classification error: {e} — using rule-based fallback")

        # ── Tier 3: Lightweight rule-based fallback ─────────────────────────────
        for row_idx in range(n):
            if results[row_idx] is not None:
                continue
            row = merged_df.iloc[row_idx]
            motion = float(row.get("M", 0.0))
            audio_energy = float(row.get("A", 0.0))
            face_emo = str(row.get("face_emotion", "unknown")).lower()

            if motion >= 0.55 or (motion >= 0.40 and audio_energy >= 0.60):
                st, conf = "Action", 0.65
            elif face_emo == "happy":
                st, conf = "Comedy", 0.60
            elif face_emo in ["sad", "fear"] and audio_energy <= 0.40:
                st, conf = "Emotional", 0.55
            elif audio_energy >= 0.60:
                st, conf = "Thriller", 0.55
            else:
                st, conf = "Drama", 0.50

            results[row_idx] = {
                "scene_type": st,
                "confidence": conf,
                "classification_reliable": True
            }
            tier_log[row_idx] = "Rules"

        # Log per-scene tier assignments
        for i in range(n):
            scene_num = int(merged_df.iloc[i].get("scene", i + 1))
            print(f"[SceneModel] Scene {scene_num}: tier={tier_log[i]}, type={results[i]['scene_type']}, conf={results[i]['confidence']:.4f}")

        return results

    def classify_trailer_genre(self, final_df: pd.DataFrame) -> dict:
        """
        Trailer-Level Multi-Genre Probability Aggregator.
        Works for any genre: Action, Comedy, Romance, Thriller, Horror, Mystery, Adventure, Drama, etc.
        Based entirely on real scene-by-scene analysis — zero title keywords.
        """
        if final_df.empty:
            return {"dominant_genre": "Drama", "secondary_genre": None, "genre_mixture": {}}

        n = len(final_df)
        scene_types = final_df["scene_type"].value_counts().to_dict()

        avg_motion = float(final_df["M"].mean())
        avg_tempo = float(final_df["tempo_bpm"].mean())
        avg_energy = float(final_df["A"].mean())

        face_emotions = final_df["face_emotion"].value_counts().to_dict() if "face_emotion" in final_df.columns else {}
        audio_emotions = final_df["audio_emotion"].value_counts().to_dict() if "audio_emotion" in final_df.columns else {}
        audio_moods = final_df["audio_mood"].value_counts().to_dict() if "audio_mood" in final_df.columns else {}

        happy_r = face_emotions.get("happy", 0) / n
        angry_r = face_emotions.get("angry", 0) / n
        sad_r = face_emotions.get("sad", 0) / n
        fear_r = face_emotions.get("fear", 0) / n
        surprise_r = face_emotions.get("surprise", 0) / n

        audio_fear_r = audio_emotions.get("fear", 0) / n
        audio_sad_r = audio_emotions.get("sad", 0) / n
        audio_happy_r = audio_emotions.get("happy", 0) / n
        
        suspense_r = audio_moods.get("suspense", 0) / n
        intense_r = audio_moods.get("intense", 0) / n

        # Count scene types (visual ground truth anchors)
        action_r = scene_types.get("Action", 0) / n
        comedy_r = scene_types.get("Comedy", 0) / n
        romance_r = scene_types.get("Romance", 0) / n
        thriller_r = scene_types.get("Thriller", 0) / n
        adventure_r = scene_types.get("Adventure", 0) / n
        emotional_r = scene_types.get("Emotional", 0) / n
        drama_r = (scene_types.get("Drama", 0) + scene_types.get("Dialogue", 0)) / n
        horror_r = scene_types.get("Horror", 0) / n
        mystery_r = (scene_types.get("Mystery", 0) + scene_types.get("Suspense", 0)) / n

        scores = {
            "Action": action_r * 0.65 + intense_r * 0.15 + (avg_motion * 0.15 if avg_energy >= 0.40 else 0) + angry_r * 0.05,
            "Comedy": comedy_r * 0.65 + happy_r * 0.15 + audio_happy_r * 0.10 + (0.10 if avg_tempo >= 115 else 0),
            "Romance": romance_r * 0.65 + happy_r * 0.15 + (0.20 if avg_energy < 0.40 and emotional_r > 0.10 else 0),
            "Thriller": thriller_r * 0.60 + fear_r * 0.15 + suspense_r * 0.15 + intense_r * 0.10,
            "Horror": horror_r * 0.60 + fear_r * 0.20 + audio_fear_r * 0.10 + (0.10 if suspense_r > 0.25 and surprise_r > 0.10 else 0),
            "Adventure": adventure_r * 0.65 + avg_motion * 0.15 + (0.10 if avg_tempo >= 110 else 0) + surprise_r * 0.10,
            "Drama": drama_r * 0.50 + emotional_r * 0.25 + sad_r * 0.15 + audio_sad_r * 0.10,
            "Mystery": mystery_r * 0.55 + (suspense_r * 0.25 if mystery_r > 0.05 else 0.05) + (drama_r * 0.15 if suspense_r > 0.20 else 0) + fear_r * 0.05
        }

        # Ensure no negatives
        scores = {k: max(0.01, v) for k, v in scores.items()}

        total_s = sum(scores.values()) or 1.0
        mixture = {k: round(v / total_s, 4) for k, v in scores.items()}
        sorted_g = sorted(mixture.items(), key=lambda x: x[1], reverse=True)
        dominant = sorted_g[0][0]
        secondary = sorted_g[1][0] if len(sorted_g) > 1 and sorted_g[1][1] >= 0.12 else None

        return {
            "dominant_genre": dominant,
            "secondary_genre": secondary,
            "genre_mixture": mixture
        }

    @staticmethod
    def generate_insights(final_df: pd.DataFrame, genre_report: dict) -> dict:
        if final_df.empty:
            return {
                "average_emotional_intensity": 0,
                "engagement_level": "No scenes analyzed",
                "high_intensity_scenes": [],
                "dominant_genre": "Unknown",
                "genre_mixture": {},
                "scene_type_distribution": {},
                "audio_mood_distribution": {},
            }
        avg_ei = float(final_df["EI"].mean())
        high_scenes = final_df[final_df["level"] == "High"][["scene", "time", "scene_type", "EI"]]
        if avg_ei >= 0.70:
            engagement = "High engagement trailer"
        elif avg_ei >= 0.40:
            engagement = "Medium engagement trailer"
        else:
            engagement = "Low engagement trailer"
        # Emotion distribution across detected emotional scenes
        valid_face_emotions = final_df[final_df.get("face_found", False) == True]["face_emotion"] if "face_found" in final_df.columns else final_df["face_emotion"][final_df["face_emotion"] != "unknown"]
        if not valid_face_emotions.empty:
            video_emo_dist = valid_face_emotions.value_counts().to_dict()
        else:
            video_emo_dist = final_df["audio_emotion"].value_counts().to_dict()

        return {
            "average_emotional_intensity": round(avg_ei, 2),
            "engagement_level": engagement,
            "dominant_genre": genre_report.get("dominant_genre", "Action"),
            "secondary_genre": genre_report.get("secondary_genre"),
            "genre_mixture": genre_report.get("genre_mixture", {}),
            "high_intensity_scenes": high_scenes.to_dict(orient="records"),
            "scene_type_distribution": final_df["scene_type"].value_counts().to_dict(),
            "audio_mood_distribution": final_df["audio_mood"].value_counts().to_dict(),
            "video_emotion_distribution": video_emo_dist,
        }

    @staticmethod
    def clean_records(df: pd.DataFrame):
        if df.empty:
            return []
        df = df.replace({np.nan: None})
        records = df.to_dict(orient="records")
        for r in records:
            for k, v in list(r.items()):
                if isinstance(v, (np.integer,)):
                    r[k] = int(v)
                elif isinstance(v, (np.floating,)):
                    r[k] = round(float(v), 6)
        return records
