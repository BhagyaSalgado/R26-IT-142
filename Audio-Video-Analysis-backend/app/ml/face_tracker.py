"""
Face Tracking and multi-face association within a single PySceneDetect shot.
Associates face detections across sampled frames using IoU overlap and Centroid distance.
"""

import numpy as np


def compute_iou(box1: list | np.ndarray, box2: list | np.ndarray) -> float:
    """Computes Intersection over Union (IoU) between two [x, y, w, h] boxes."""
    x1_min, y1_min, w1, h1 = box1  # Get the first bounding box coordinates
    x1_max, y1_max = x1_min + w1, y1_min + h1
# Calculate the bottom-right corner of box 2
    x2_min, y2_min, w2, h2 = box2
    x2_max, y2_max = x2_min + w2, y2_min + h2
# Calculate the coordinates of the intersection area
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
# Calculate intersection width # max() prevents a negative value when boxes don't overlap
    inter_w = max(0.0, inter_xmax - inter_xmin)
    inter_h = max(0.0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h  

    area1 = w1 * h1  # Calculate the area of the first bounding box
    area2 = w2 * h2  # Calculate the area of the second bounding box
    union_area = area1 + area2 - inter_area # Calculate the union area

    if union_area <= 0:  
        return 0.0
    return float(inter_area / union_area)

# COMPUTE NORMALIZED CENTROID DISTANCE
def compute_centroid_distance_norm(box1: list | np.ndarray, box2: list | np.ndarray, frame_diag: float) -> float:
    """Computes normalized Euclidean distance between box centroids relative to frame diagonal."""
    c1_x = box1[0] + box1[2] / 2.0 # Calculate the center X coordinate of box 1
    c1_y = box1[1] + box1[3] / 2.0 # Calculate the center Y coordinate of box 1

    c2_x = box2[0] + box2[2] / 2.0 # Calculate the center X coordinate of box 2
    c2_y = box2[1] + box2[3] / 2.0  # Calculate the center Y coordinate of box 2
# Calculate Euclidean distance between the two centers
    dist = np.sqrt((c1_x - c2_x) ** 2 + (c1_y - c2_y) ** 2)
    return float(dist / max(1.0, frame_diag))


class FaceTrack:  # Represents one continuously tracked face
    def __init__(self, track_id: int, initial_detection: dict, frame_idx: int):
        self.track_id = track_id   # Unique ID assigned to this face
        self.detections = [initial_detection]  # Store all detections belonging to this face
        self.frame_indices = [frame_idx]  # Store the frame numbers where the face was detected
        self.last_bbox = initial_detection["bbox"] # Store the latest bounding box
        self.last_frame_idx = frame_idx
# Add a new detection to this face track
    def add_detection(self, detection: dict, frame_idx: int):
        self.detections.append(detection)  # Add the new detection to the track
        self.frame_indices.append(frame_idx) # Store the frame number
        self.last_bbox = detection["bbox"]  # Update the latest bounding box
        self.last_frame_idx = frame_idx
# Calculate the average face area ratio
    @property
    def avg_area_ratio(self) -> float:   # Calculate the mean area ratio across all detections
        return float(np.mean([d["area_ratio"] for d in self.detections]))

    @property# Calculate the average detection confidence
    def avg_confidence(self) -> float:
        return float(np.mean([d["confidence"] for d in self.detections]))

    @property
    def avg_sharpness(self) -> float:  # Calculate the average face sharpness
        return float(np.mean([d["sharpness"] for d in self.detections]))

    @property  # Return the number of detections in this track
    def track_length(self) -> int:
        return len(self.detections)

# SHOT FACE TRACKER
class ShotFaceTracker:
    def __init__(self, iou_threshold: float = 0.25, max_centroid_dist_norm: float = 0.20):
        self.iou_threshold = iou_threshold
        self.max_centroid_dist_norm = max_centroid_dist_norm
# TRACK FACES WITHIN A SHOT
    def track_faces_in_shot(self, frame_detections: list[tuple[int, list[dict]]], frame_shape: tuple[int, int]) -> list[FaceTrack]:
        """
        Takes a sequence of (frame_idx, list_of_detected_faces) for a shot and associates them into FaceTracks.
        frame_shape: (height, width)
        """
        frame_h, frame_w = frame_shape[:2]
        frame_diag = np.sqrt(frame_w ** 2 + frame_h ** 2)  # Calculate the diagonal length of the frame

        tracks: list[FaceTrack] = []  # List that will contain all face tracks
        next_track_id = 1

        for frame_idx, detections in frame_detections: # Process each sampled frame
            if not detections:
                continue

            unmatched_detections = list(detections)

            # Match against active tracks that were seen recently (within last 3 frames)
            active_tracks = [t for t in tracks if (frame_idx - t.last_frame_idx) <= 3] # Only compare against tracks that were detected # within the previous 3 frames

            matched_track_ids = set()
# MATCH DETECTIONS TO EXISTING TRACKS
            for track in active_tracks:
                best_match_idx = -1  # Store the best matching detection index
                best_match_score = -1.0

                for i, det in enumerate(unmatched_detections):
                    iou = compute_iou(track.last_bbox, det["bbox"])
                    c_dist = compute_centroid_distance_norm(track.last_bbox, det["bbox"], frame_diag)

                    # Match score: high IoU or close centroid distance
                    if iou >= self.iou_threshold:
                        score = 0.7 * iou + 0.3 * (1.0 - c_dist)
                    elif c_dist <= self.max_centroid_dist_norm:
                        score = 0.5 * (1.0 - c_dist)
                    else:
                        score = -1.0

                    if score > best_match_score:
                        best_match_score = score
                        best_match_idx = i

                if best_match_idx >= 0 and best_match_score > 0.25:
                    matched_det = unmatched_detections.pop(best_match_idx)
                    track.add_detection(matched_det, frame_idx)
                    matched_track_ids.add(track.track_id)
 # CREATE NEW TRACKS
            # Any remaining unmatched detections start a new track
            for det in unmatched_detections:
                new_track = FaceTrack(next_track_id, det, frame_idx)
                tracks.append(new_track)
                next_track_id += 1

        # Sort tracks by importance: composite of track_length and average area ratio
        tracks.sort(key=lambda t: (t.track_length * 2.0 + t.avg_area_ratio * 100.0), reverse=True)
        return tracks
