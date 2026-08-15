import ctypes
import math
from collections import deque
import numpy as np
import pyautogui

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FRAME_MARGIN,
    BUFFER_SIZE,
    MOVE_DEADZONE,
    SCROLL_SPEED,
    SCROLL_DEADZONE,
)

class MouseController:
    """Handles OS-level mouse movement, clicks, scrolling, and dragging."""

    def __init__(self):
        # Position memory
        self.prev_x = SCREEN_WIDTH // 2
        self.prev_y = SCREEN_HEIGHT // 2
        
        # Jitter reduction buffers
        self.coord_buffer_x = deque(maxlen=BUFFER_SIZE)
        self.coord_buffer_y = deque(maxlen=BUFFER_SIZE)
        
        # Scroll tracking memory
        self.prev_scroll_y = 0

    def move_cursor(self, raw_x: int, raw_y: int, frame_w: int, frame_h: int, should_freeze: bool = False):
        """Maps frame coordinates to screen coordinates and moves cursor via ctypes."""
        # 1. Project bounding-box coordinates to monitor dimensions
        mapped_x = np.interp(raw_x, (FRAME_MARGIN, frame_w - FRAME_MARGIN), (0, SCREEN_WIDTH))
        mapped_y = np.interp(raw_y, (FRAME_MARGIN, frame_h - FRAME_MARGIN), (0, SCREEN_HEIGHT))

        # 2. Moving average smoothing
        self.coord_buffer_x.append(mapped_x)
        self.coord_buffer_y.append(mapped_y)
        target_x = sum(self.coord_buffer_x) / len(self.coord_buffer_x)
        target_y = sum(self.coord_buffer_y) / len(self.coord_buffer_y)

        # 3. Calculate displacement
        travel_dist = math.hypot(target_x - self.prev_x, target_y - self.prev_y)

        # 4. Deadzone and freeze checks
        if should_freeze or travel_dist < MOVE_DEADZONE:
            curr_x, curr_y = self.prev_x, self.prev_y
        else:
            smooth_weight = 0.40 if travel_dist < 25 else 0.80
            curr_x = self.prev_x + smooth_weight * (target_x - self.prev_x)
            curr_y = self.prev_y + smooth_weight * (target_y - self.prev_y)

        # 5. Direct OS-level move
        ctypes.windll.user32.SetCursorPos(int(curr_x), int(curr_y))
        self.prev_x, self.prev_y = curr_x, curr_y

        return curr_x, curr_y, travel_dist

    def click(self):
        pyautogui.click()

    def double_click(self):
        pyautogui.doubleClick()

    def right_click(self):
        pyautogui.rightClick()

    def middle_click(self):
        pyautogui.middleClick()

    def mouse_down(self):
        pyautogui.mouseDown(button='left')

    def mouse_up(self):
        pyautogui.mouseUp(button='left')

    def handle_scroll(self, thumb_y: int):
        """Translates vertical finger delta into smooth scroll steps."""
        if self.prev_scroll_y == 0:
            self.prev_scroll_y = thumb_y
            return

        dy = self.prev_scroll_y - thumb_y
        if abs(dy) > SCROLL_DEADZONE:
            scroll_units = int(dy * (SCROLL_SPEED / 10))
            pyautogui.scroll(scroll_units)
            self.prev_scroll_y = thumb_y

    def reset_scroll(self):
        self.prev_scroll_y = 0

    def reset_buffers(self):
        """Clears smoothing history when hand tracking is lost/idle."""
        self.coord_buffer_x.clear()
        self.coord_buffer_y.clear()
        self.reset_scroll()