"""Entry point for the Gesture-Controlled Interface."""
import cv2
import time
from collections import deque
import logging
from hand_tracker import HandTracker
from paint_mode import PaintMode
from volume_mode import VolumeMode
from ui_overlay import UIOverlay
import config

# Suppress verbose debug logs from comtypes and mediapipe internals
logging.getLogger("comtypes").setLevel(logging.WARNING)
logging.getLogger("comtypes._post_coinit.unknwn").setLevel(logging.WARNING)
WINDOW_NAME = "Gesture Controller  |  Q or ESC to quit"

def main():
    logging.info("Starting Gesture-Controlled Interface...")
    
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        logging.error("Failed to open webcam. Please check your camera index or permissions.")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    
    tracker = HandTracker()
    paint_mode = PaintMode()
    volume_mode = VolumeMode()
    ui = UIOverlay()
    
    # Mode states
    active_mode = "PAINT" 
    
    # Switching logic states
    switch_start_time = 0.0
    is_switching = False
    target_mode = ""
    
    fps_times = deque(maxlen=30)
    
    # Create window explicitly so X-button close detection works
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, config.FRAME_WIDTH, config.FRAME_HEIGHT)
    
    while True:
        success, frame = cap.read()
        if not success:
            logging.warning("Failed to grab frame.")
            break
            
        frame = cv2.flip(frame, 1)  # Mirror for intuitive use
        
        # 1. Process Hands
        frame = tracker.find_hands(frame)
        landmark_list = tracker.get_landmark_list(frame)
        fingers = tracker.get_fingers_up()
        
        # 2. Mode Switching Logic
        if fingers == [0, 0, 0, 1, 0]:
            if not is_switching or target_mode != "VOLUME":
                is_switching = True
                switch_start_time = time.time()
                target_mode = "VOLUME"
        elif fingers == [0, 1, 1, 1, 0]:
            if not is_switching or target_mode != "PAINT":
                is_switching = True
                switch_start_time = time.time()
                target_mode = "PAINT"
        else:
            is_switching = False
            
        # Check hold duration
        if is_switching:
            elapsed = time.time() - switch_start_time
            if elapsed >= config.MODE_SWITCH_HOLD_SECONDS:
                active_mode = target_mode
                is_switching = False
                logging.info(f"Switched to {active_mode} mode.")
            else:
                cv2.putText(frame, f"Switching to {target_mode}... {config.MODE_SWITCH_HOLD_SECONDS - elapsed:.1f}s", 
                            (400, config.FRAME_HEIGHT // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 165, 255), 3)

        # 3. Dispatch to Active Mode
        if active_mode == "PAINT":
            frame = paint_mode.update(fingers, landmark_list, frame)
        elif active_mode == "VOLUME":
            frame = volume_mode.update(fingers, landmark_list, frame, tracker)
            
        # 4. Overlay UI Elements
        ui.draw_mode_indicator(frame, active_mode)
        ui.draw_finger_states(frame, fingers)
        ui.draw_instructions(frame)
        
        # 5. FPS Calc
        current_time = time.time()
        fps_times.append(current_time)
        if len(fps_times) > 1:
            fps = len(fps_times) / (fps_times[-1] - fps_times[0])
            ui.draw_fps(frame, fps)
            
        # 6. Show Frame
        cv2.imshow(WINDOW_NAME, frame)
        
        # IMPORTANT: Click inside the OpenCV window first to give it keyboard focus.
        # Then press Q or ESC to quit, C to clear the paint canvas.
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 27 = ESC
            break
        elif key == ord('c'):
            paint_mode.clear_canvas()
        
        # Also allow closing via the window's X button
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
    tracker.close()
    logging.info("Exiting successfully.")

if __name__ == "__main__":
    main()
