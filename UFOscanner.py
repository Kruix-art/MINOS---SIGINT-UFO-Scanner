# minos_sigint_ufo_scanner.py
# Android/Pydroid 3 friendly Kivy + OpenCV SIGINT / UFO micro-motion scanner.
#
# Features:
# - Live camera feed
# - Terminal-green SIGINT overlay
# - UFO / MICRO motion mode capable of tracking tiny pixel-level movement
# - Sensitivity slider for threshold
# - Min-area slider down to 1 pixel
# - Max point limiter to avoid lag
# - Motion persistence trails
# - Optional thermal/dither render modes
# - No fake idle auto-animation: overlays are driven by actual camera frame difference only
#
# Install in Pydroid 3:
#   pip install kivy opencv-python numpy
#
# Run:
#   python minos_sigint_ufo_scanner.py

import os
import time
import math
import random
import threading
from collections import deque

import cv2
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout


def request_android_permissions():
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.CAMERA,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
        ])
    except Exception:
        pass


GREEN = (0, 255, 110)
AMBER = (255, 180, 40)
RED = (255, 50, 50)
CYAN = (40, 220, 255)
WHITE = (230, 255, 235)


class MinosSigintUFO(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.capture = None
        self.running = True
        self.frame = None
        self.frame_lock = threading.Lock()
        self.camera_index = 0

        # Render / scan state
        self.render_mode = "NORMAL"  # NORMAL, EDGE, THERMAL, DITHER
        self.palette_i = 0
        self.overlay_color = GREEN
        self.overlay_i = 0
        self.scanline_enabled = True
        self.mirror = False

        # UFO / micro-motion scanner settings
        self.ufo_scan_enabled = True
        self.motion_min_area = 1          # pixel-level tracking
        self.motion_threshold = 6         # lower = more sensitive
        self.motion_blur = 1              # 1 means no blur; 3 helps reduce noise
        self.motion_max_points = 220      # safety cap for mobile performance
        self.motion_decay_seconds = 1.20
        self.motion_link_distance = 46
        self.prev_motion_gray = None
        self.micro_points = []
        self.motion_history = deque(maxlen=900)
        self.last_motion_count = 0
        self.last_motion_area = 0
        self.fps_clock = time.time()
        self.fps_frames = 0
        self.fps = 0.0

        # Optional object detection placeholders remain off by default.
        self.motion_boxes_enabled = True

        # Radar overlay system
        self.radar_enabled = True
        self.radar_sweep_angle = 0.0
        self.radar_blips = deque(maxlen=450)
        self.radar_decay_seconds = 2.4
        self.radar_radius = 58
        self.radar_margin = 16

        # UI
        self.image = Image(size_hint=(1, 1), allow_stretch=True, keep_ratio=True)
        self.add_widget(self.image)

        self.status = Label(
            text="MINOS SIGINT // UFO MICRO-MOTION SCANNER",
            size_hint=(1, None),
            height=dp(26),
            pos_hint={"x": 0, "top": 1},
            color=(0, 1, 0.42, 1),
            font_size=dp(13),
            bold=True,
        )
        self.add_widget(self.status)

        self.controls = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(162),
            pos_hint={"x": 0, "y": 0},
            spacing=dp(2),
            padding=[dp(4), dp(2), dp(4), dp(2)],
        )
        self.add_widget(self.controls)

        row = GridLayout(cols=6, size_hint=(1, None), height=dp(42), spacing=dp(3))
        self.controls.add_widget(row)

        self.btn_ufo = ToggleButton(text="UFO\nSCAN", state="down", font_size=dp(11))
        self.btn_ufo.bind(on_press=self.toggle_ufo)
        row.add_widget(self.btn_ufo)

        self.btn_render = Button(text="MODE\nNORMAL", font_size=dp(11))
        self.btn_render.bind(on_press=self.cycle_render)
        row.add_widget(self.btn_render)

        self.btn_color = Button(text="BOXCLR\nGREEN", font_size=dp(11))
        self.btn_color.bind(on_press=self.cycle_color)
        row.add_widget(self.btn_color)

        self.btn_scanline = ToggleButton(text="SCAN\nLINES", state="down", font_size=dp(11))
        self.btn_scanline.bind(on_press=self.toggle_scanlines)
        row.add_widget(self.btn_scanline)

        self.btn_radar = ToggleButton(text="RADAR\nON", state="down", font_size=dp(11))
        self.btn_radar.bind(on_press=self.toggle_radar)
        row.add_widget(self.btn_radar)

        self.btn_mirror = ToggleButton(text="MIRROR\nOFF", state="normal", font_size=dp(11))
        self.btn_mirror.bind(on_press=self.toggle_mirror)
        row.add_widget(self.btn_mirror)

        self.threshold_label = Label(
            text=f"SENS / THRESHOLD: {self.motion_threshold}  | lower = more sensitive",
            size_hint=(1, None), height=dp(24), color=(0, 1, 0.42, 1), font_size=dp(12)
        )
        self.controls.add_widget(self.threshold_label)
        self.threshold_slider = Slider(min=1, max=60, value=self.motion_threshold, step=1, size_hint=(1, None), height=dp(28))
        self.threshold_slider.bind(value=self.on_threshold)
        self.controls.add_widget(self.threshold_slider)

        self.area_label = Label(
            text=f"MIN MOTION AREA: {self.motion_min_area}px  | 1 = pixel-level UFO scan",
            size_hint=(1, None), height=dp(24), color=(0, 1, 0.42, 1), font_size=dp(12)
        )
        self.controls.add_widget(self.area_label)
        self.area_slider = Slider(min=1, max=80, value=self.motion_min_area, step=1, size_hint=(1, None), height=dp(28))
        self.area_slider.bind(value=self.on_area)
        self.controls.add_widget(self.area_slider)

        self.points_label = Label(
            text=f"MAX POINTS: {self.motion_max_points}",
            size_hint=(1, None), height=dp(24), color=(0, 1, 0.42, 1), font_size=dp(12)
        )
        self.controls.add_widget(self.points_label)
        self.points_slider = Slider(min=25, max=500, value=self.motion_max_points, step=5, size_hint=(1, None), height=dp(28))
        self.points_slider.bind(value=self.on_points)
        self.controls.add_widget(self.points_slider)

        request_android_permissions()
        self.start_camera()
        Clock.schedule_interval(self.update, 1 / 30.0)

    def start_camera(self):
        self.capture = cv2.VideoCapture(self.camera_index)
        try:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
        except Exception:
            pass

        t = threading.Thread(target=self.camera_loop, daemon=True)
        t.start()

    def camera_loop(self):
        while self.running:
            if self.capture is None or not self.capture.isOpened():
                time.sleep(0.05)
                continue
            ok, frame = self.capture.read()
            if not ok or frame is None:
                time.sleep(0.01)
                continue
            if self.mirror:
                frame = cv2.flip(frame, 1)
            with self.frame_lock:
                self.frame = frame
            time.sleep(0.001)

    def toggle_ufo(self, *_):
        self.ufo_scan_enabled = self.btn_ufo.state == "down"
        self.btn_ufo.text = "UFO\nSCAN" if self.ufo_scan_enabled else "UFO\nOFF"
        self.prev_motion_gray = None
        self.motion_history.clear()

    def toggle_scanlines(self, *_):
        self.scanline_enabled = self.btn_scanline.state == "down"

    def toggle_radar(self, *_):
        self.radar_enabled = self.btn_radar.state == "down"
        self.btn_radar.text = "RADAR\nON" if self.radar_enabled else "RADAR\nOFF"
        if not self.radar_enabled:
            self.radar_blips.clear()

    def toggle_mirror(self, *_):
        self.mirror = self.btn_mirror.state == "down"
        self.btn_mirror.text = "MIRROR\nON" if self.mirror else "MIRROR\nOFF"
        self.prev_motion_gray = None

    def cycle_render(self, *_):
        modes = ["NORMAL", "EDGE", "THERMAL", "DITHER"]
        idx = modes.index(self.render_mode)
        self.render_mode = modes[(idx + 1) % len(modes)]
        self.btn_render.text = "MODE\n" + self.render_mode

    def cycle_color(self, *_):
        colors = [
            ("GREEN", GREEN),
            ("CYAN", CYAN),
            ("AMBER", AMBER),
            ("RED", RED),
            ("WHITE", WHITE),
        ]
        self.overlay_i = (self.overlay_i + 1) % len(colors)
        name, col = colors[self.overlay_i]
        self.overlay_color = col
        self.btn_color.text = "BOXCLR\n" + name

    def on_threshold(self, _, value):
        self.motion_threshold = int(value)
        self.threshold_label.text = f"SENS / THRESHOLD: {self.motion_threshold}  | lower = more sensitive"

    def on_area(self, _, value):
        self.motion_min_area = int(value)
        self.area_label.text = f"MIN MOTION AREA: {self.motion_min_area}px  | 1 = pixel-level UFO scan"

    def on_points(self, _, value):
        self.motion_max_points = int(value)
        self.points_label.text = f"MAX POINTS: {self.motion_max_points}"

    def render_base(self, frame):
        if self.render_mode == "NORMAL":
            return frame.copy()

        if self.render_mode == "EDGE":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 45, 120)
            out = np.zeros_like(frame)
            out[:, :, 1] = edges
            out[:, :, 0] = edges // 5
            return cv2.addWeighted(frame, 0.28, out, 1.0, 0)

        if self.render_mode == "THERMAL":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            eq = cv2.equalizeHist(gray)
            return cv2.applyColorMap(eq, cv2.COLORMAP_TURBO)

        if self.render_mode == "DITHER":
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            bayer = np.array([
                [0, 8, 2, 10],
                [12, 4, 14, 6],
                [3, 11, 1, 9],
                [15, 7, 13, 5]
            ], dtype=np.uint8) * 16
            tile = np.tile(bayer, (gray.shape[0] // 4 + 1, gray.shape[1] // 4 + 1))[:gray.shape[0], :gray.shape[1]]
            d = (gray > tile).astype(np.uint8) * 255
            out = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)
            out[:, :, 1] = d
            out[:, :, 0] = d // 8
            return cv2.resize(out, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)

        return frame.copy()

    def detect_micro_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.motion_blur > 1:
            k = self.motion_blur if self.motion_blur % 2 == 1 else self.motion_blur + 1
            gray = cv2.GaussianBlur(gray, (k, k), 0)

        if self.prev_motion_gray is None:
            self.prev_motion_gray = gray
            return []

        diff = cv2.absdiff(self.prev_motion_gray, gray)
        self.prev_motion_gray = gray

        _, mask = cv2.threshold(diff, self.motion_threshold, 255, cv2.THRESH_BINARY)

        # Keep this 1x1 on purpose. Bigger kernels erase the tiny UFO/pixel motion.
        kernel = np.ones((1, 1), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

        points = []
        total_area = 0
        for i in range(1, num_labels):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area >= self.motion_min_area:
                cx, cy = centroids[i]
                x = int(cx)
                y = int(cy)
                w = int(stats[i, cv2.CC_STAT_WIDTH])
                h = int(stats[i, cv2.CC_STAT_HEIGHT])
                left = int(stats[i, cv2.CC_STAT_LEFT])
                top = int(stats[i, cv2.CC_STAT_TOP])
                points.append({"x": x, "y": y, "area": area, "box": (left, top, w, h)})
                total_area += area

        if len(points) > self.motion_max_points:
            points = random.sample(points, self.motion_max_points)

        self.last_motion_count = len(points)
        self.last_motion_area = total_area
        now = time.time()
        for p in points:
            self.motion_history.append((p["x"], p["y"], p["area"], now))

        return points

    def draw_sigint_frame(self, img):
        h, w = img.shape[:2]
        col = self.overlay_color
        t = 1
        margin = 10
        # corner brackets
        cv2.line(img, (margin, margin), (margin + 55, margin), col, t)
        cv2.line(img, (margin, margin), (margin, margin + 55), col, t)
        cv2.line(img, (w - margin, margin), (w - margin - 55, margin), col, t)
        cv2.line(img, (w - margin, margin), (w - margin, margin + 55), col, t)
        cv2.line(img, (margin, h - margin), (margin + 55, h - margin), col, t)
        cv2.line(img, (margin, h - margin), (margin, h - margin - 55), col, t)
        cv2.line(img, (w - margin, h - margin), (w - margin - 55, h - margin), col, t)
        cv2.line(img, (w - margin, h - margin), (w - margin, h - margin - 55), col, t)

        # center reticle
        cx, cy = w // 2, h // 2
        cv2.line(img, (cx - 12, cy), (cx - 4, cy), col, 1)
        cv2.line(img, (cx + 4, cy), (cx + 12, cy), col, 1)
        cv2.line(img, (cx, cy - 12), (cx, cy - 4), col, 1)
        cv2.line(img, (cx, cy + 4), (cx, cy + 12), col, 1)
        cv2.circle(img, (cx, cy), 22, col, 1)

        if self.scanline_enabled:
            for y in range(0, h, 8):
                cv2.line(img, (0, y), (w, y), (0, 45, 20), 1)

        return img

    def draw_micro_motion(self, img, points):
        h, w = img.shape[:2]
        col = self.overlay_color
        now = time.time()

        # draw fading history first
        fresh_history = deque(maxlen=900)
        for x, y, area, ts in self.motion_history:
            age = now - ts
            if age <= self.motion_decay_seconds:
                fresh_history.append((x, y, area, ts))
                fade = max(0.15, 1.0 - age / self.motion_decay_seconds)
                radius = 1 if area <= 3 else 2
                trail_col = tuple(int(c * fade) for c in col)
                cv2.circle(img, (x, y), radius, trail_col, 1)
        self.motion_history = fresh_history

        # regional links only, no fake bottom/top stemming
        raw = [(p["x"], p["y"], p["area"]) for p in points]
        if len(raw) > 1:
            # keep link load sane
            sample = raw if len(raw) <= 90 else random.sample(raw, 90)
            for i in range(len(sample)):
                x1, y1, a1 = sample[i]
                nearest = []
                for j in range(i + 1, len(sample)):
                    x2, y2, a2 = sample[j]
                    dx = x2 - x1
                    dy = y2 - y1
                    d2 = dx * dx + dy * dy
                    if d2 <= self.motion_link_distance * self.motion_link_distance:
                        nearest.append((d2, x2, y2))
                nearest.sort(key=lambda q: q[0])
                for _, x2, y2 in nearest[:2]:
                    cv2.line(img, (x1, y1), (x2, y2), col, 1)

        for p in points:
            x, y, area = p["x"], p["y"], p["area"]
            left, top, bw, bh = p["box"]

            # Pixel-level points get tiny rings; bigger points get brackets.
            if area <= 3:
                cv2.circle(img, (x, y), 2, col, 1)
                cv2.circle(img, (x, y), 5, col, 1)
                label = "MICRO SIG"
            elif area <= 15:
                cv2.circle(img, (x, y), 3, col, 1)
                cv2.rectangle(img, (left - 2, top - 2), (left + bw + 2, top + bh + 2), col, 1)
                label = "SMALL VECTOR"
            else:
                cv2.rectangle(img, (left - 3, top - 3), (left + bw + 3, top + bh + 3), col, 1)
                label = "MOTION BODY"

            # avoid covering entire view with text when many micro points exist
            if len(points) <= 55 or random.random() < 0.18:
                cv2.putText(img, label, (min(w - 110, x + 5), max(12, y - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.32, col, 1, cv2.LINE_AA)

        return img


    def draw_radar(self, img, points):
        if not self.radar_enabled:
            return img

        h, w = img.shape[:2]
        col = self.overlay_color
        now = time.time()

        # Bottom-right radar placement, raised above the control panel zone in the camera frame.
        r = self.radar_radius
        cx = w - r - self.radar_margin
        cy = h - r - self.radar_margin - 8

        # Feed radar with current real motion points. Store normalized camera coordinates.
        for p in points:
            nx = (p["x"] / max(1, w)) * 2.0 - 1.0
            ny = (p["y"] / max(1, h)) * 2.0 - 1.0
            area = p.get("area", 1)
            self.radar_blips.append((nx, ny, area, now))

        overlay = img.copy()

        # Dark glass backing.
        cv2.circle(overlay, (cx, cy), r + 7, (0, 22, 10), -1)
        cv2.addWeighted(overlay, 0.28, img, 0.72, 0, img)

        # Range rings and cross axis.
        cv2.circle(img, (cx, cy), r, col, 1)
        cv2.circle(img, (cx, cy), int(r * 0.66), tuple(int(c * 0.65) for c in col), 1)
        cv2.circle(img, (cx, cy), int(r * 0.33), tuple(int(c * 0.45) for c in col), 1)
        cv2.line(img, (cx - r, cy), (cx + r, cy), tuple(int(c * 0.45) for c in col), 1)
        cv2.line(img, (cx, cy - r), (cx, cy + r), tuple(int(c * 0.45) for c in col), 1)

        # Sweep arm.
        self.radar_sweep_angle = (self.radar_sweep_angle + 4.0) % 360.0
        ang = math.radians(self.radar_sweep_angle)
        sx = int(cx + math.cos(ang) * r)
        sy = int(cy + math.sin(ang) * r)
        cv2.line(img, (cx, cy), (sx, sy), col, 1)

        # Fading wedge trail behind sweep.
        for back in range(1, 7):
            bang = math.radians(self.radar_sweep_angle - back * 7)
            ex = int(cx + math.cos(bang) * r)
            ey = int(cy + math.sin(bang) * r)
            fade = max(0.12, 0.42 - back * 0.045)
            cv2.line(img, (cx, cy), (ex, ey), tuple(int(c * fade) for c in col), 1)

        # Draw blips mapped from screen-space motion into radar-space.
        fresh = deque(maxlen=450)
        strongest = 0
        for nx, ny, area, ts in self.radar_blips:
            age = now - ts
            if age <= self.radar_decay_seconds:
                fresh.append((nx, ny, area, ts))
                fade = max(0.18, 1.0 - age / self.radar_decay_seconds)
                bx = int(cx + nx * r * 0.92)
                by = int(cy + ny * r * 0.92)
                if (bx - cx) * (bx - cx) + (by - cy) * (by - cy) <= r * r:
                    br = 2 if area <= 8 else 3
                    bcol = tuple(int(c * fade) for c in col)
                    cv2.circle(img, (bx, by), br, bcol, -1)
                    if area > 12:
                        cv2.circle(img, (bx, by), br + 3, bcol, 1)
                    strongest = max(strongest, int(area))
        self.radar_blips = fresh

        cv2.putText(img, "RADAR", (cx - r, cy - r - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, "RADAR", (cx - r, cy - r - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.40, col, 1, cv2.LINE_AA)
        cv2.putText(img, f"BLIPS {len(self.radar_blips)}", (cx - r, cy + r + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, f"BLIPS {len(self.radar_blips)}", (cx - r, cy + r + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1, cv2.LINE_AA)
        if strongest > 0:
            cv2.putText(img, f"SIG {strongest}", (cx + 12, cy + r + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, f"SIG {strongest}", (cx + 12, cy + r + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1, cv2.LINE_AA)

        return img

    def draw_hud_text(self, img):
        h, w = img.shape[:2]
        col = self.overlay_color

        self.fps_frames += 1
        now = time.time()
        if now - self.fps_clock >= 1.0:
            self.fps = self.fps_frames / (now - self.fps_clock)
            self.fps_frames = 0
            self.fps_clock = now

        mode = "UFO MICRO" if self.ufo_scan_enabled else "PASSIVE"
        lines = [
            "MINOS SIGINT // REALITY SCANNER",
            f"SCAN MODE: {mode}   RENDER: {self.render_mode}",
            f"THRESH: {self.motion_threshold}   MIN AREA: {self.motion_min_area}px   POINTS: {self.last_motion_count}",
            f"TOTAL DELTA AREA: {self.last_motion_area}   FPS: {self.fps:.1f}",
        ]
        y = 28
        for line in lines:
            cv2.putText(img, line, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, line, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.43, col, 1, cv2.LINE_AA)
            y += 18

        if self.ufo_scan_enabled and self.motion_min_area <= 2:
            warning = "PIXEL-LEVEL ACTIVE: EXPECT DUST / SENSOR NOISE / DISTANT LIGHTS"
            cv2.putText(img, warning, (14, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, warning, (14, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.38, col, 1, cv2.LINE_AA)

        return img

    def update(self, _dt):
        with self.frame_lock:
            frame = None if self.frame is None else self.frame.copy()

        if frame is None:
            return

        # Work at camera resolution for detection, display after overlays.
        display = self.render_base(frame)

        points = []
        if self.ufo_scan_enabled:
            points = self.detect_micro_motion(frame)
            display = self.draw_micro_motion(display, points)
        else:
            self.prev_motion_gray = None
            self.last_motion_count = 0
            self.last_motion_area = 0

        display = self.draw_radar(display, points)
        display = self.draw_sigint_frame(display)
        display = self.draw_hud_text(display)

        # Convert BGR to RGB for Kivy texture
        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        rgb = cv2.flip(rgb, 0)
        texture = Texture.create(size=(rgb.shape[1], rgb.shape[0]), colorfmt="rgb")
        texture.blit_buffer(rgb.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
        self.image.texture = texture

        self.status.text = (
            f"MINOS SIGINT // UFO SCANNER  |  micro points: {self.last_motion_count}  "
            f"| threshold: {self.motion_threshold}  | min area: {self.motion_min_area}px"
        )

    def stop(self):
        self.running = False
        try:
            if self.capture is not None:
                self.capture.release()
        except Exception:
            pass


class MinosSigintUFOApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.root_widget = MinosSigintUFO()
        return self.root_widget

    def on_stop(self):
        try:
            self.root_widget.stop()
        except Exception:
            pass


if __name__ == "__main__":
    MinosSigintUFOApp().run()
