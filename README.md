# Gesture-Controlled Interface

A real-time dual-mode gesture-controlled application using Python, OpenCV, and MediaPipe. 

## Setup Instructions
1. Run setup:
   - Windows: `setup.bat`
   - Linux/macOS: `bash setup.sh`
   *(Alternatively: `pip install -r requirements.txt`)*

2. Start the application:
   ```bash
   python main.py
   ```

## OS Specific Notes
- **macOS**: You must grant Terminal/iTerm camera permissions in System Preferences > Security & Privacy.
- **Windows**: `pycaw` requires `comtypes`, which is included in `requirements.txt`.
- **Linux**: The volume controller uses `amixer`. You may need to install `alsa-utils` (`sudo apt install alsa-utils`).

## Gesture Cheat-Sheet

| Mode   | Action        | Gesture (Fingers Up)            | Description |
|--------|---------------|---------------------------------|-------------|
| ANY    | Switch Volume | Ring only `[0,0,0,1,0]`         | Hold for 1s to enter Volume Mode. |
| ANY    | Switch Paint  | Index+Middle+Ring `[0,1,1,1,0]` | Hold for 1s to enter Paint Mode. |
| PAINT  | Draw          | Index `[_,1,0,_,_]`             | Draws with current color. |
| PAINT  | Select Color  | Index+Middle `[_,1,1,_,_]`      | Hover over swatches to select. |
| PAINT  | Erase         | All Fingers `[1,1,1,1,1]`       | Acts as an eraser. |
| PAINT  | Clear Canvas  | Pinky `[0,0,0,0,1]`             | Clears all drawings. |
| VOLUME | Adjust Vol    | Thumb+Index `[1,1,0,0,0]`       | Pinch to change volume. |
