"""Virtual paint canvas mode."""
import cv2
import numpy as np
from typing import List, Tuple
import config

class PaintMode:
    """Handles virtual drawing logic on a canvas."""
    
    def __init__(self):
        """Initialize the canvas and drawing state."""
        self.canvas = None
        self.draw_color = config.COLORS["Red"]
        self.brush_size = config.DRAW_BRUSH_SIZE
        self.prev_x = 0
        self.prev_y = 0
        
        # Swatch positions
        self.swatch_w = config.SWATCH_WIDTH
        self.swatch_h = config.SWATCH_HEIGHT
        self.swatches = []
        
        x_offset = 10
        for name, color in config.COLORS.items():
            self.swatches.append((name, color, x_offset, 10, x_offset + self.swatch_w, 10 + self.swatch_h))
            x_offset += self.swatch_w + 10

    def clear_canvas(self):
        """Clear the canvas by setting all pixels to black."""
        if self.canvas is not None:
            self.canvas.fill(0)

    def update(self, fingers: List[int], landmark_list: List[Tuple[int, int]], frame: cv2.Mat) -> cv2.Mat:
        """Update the paint canvas based on gestures and blend with frame."""
        if self.canvas is None:
            self.canvas = np.zeros_like(frame)

        if not landmark_list or len(landmark_list) < 9:
            return self._blend(frame)

        x8, y8 = landmark_list[8]  # Index tip

        # 1. DRAW MODE -> Index up, Middle down [_, 1, 0, _, _]
        if fingers[1] == 1 and fingers[2] == 0:
            if self.prev_x == 0 and self.prev_y == 0:
                self.prev_x, self.prev_y = x8, y8
            
            cv2.line(self.canvas, (self.prev_x, self.prev_y), (x8, y8), self.draw_color, self.brush_size)
            self.prev_x, self.prev_y = x8, y8

        # 2. SELECT MODE -> Index up, Middle up [_, 1, 1, _, _]
        elif fingers[1] == 1 and fingers[2] == 1:
            self.prev_x, self.prev_y = 0, 0  # reset streak
            cv2.circle(frame, (x8, y8), 15, self.draw_color, cv2.FILLED)
            
            # Check for color selection
            for name, color, x1, y1, x2, y2 in self.swatches:
                if x1 < x8 < x2 and y1 < y8 < y2:
                    self.draw_color = color
                    break

        # 3. ERASE MODE -> All five fingers up [1, 1, 1, 1, 1]
        elif fingers == [1, 1, 1, 1, 1]:
            if self.prev_x == 0 and self.prev_y == 0:
                self.prev_x, self.prev_y = x8, y8
            cv2.line(self.canvas, (self.prev_x, self.prev_y), (x8, y8), (0, 0, 0), config.ERASE_BRUSH_SIZE)
            self.prev_x, self.prev_y = x8, y8
            cv2.circle(frame, (x8, y8), config.ERASE_BRUSH_SIZE // 2, (255, 255, 255), 2)

        # 4. CLEAR ALL -> Only Pinky up [0, 0, 0, 0, 1]
        elif fingers == [0, 0, 0, 0, 1]:
            self.clear_canvas()
            
        else:
            self.prev_x, self.prev_y = 0, 0

        # Draw swatches
        for name, color, x1, y1, x2, y2 in self.swatches:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FILLED)
            if color == self.draw_color:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 3)

        return self._blend(frame)

    def _blend(self, frame: cv2.Mat) -> cv2.Mat:
        """Blend the canvas onto the original frame."""
        img_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 10, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        
        frame_bg = cv2.bitwise_and(frame, img_inv)
        return cv2.bitwise_or(frame_bg, self.canvas)
