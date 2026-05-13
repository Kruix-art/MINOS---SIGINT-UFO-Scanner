# MINOS - SIGINT // UFO Scanner  
## Advanced Tracking Module for Android

**MINOS - SIGINT // UFO Scanner** is an experimental Android-friendly computer vision scanner built with **Python, Kivy, OpenCV, and YOLO ONNX**.

It turns a phone camera into a sci-fi SIGINT-style motion analysis tool with reticle capture, micro-motion detection, stabilized target locking, radar overlays, zoomed target inspection, and one-time AI snap tagging.

This project is designed to run on Android using **Pydroid 3**.

---

## Features

- Live Android camera feed
- Pixel-level micro-motion detection
- Reticle-based target capture
- Advanced stabilized target tracking
- Kalman prediction smoothing
- Optical flow recovery
- Local motion reacquire
- Target memory when object temporarily disappears
- YOLO ONNX snap-tagging after capture
- YOLO runs once, then shuts off during tracking to save performance
- Enlarged target inspector window
- Radar-style motion display
- Digital camera zoom
- Manual focus slider when supported
- Exposure lock and white balance lock attempts
- Compact UI mode to hide sliders
- Terminal-green SIGINT visual style

---

## What This Is

This is a visual computer-vision experiment.

It does not emit radar, transmit signals, interfere with aircraft, or interact with anything physically.  
All tracking happens locally by analyzing pixels from the phone camera.

---

## Requirements

### Android

Recommended:

- Android phone
- Pydroid 3
- Pydroid repository plugin
- OpenCV installed in Pydroid
- Kivy installed in Pydroid
- NumPy installed in Pydroid

### Python Packages

Install these in Pydroid 3:

```bash
pip install numpy
pip install opencv-python
pip install kivy

If opencv-python gives issues on Android, install OpenCV from the Pydroid 3 plugin/repository instead.

File Structure

Recommended folder layout:

/storage/emulated/0/Python Projects/
│
├── minos_sigint_ufo_scanner_advanced_lock.py
├── download_minos_mobile_models_fixed.py
│
└── models/
    └── yolov8n.onnx

The scanner expects the YOLO model here:

/storage/emulated/0/Python Projects/models/yolov8n.onnx
Installation on Android / Pydroid 3
1. Install Pydroid 3

Install Pydroid 3 from the Play Store.

Also install:

Pydroid repository plugin
Pydroid permissions plugin if needed
2. Create the Project Folder

Open your Android file manager and create:

/storage/emulated/0/Python Projects/

Inside it, create:

/storage/emulated/0/Python Projects/models/
3. Add the Scanner Script

Copy this file into:

/storage/emulated/0/Python Projects/
minos_sigint_ufo_scanner_advanced_lock.py
4. Download the Model

Run the downloader script:

python download_minos_mobile_models_fixed.py

It should place:

yolov8n.onnx

inside:

/storage/emulated/0/Python Projects/models/
5. Run the Scanner

Run:

python minos_sigint_ufo_scanner_advanced_lock.py

Allow camera permission when Android asks.

Controls
Main Buttons
Button	Function
CAPTURE RETICLE	Locks the strongest motion near the center reticle
UNLOCK TARGET	Clears the current target
SNAP YOLO	Enables/disables one-time YOLO tagging
FLOW ON	Enables optical-flow recovery
MODE	Cycles visual render mode
RADAR ON	Toggles radar overlay
FOCUS AUTO/MAN	Attempts manual focus control
SLIDERS HIDE	Hides sliders for more screen space
How Target Lock Works

The scanner does not constantly auto-lock random motion.

The intended flow is:

Aim reticle at target
↓
Press CAPTURE
↓
Scanner locks the best micro-motion near center
↓
YOLO tags it once
↓
YOLO shuts off
↓
Kalman + optical flow + motion memory keep tracking

This keeps performance better on Android and prevents the AI from constantly identifying unrelated background objects.

Tracking System

The advanced tracker combines:

Micro-Motion Detection

Detects tiny pixel changes in the camera feed.

Kalman Prediction

Smooths motion and predicts where the target should move next.

Optical Flow

Tracks small local image features around the locked target.

Local Reacquire

If motion disappears briefly, the scanner searches near the predicted target position.

Target Memory

The scanner remembers:

last position
velocity
box size
average brightness
local color profile
last known target area

This helps stabilize the lock.

YOLO Snap Tagging

YOLO is used only once per capture.

After a successful lock:

YOLO scans the locked target crop
assigns a label/confidence
stores the tag
then shuts off during tracking

Example labels:

AIRPLANE
BIRD
CAR
PERSON
UNKNOWN

If no confident object is found, the target is labeled:

UNKNOWN
Performance Tips

For smoother Android performance:

Use compact slider mode
Keep camera zoom under 3x
Keep max motion points around 150–220
Use YOLO snap once, not continuous AI
Turn off thermal/dither mode if laggy
Use exposure lock if the screen keeps flickering
Use a tripod for sky tracking

Recommended settings:

Threshold: 6–12
Min Area: 1–3 px
Max Points: 150–220
Camera Zoom: 1x–3x
Lock Radius: 60–90 px
Flow Radius: 24–40 px
Known Limitations
Manual focus may not work on every Android phone.
Exposure lock may be ignored by some camera drivers.
YOLO can only identify classes it was trained on.
Tiny sky objects may be labeled UNKNOWN.
Digital zoom reduces image quality.
Hand shake can create false motion.
Low light increases noise.
Safety / Legal Notes

This app only analyzes camera pixels locally.

It does not:

emit radar
transmit signals
interfere with aircraft
communicate with drones
affect anything you point it at
@ Copyright Tyler Vinge 2026
Use responsibly:

Do not shine lasers at aircraft
Do not record people without permission where prohibited
Do not use while driving
Follow local drone/aircraft/privacy laws
License

MIT License

You may use, modify, distribute, and remix this project freely as long as the license notice is included.

Credits

Built with:

Python
Kivy
OpenCV
NumPy
YOLO ONNX

Concept and visual style inspired by:

SIGINT interfaces
aerospace tracking displays
CRT terminals
radar screens
sci-fi surveillance systems
MINOS project visual language
