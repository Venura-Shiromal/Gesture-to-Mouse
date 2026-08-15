import math
import time
from src.config import (
    PINCH_DIST_MAX,
    CLICK_DIST_MAX,
    RIGHT_CLICK_DIST_MAX,
    SCROLL_PINCH_DIST_MAX,
    MIDDLE_CLICK_DIST_MAX,
    DOUBLE_CLICK_TIME,
    DRAG_MOVE_THRESHOLD,
)
from src.controller import MouseController


class GestureEngine:
    """Processes hand landmarks to recognize gestures and trigger mouse actions."""

    def __init__(self, controller: MouseController):
        self.controller = controller

        # Interaction state memory
        self.is_touching = False
        self.is_dragging = False
        self.is_right_clicked = False
        self.is_middle_clicked = False
        self.last_tap_time = 0.0
        self.tap_count = 0
        self.touch_start_frame_pos = (0, 0)

    def process(self, hand, frame_w: int, frame_h: int) -> str:
        """Evaluates hand landmarks, executes mouse actions, and returns status text."""
        current_time = time.time()
        status_text = "Idle"

        if hand is None:
            self._handle_idle()
            return status_text

        # Extract Landmark Coordinates
        # 4 = Thumb | 8 = Index | 12 = Middle | 16 = Ring | 20 = Pinky
        thumb_x, thumb_y = int(hand[4].x * frame_w), int(hand[4].y * frame_h)
        idx_x, idx_y = int(hand[8].x * frame_w), int(hand[8].y * frame_h)
        mid_x, mid_y = int(hand[12].x * frame_w), int(hand[12].y * frame_h)
        ring_x, ring_y = int(hand[16].x * frame_w), int(hand[16].y * frame_h)
        pinky_x, pinky_y = int(hand[20].x * frame_w), int(hand[20].y * frame_h)

        # Distance Calculations
        move_pinch_dist = math.hypot(thumb_x - idx_x, thumb_y - idx_y)
        scroll_pinch_dist = math.hypot(thumb_x - ring_x, thumb_y - ring_y)
        middle_click_dist = math.hypot(thumb_x - pinky_x, thumb_y - pinky_y)
        left_click_dist = math.hypot(idx_x - mid_x, idx_y - mid_y)
        right_click_dist = math.hypot(idx_x - ring_x, idx_y - ring_y)

        # ==================== 1. MIDDLE CLICK (Thumb + Pinky) ==================== #
        if middle_click_dist < MIDDLE_CLICK_DIST_MAX:
            if not self.is_middle_clicked:
                self.controller.middle_click()
                self.is_middle_clicked = True
            status_text = "MIDDLE CLICK"

        # ==================== 2. SCROLL MODE (Thumb + Ring) ==================== #
        elif scroll_pinch_dist < SCROLL_PINCH_DIST_MAX:
            self.is_middle_clicked = False
            status_text = "SCROLL MODE"

            self.controller.handle_scroll(thumb_y)

            if self.is_dragging:
                self.controller.mouse_up()
                self.is_dragging = False

        # ==================== 3. CURSOR & CLICKS (Thumb + Index) ==================== #
        elif move_pinch_dist < PINCH_DIST_MAX:
            self.is_middle_clicked = False
            self.controller.reset_scroll()
            status_text = "Tracking Cursor"

            # Check contact flags
            is_left_touching = left_click_dist < CLICK_DIST_MAX
            is_right_touching = right_click_dist < RIGHT_CLICK_DIST_MAX

            # --- Evaluate Left Touch / Drag State FIRST ---
            if is_left_touching:
                if not self.is_touching:
                    # Initial contact frame: record where the finger touched
                    self.is_touching = True
                    self.touch_start_frame_pos = (idx_x, idx_y)

                    if (current_time - self.last_tap_time) <= DOUBLE_CLICK_TIME:
                        self.controller.double_click()
                        self.tap_count = 0
                        self.last_tap_time = 0.0
                        status_text = "DOUBLE CLICK"
                    else:
                        self.tap_count = 1
                        self.last_tap_time = current_time
                else:
                    # Finger held together: Check physical movement in camera frame
                    hand_displacement = math.hypot(
                        idx_x - self.touch_start_frame_pos[0],
                        idx_y - self.touch_start_frame_pos[1]
                    )

                    # Trigger Drag Mode once hand moves past threshold
                    if not self.is_dragging and hand_displacement > DRAG_MOVE_THRESHOLD:
                        self.controller.mouse_down()
                        self.is_dragging = True
                        self.tap_count = 0  # Cancel pending single click

                    if self.is_dragging:
                        status_text = "DRAGGING"
            else:
                # Finger released: Drop if was dragging
                if self.is_dragging:
                    self.controller.mouse_up()
                    self.is_dragging = False
                    self.tap_count = 0
                self.is_touching = False

            # --- Move Cursor ---
            # Freeze cursor ONLY during a brief tap or right-click (NOT while dragging)
            should_freeze = is_right_touching or (is_left_touching and not self.is_dragging)

            self.controller.move_cursor(
                idx_x, idx_y, frame_w, frame_h, should_freeze=should_freeze
            )

            # --- Right Click (Index + Ring) ---
            if is_right_touching:
                if not self.is_right_clicked:
                    self.controller.right_click()
                    self.is_right_clicked = True
                status_text = "RIGHT CLICK"
            else:
                self.is_right_clicked = False

        # ==================== 4. IDLE ==================== #
        else:
            self._handle_idle()

        # Resolve Pending Single Click (if released without dragging)
        if self.tap_count == 1 and not self.is_dragging and (current_time - self.last_tap_time > DOUBLE_CLICK_TIME):
            self.controller.click()
            self.tap_count = 0
            status_text = "SINGLE CLICK"

        return status_text

    def _handle_idle(self):
        """Resets active states when hand is absent or outside interactive pinch postures."""
        self.controller.reset_buffers()
        self.is_middle_clicked = False
        self.is_right_clicked = False
        self.is_touching = False
        if self.is_dragging:
            self.controller.mouse_up()
            self.is_dragging = False