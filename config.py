"""Configuration constants for the Gesture Controller."""
import logging

# General
DEBUG = True
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# MediaPipe
MEDIAPIPE_MAX_HANDS = 1
DETECTION_CONFIDENCE = 0.75
TRACKING_CONFIDENCE = 0.75

# Paint Mode
DRAW_BRUSH_SIZE = 10
ERASE_BRUSH_SIZE = 50
COLORS = {
    "Red": (0, 0, 255),
    "Green": (0, 255, 0),
    "Blue": (255, 0, 0),
    "Yellow": (0, 255, 255),
    "Purple": (255, 0, 255)
}
SWATCH_WIDTH = 80
SWATCH_HEIGHT = 50

# Volume Mode
VOLUME_MIN_DIST = 20
VOLUME_MAX_DIST = 220
VOLUME_THROTTLE_MS = 150
VOLUME_CHANGE_THRESHOLD = 0.02

# App Modes
MODE_SWITCH_HOLD_SECONDS = 1.0
