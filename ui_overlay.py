"""UI Overlay components for HUD."""
import cv2
from typing import List
import config

class UIOverlay:
    """Draws HUD text, mode indicators, and debug info onto the frame."""
    
    def draw_mode_indicator(self, frame: cv2.Mat, mode_name: str):
        """Draw a semi-transparent pill in the top-left with the mode name."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 80), (300, 140), (0, 0, 0), cv2.FILLED)
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        cv2.putText(frame, f"MODE: {mode_name}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    def draw_finger_states(self, frame: cv2.Mat, fingers: List[int]):
        """Show which fingers are up as small text/icons."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 160), (200, 200), (0, 0, 0), cv2.FILLED)
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        state_str = "".join([str(f) for f in fingers])
        cv2.putText(frame, f"Fingers: {state_str}", (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    def draw_fps(self, frame: cv2.Mat, fps: float):
        """Draw FPS in the top-right corner."""
        cv2.putText(frame, f"FPS: {int(fps)}", (config.FRAME_WIDTH - 150, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    def draw_instructions(self, frame: cv2.Mat):
        """Draw bottom bar with gesture legend."""
        h, w, _ = frame.shape
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - 50), (w, h), (0, 0, 0), cv2.FILLED)
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        legend = "PAINT: Indx=Draw, Indx+Mid=Select, All=Erase, Pinky=Clear | VOL: Thmb+Indx=Adjust | SWITCH: Ring=Vol, Indx+Mid+Ring=Paint"
        cv2.putText(frame, legend, (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
