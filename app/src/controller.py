import sys
import math
from collections import deque
import numpy as np
import pyautogui

if sys.platform == "win32":
    import ctypes

import src.config as cfg


class MouseController:
    """Handles OS-level mouse movement, clicks, scrolling, and dragging."""

    def __init__(self):
        # Position memory
        self.prev_x = cfg.SCREEN_WIDTH // 2
        self.prev_y = cfg.SCREEN_HEIGHT // 2

        # Jitter reduction buffers
        self.coord_buffer_x = deque(maxlen=cfg.BUFFER_SIZE)
        self.coord_buffer_y = deque(maxlen=cfg.BUFFER_SIZE)

        # Scroll tracking memory
        self.prev_scroll_y = 0

    def _set_os_cursor(self, x: int, y: int):
        """Dispatches cursor position directly to OS input layer."""
        if sys.platform == "win32":
            ctypes.windll.user32.SetCursorPos(int(x), int(y))
        else:
            pyautogui.moveTo(int(x), int(y), _pause=False)

    def move_cursor(self, raw_x: int, raw_y: int, frame_w: int, frame_h: int, should_freeze: bool = False):
        """Maps frame coordinates to screen coordinates and moves cursor smoothly."""
        # 1. Project bounding-box coordinates using dynamic config values
        margin = cfg.FRAME_MARGIN
        mapped_x = np.interp(raw_x, (margin, frame_w - margin), (0, cfg.SCREEN_WIDTH))
        mapped_y = np.interp(raw_y, (margin, frame_h - margin), (0, cfg.SCREEN_HEIGHT))

        # 2. Moving average smoothing
        self.coord_buffer_x.append(mapped_x)
        self.coord_buffer_y.append(mapped_y)
        target_x = sum(self.coord_buffer_x) / len(self.coord_buffer_x)
        target_y = sum(self.coord_buffer_y) / len(self.coord_buffer_y)

        # 3. Calculate displacement
        travel_dist = math.hypot(target_x - self.prev_x, target_y - self.prev_y)

        # 4. Deadzone and freeze checks
        if should_freeze or travel_dist < cfg.MOVE_DEADZONE:
            curr_x, curr_y = self.prev_x, self.prev_y
        else:
            smooth_weight = 0.40 if travel_dist < 25 else 0.80
            curr_x = self.prev_x + smooth_weight * (target_x - self.prev_x)
            curr_y = self.prev_y + smooth_weight * (target_y - self.prev_y)

        # 5. Clamp to screen boundaries and send to OS
        curr_x = max(0, min(cfg.SCREEN_WIDTH - 1, curr_x))
        curr_y = max(0, min(cfg.SCREEN_HEIGHT - 1, curr_y))

        self._set_os_cursor(curr_x, curr_y)
        self.prev_x, self.prev_y = curr_x, curr_y

        return curr_x, curr_y, travel_dist

    def click(self):
        pyautogui.click(_pause=False)

    def double_click(self):
        pyautogui.doubleClick(_pause=False)

    def right_click(self):
        pyautogui.rightClick(_pause=False)

    def middle_click(self):
        pyautogui.middleClick(_pause=False)

    def mouse_down(self):
        pyautogui.mouseDown(button='left', _pause=False)

    def mouse_up(self):
        pyautogui.mouseUp(button='left', _pause=False)

    def handle_scroll(self, thumb_y: int):
        """Translates vertical finger delta into smooth scroll steps."""
        if self.prev_scroll_y == 0:
            self.prev_scroll_y = thumb_y
            return

        dy = self.prev_scroll_y - thumb_y
        if abs(dy) > cfg.SCROLL_DEADZONE:
            scroll_units = int(dy * (cfg.SCROLL_SPEED / 10))
            pyautogui.scroll(scroll_units, _pause=False)
            self.prev_scroll_y = thumb_y

    def reset_scroll(self):
        self.prev_scroll_y = 0

    def reset_buffers(self):
        """Clears smoothing history when hand tracking is lost or idle."""
        self.coord_buffer_x.clear()
        self.coord_buffer_y.clear()
        self.reset_scroll()