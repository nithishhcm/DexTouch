"""Hand tracking module using MediaPipe Tasks API (0.10.30+)."""
import math
import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.components import containers
from mediapipe import Image, ImageFormat
from typing import List, Tuple
import config

# Drawing utilities from tasks API
mp_drawing = vision.drawing_utils if hasattr(vision, 'drawing_utils') else None

# Hand connections for drawing
HAND_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
])


class HandTracker:
    """Wrapper for MediaPipe HandLandmarker Tasks API to extract landmarks and finger states."""

    def __init__(self, max_hands: int = config.MEDIAPIPE_MAX_HANDS,
                 detection_confidence: float = config.DETECTION_CONFIDENCE,
                 tracking_confidence: float = config.TRACKING_CONFIDENCE):
        """Initialize the MediaPipe HandLandmarker model."""
        model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"MediaPipe model not found at '{model_path}'.\n"
                "Please download it with:\n"
                "  Invoke-WebRequest -Uri https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task -OutFile hand_landmarker.task"
            )

        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.detection_result = None
        self.tip_ids = [4, 8, 12, 16, 20]
        self._frame_timestamp_ms = 0

    def find_hands(self, frame: cv2.Mat) -> cv2.Mat:
        """Process the frame to find hands. Draws landmarks if DEBUG is True."""
        self._frame_timestamp_ms += 33  # Approx 30 FPS timestamp

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=img_rgb)
        self.detection_result = self.landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

        if config.DEBUG and self.detection_result and self.detection_result.hand_landmarks:
            for hand in self.detection_result.hand_landmarks:
                self._draw_landmarks(frame, hand)

        return frame

    def _draw_landmarks(self, frame: cv2.Mat, hand_landmarks: list):
        """Manually draw landmarks and connections onto the frame."""
        h, w = frame.shape[:2]
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]

        for (a, b) in HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 200, 0), 2)
        for pt in pts:
            cv2.circle(frame, pt, 5, (0, 255, 0), cv2.FILLED)
            cv2.circle(frame, pt, 5, (255, 255, 255), 1)

    def get_landmark_list(self, frame: cv2.Mat) -> List[Tuple[int, int]]:
        """Return a list of (x, y) pixel coordinates for all 21 landmarks."""
        lm_list = []
        if not self.detection_result or not self.detection_result.hand_landmarks:
            return lm_list

        h, w = frame.shape[:2]
        for lm in self.detection_result.hand_landmarks[0]:
            lm_list.append((int(lm.x * w), int(lm.y * h)))
        return lm_list

    def get_fingers_up(self) -> List[int]:
        """Return [Thumb, Index, Middle, Ring, Pinky] — 1=extended, 0=folded."""
        if not self.detection_result or not self.detection_result.hand_landmarks:
            return [0, 0, 0, 0, 0]

        lm_list_raw = self.detection_result.hand_landmarks[0]
        lm = [(l.x, l.y) for l in lm_list_raw]

        # Determine handedness (MediaPipe returns mirrored labels for live video)
        is_right = True
        if self.detection_result.handedness:
            label = self.detection_result.handedness[0][0].category_name
            # In a mirrored/selfie view, "Left" label means the user's right hand
            is_right = (label == "Left")

        fingers = []

        # Thumb: x-axis comparison
        if is_right:
            fingers.append(1 if lm[self.tip_ids[0]][0] < lm[self.tip_ids[0] - 1][0] else 0)
        else:
            fingers.append(1 if lm[self.tip_ids[0]][0] > lm[self.tip_ids[0] - 1][0] else 0)

        # Index → Pinky: y-axis comparison (tip vs PIP joint)
        for i in range(1, 5):
            fingers.append(1 if lm[self.tip_ids[i]][1] < lm[self.tip_ids[i] - 2][1] else 0)

        return fingers

    def get_distance(self, p1_idx: int, p2_idx: int, frame: cv2.Mat) -> Tuple[float, cv2.Mat, List[int]]:
        """Calculate pixel distance between two landmarks; draw connecting line and midpoint circle."""
        lm_list = self.get_landmark_list(frame)
        if not lm_list or len(lm_list) <= max(p1_idx, p2_idx):
            return 0.0, frame, []

        x1, y1 = lm_list[p1_idx]
        x2, y2 = lm_list[p2_idx]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        distance = math.hypot(x2 - x1, y2 - y1)

        cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(frame, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
        cv2.circle(frame, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
        cv2.circle(frame, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

        return distance, frame, [x1, y1, x2, y2, cx, cy]

    def close(self):
        """Release MediaPipe resources."""
        self.landmarker.close()
