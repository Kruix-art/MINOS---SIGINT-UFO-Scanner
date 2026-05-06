# MINOS---SIGINT-UFO-Scanner (ANDROID ONLY)
A real time micro motion tracking display for phones with the intent of tracking objects HIGH in the sky in style. 


A lightweight real-time SIGINT-style motion scanner built with Python, OpenCV, and Kivy.

Designed for Android / Pydroid 3 and desktop environments, this project turns a camera feed into a stylized low-level surveillance system capable of tracking extremely small motion signatures — including distant lights, micro movement, airborne particles, and fast moving anomalies.

The project combines:

Micro-motion detection
Radar-style object tracking
Terminal-inspired holographic overlays
Wireframe / scanline rendering
Real-time motion telemetry
Experimental “UFO scanner” behavior
Features
UFO / Micro Motion Detection

Tracks movement down to near pixel-level changes.

Unlike traditional motion trackers that require large blobs, this scanner can detect:

Tiny moving lights
Distant aircraft
Fast particles
Small insects
Faraway movement signatures
Sensor anomalies

Sensitivity can be tuned live through thresholds and motion filtering.

Radar System

Includes a real-time radar overlay that:

Tracks detected motion points
Maps movement into radar space
Sweeps continuously
Displays target blips
Simulates SIGINT / aerospace scanning systems

Targets appear dynamically as motion enters the camera frame.

SIGINT Visual Style

Inspired by:

Military ISR systems
Analog surveillance hardware
CRT terminals
Low-poly PS2 rendering
Tactical scan overlays
Thermal imaging systems

Includes:

Green terminal overlays
Scanlines
Bracket tracking
Motion vectors
Skeleton-like point linking
Wireframe effects
Screenshots


Requirements
Desktop
Python 3.10+
OpenCV
NumPy
Kivy

Install dependencies:

pip install opencv-python kivy numpy
Android (Pydroid 3)

Recommended:

Pydroid 3
OpenCV plugin
Kivy support package

The script was designed specifically to remain lightweight enough for mobile realtime rendering.

Running
python minos_sigint_ufo_scanner_radar.py
Controls
Control	Function
Motion Toggle	Enables/disables motion tracking
Radar Toggle	Enables radar system
Palette Button	Cycles render palettes
Threshold Slider	Motion sensitivity
Box Color Button	Changes overlay color
UFO Mode	Enables ultra-sensitive micro motion
UFO Scanner Mode

The UFO mode lowers the minimum motion area to near pixel-level detection.

Example settings:

self.motion_min_area = 1
self.motion_threshold = 6
self.motion_blur = 1

This enables tracking of extremely small movement signatures.

Because of this sensitivity, environmental noise may also become visible:

Dust
Compression artifacts
Camera grain
Reflections
Insects
Atmospheric flicker
Performance Notes

For smoother mobile performance:

Recommended:

FRAME_W = 640
FRAME_H = 360

Disable:

Heavy wireframe rendering
Dense point linking
High contour counts

if FPS becomes unstable.

Project Goals

MINOS SIGINT is intended as:

An experimental visualization project
A realtime motion analysis prototype
A stylized surveillance interface
A synthetic ISR aesthetic system
A sci-fi inspired scanner interface

This project is not intended for security or aerospace use.

Future Ideas

Planned / experimental concepts:

Thermal fusion mode
AI object labeling
Biometric silhouette tracking
Star tracking mode
Low-light amplification
Point-cloud motion accumulation
Satellite-style map overlay
Synthetic targeting telemetry
Multi-camera fusion
Audio-reactive SIGINT mode
License

MIT License

Credits

Built with:

Python
OpenCV
Kivy
NumPy

Inspired by:

Tactical ISR systems
Analog military displays
Retro-futurism
Experimental surveillance aesthetics
PS1 / PS2 era rendering pipelines
