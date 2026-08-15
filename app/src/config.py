import os
import sys
import pyautogui

pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works in dev (relative to project root) and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.normpath(os.path.join(base_path, relative_path))

# ==================== PATHS ==================== #
# ==================== PATHS ==================== #
MODEL_PATH = get_resource_path(os.path.join("assets", "hand_landmarker.task"))

ICON_PATH = get_resource_path(os.path.join("assets", "icon.ico"))
LOGO_ICON_PATH = get_resource_path(os.path.join("assets", "logo.png"))
PLAY_ICON_PATH = get_resource_path(os.path.join("assets", "play.png"))
PAUSE_ICON_PATH = get_resource_path(os.path.join("assets", "pause.png"))
SETTINGS_ICON_PATH = get_resource_path(os.path.join("assets", "settings.png"))
CAMERA_ON_ICON_PATH = get_resource_path(os.path.join("assets", "camera_on.png"))
CAMERA_OFF_ICON_PATH = get_resource_path(os.path.join("assets", "camera_off.png"))

# ==================== GUI / VISUAL OVERLAYS ==================== #
SHOW_CAMERA_VIEW = True
DRAW_SKELETON = True
DRAW_BOUNDING_BOX = True
DRAW_STATUS_TEXT = True
# ==================== CAMERA SETTINGS ==================== #
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 60

# ==================== GUI / VISUAL OVERLAYS ==================== #
SHOW_CAMERA_VIEW = True
DRAW_SKELETON = True
DRAW_BOUNDING_BOX = True
DRAW_STATUS_TEXT = True

# ==================== MODEL SETTINGS ==================== #
NO_OF_HANDS = 1
PRESENCE_CONFIDENCE = 0.6
HAND_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.6
MAX_GRACE_FRAMES = 2

# ==================== GESTURE DISTANCES (PIXELS) ==================== #
PINCH_DIST_MAX = 35          # Thumb <-> Index (Move Cursor)
CLICK_DIST_MAX = 40          # Index <-> Middle (Left Click / Drag)
RIGHT_CLICK_DIST_MAX = 45    # Index <-> Ring (Right Click)
SCROLL_PINCH_DIST_MAX = 35   # Thumb <-> Ring (Scroll Mode)
MIDDLE_CLICK_DIST_MAX = 35   # Thumb <-> Pinky (Middle Click)

# ==================== MOUSE CALIBRATION ==================== #
FRAME_MARGIN = 90            # Active bounding box margin
DOUBLE_CLICK_TIME = 0.65     # Max seconds between taps for double click
DRAG_MOVE_THRESHOLD = 15     # Pixels of hand movement while touching to start dragging
SCROLL_SPEED = 40            # Multiplier for scroll speed
SCROLL_DEADZONE = 4          # Pixels of vertical hand shift before scroll fires
JITTER_DEADZONE = 8          # Pixels of hand movement before cursor moves
MOVE_DEADZONE = 3.0          # Deadzone for resting hand jitter
BUFFER_SIZE = 5              # Moving average buffer window length

# ==================== SYSTEM ==================== #
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()