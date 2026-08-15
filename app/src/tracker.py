import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import src.config as cfg


class HandTracker:
    """Handles camera capture and MediaPipe Hand Landmark detection."""

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),        # Index
        (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
        (9, 13), (13, 14), (14, 15), (15, 16), # Ring
        (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
        (0, 17)                                 # Palm base
    ]

    def __init__(self):
        self.cap = None
        self.last_timestamp_ms = 0
        self.detector = None

        self.reinit_camera()
        self.reinit_detector()

    def reinit_camera(self):
        """Re-initializes the camera device and applies resolution and FPS."""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(cfg.CAMERA_INDEX, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, cfg.TARGET_FPS)

    def reinit_detector(self):
        """Initializes or re-configures MediaPipe detector."""
        if self.detector is not None:
            self.detector.close()

        base_options = python.BaseOptions(model_asset_path=cfg.MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=cfg.NO_OF_HANDS,
            min_hand_presence_confidence=cfg.PRESENCE_CONFIDENCE,
            min_hand_detection_confidence=cfg.HAND_CONFIDENCE,
            min_tracking_confidence=cfg.TRACKING_CONFIDENCE,
            running_mode=vision.RunningMode.VIDEO,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def read_frame(self):
        if self.cap and self.cap.isOpened():
            return self.cap.read()
        return False, None

    def process_frame(self, frame):
        """Runs MediaPipe detection and draws skeleton if enabled."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)
        if timestamp_ms <= self.last_timestamp_ms:
            timestamp_ms = self.last_timestamp_ms + 1
        self.last_timestamp_ms = timestamp_ms

        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        if result.hand_landmarks:
            hand_landmarks = result.hand_landmarks[0]
            if getattr(cfg, "DRAW_SKELETON", True):
                self.draw_skeleton(frame, hand_landmarks)
            return hand_landmarks

        return None

    def draw_skeleton(self, frame, landmarks):
        h, w, _ = frame.shape
        points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
        for start_idx, end_idx in self.HAND_CONNECTIONS:
            cv2.line(frame, points[start_idx], points[end_idx], (0, 255, 180), 2)
        for pt in points:
            cv2.circle(frame, pt, 4, (0, 100, 255), -1)

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        if self.detector:
            self.detector.close()

    def probe_supported_modes(self):
        """Safely probes the currently active camera handle without opening a conflicting stream."""
        if not self.cap or not self.cap.isOpened():
            return ["640x480 (Default)"], 60

        candidates = [
            (320, 240),
            (640, 480),
            (800, 600),
            (1280, 720),
            (1600, 896),
            (1920, 1080),
            (2560, 1440),
        ]

        supported_resolutions = []
        original_w = cfg.FRAME_WIDTH
        original_h = cfg.FRAME_HEIGHT
        original_fps = cfg.TARGET_FPS

        # Probe candidate resolutions on active device handle
        for w, h in candidates:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            res_str = f"{actual_w}x{actual_h}"
            if (actual_w, actual_h) == (w, h) and res_str not in supported_resolutions:
                supported_resolutions.append(res_str)

        # Restore original active stream configuration
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, original_w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, original_h)
        self.cap.set(cv2.CAP_PROP_FPS, original_fps)

        if not supported_resolutions:
            supported_resolutions = [f"{original_w}x{original_h}"]

        return supported_resolutions, 60