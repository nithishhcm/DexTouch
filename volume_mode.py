"""System volume control mode."""
import cv2
import numpy as np
import sys
import time
import subprocess
import logging
from typing import List, Tuple
import config

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False
    logging.warning("pycaw not available. Windows volume control disabled.")

class VolumeMode:
    """Maps pinch distance to system volume."""
    
    def __init__(self):
        """Initialize VolumeMode and setup platform-specific audio controls."""
        self.last_volume = -1.0
        self.last_call_time = 0.0
        self.current_vol_percent = 0.0
        
        self.platform = sys.platform
        self.volume_obj = None
        
        if self.platform == 'win32' and PYCAW_AVAILABLE:
            try:
                # pycaw 20251023+: GetSpeakers() returns AudioDevice object
                # which exposes .EndpointVolume directly — no .Activate() needed
                speakers = AudioUtilities.GetSpeakers()
                self.volume_obj = speakers.EndpointVolume
                logging.info("pycaw volume control initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to initialize pycaw: {e}")

    def _set_system_volume(self, level_float: float):
        """Set the system volume to level_float [0.0 to 1.0]."""
        level_float = max(0.0, min(1.0, level_float))
        
        if self.platform == 'darwin':
            try:
                vol_int = int(level_float * 100)
                subprocess.run(["osascript", "-e", f"set volume output volume {vol_int}"], check=True)
            except Exception as e:
                logging.error(f"macOS volume error: {e}")
                
        elif self.platform == 'win32' and self.volume_obj:
            try:
                self.volume_obj.SetMasterVolumeLevelScalar(level_float, None)
            except Exception as e:
                logging.error(f"Windows volume error: {e}")
                
        elif self.platform.startswith('linux'):
            try:
                vol_int = int(level_float * 100)
                subprocess.run(["amixer", "sset", "Master", f"{vol_int}%"], check=False)
            except Exception as e:
                logging.error(f"Linux volume error: {e}")

    def update(self, fingers: List[int], landmark_list: List[Tuple[int, int]], frame: cv2.Mat, tracker) -> cv2.Mat:
        """Update volume if Index and Thumb are up, and draw visuals."""
        if fingers == [1, 1, 0, 0, 0] and len(landmark_list) > 8:
            distance, frame, p1_p2_info = tracker.get_distance(4, 8, frame)
            if p1_p2_info:
                cx, cy = p1_p2_info[4], p1_p2_info[5]
                
                vol_mapped = np.interp(distance, [config.VOLUME_MIN_DIST, config.VOLUME_MAX_DIST], [0.0, 1.0])
                self.current_vol_percent = vol_mapped * 100
                
                color = (0, 255, 0)
                if distance < config.VOLUME_MIN_DIST:
                    color = (0, 0, 255)
                elif distance > config.VOLUME_MAX_DIST:
                    color = (255, 0, 0)
                    
                cv2.circle(frame, (cx, cy), 15, color, cv2.FILLED)
                
                current_time = time.time()
                if (current_time - self.last_call_time) > (config.VOLUME_THROTTLE_MS / 1000.0):
                    if abs(vol_mapped - self.last_volume) > config.VOLUME_CHANGE_THRESHOLD:
                        self._set_system_volume(vol_mapped)
                        self.last_volume = vol_mapped
                        self.last_call_time = current_time

        bar_x1, bar_y1 = config.FRAME_WIDTH - 60, 150
        bar_x2, bar_y2 = config.FRAME_WIDTH - 20, 400
        cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (200, 200, 200), 3)
        fill_y = int(np.interp(self.current_vol_percent, [0, 100], [bar_y2, bar_y1]))
        cv2.rectangle(frame, (bar_x1, fill_y), (bar_x2, bar_y2), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, f"{int(self.current_vol_percent)}%", (bar_x1 - 10, bar_y2 + 30), 
                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

        return frame
