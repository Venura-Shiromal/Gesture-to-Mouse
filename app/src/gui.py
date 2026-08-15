import os
import threading
import customtkinter as ctk
import cv2
import src.config as cfg
from src.app import AirMouseApp
from PIL import Image

# Global in-memory cache for camera modes so we don't freeze the UI on reopening
CAMERA_MODES_CACHE = {}


class SettingsWindow(ctk.CTkToplevel):
    """Lag-free Settings window with staged draft variables and an Apply button."""

    def __init__(self, parent, app: AirMouseApp):
        super().__init__(parent)
        self.app = app
        self.title("Preferences & Calibration")
        self.geometry("640x720")
        self.minsize(580, 560)

        self.lift()
        self.focus_force()

        # ---------------- 1. Initialize Local Draft State ---------------- #
        self.draft = {
            # Camera
            "CAMERA_INDEX": cfg.CAMERA_INDEX,
            "FRAME_WIDTH": cfg.FRAME_WIDTH,
            "FRAME_HEIGHT": cfg.FRAME_HEIGHT,
            "TARGET_FPS": cfg.TARGET_FPS,
            # Visuals
            "DRAW_SKELETON": cfg.DRAW_SKELETON,
            "DRAW_BOUNDING_BOX": cfg.DRAW_BOUNDING_BOX,
            "DRAW_STATUS_TEXT": cfg.DRAW_STATUS_TEXT,
            # Model
            "HAND_CONFIDENCE": cfg.HAND_CONFIDENCE,
            "PRESENCE_CONFIDENCE": cfg.PRESENCE_CONFIDENCE,
            "TRACKING_CONFIDENCE": cfg.TRACKING_CONFIDENCE,
            "MAX_GRACE_FRAMES": cfg.MAX_GRACE_FRAMES,
            # Gestures
            "PINCH_DIST_MAX": cfg.PINCH_DIST_MAX,
            "CLICK_DIST_MAX": cfg.CLICK_DIST_MAX,
            "RIGHT_CLICK_DIST_MAX": cfg.RIGHT_CLICK_DIST_MAX,
            "SCROLL_PINCH_DIST_MAX": cfg.SCROLL_PINCH_DIST_MAX,
            "MIDDLE_CLICK_DIST_MAX": cfg.MIDDLE_CLICK_DIST_MAX,
            # Timing & Physics
            "FRAME_MARGIN": cfg.FRAME_MARGIN,
            "DOUBLE_CLICK_TIME": cfg.DOUBLE_CLICK_TIME,
            "DRAG_MOVE_THRESHOLD": cfg.DRAG_MOVE_THRESHOLD,
            "MOVE_DEADZONE": cfg.MOVE_DEADZONE,
            "SCROLL_SPEED": cfg.SCROLL_SPEED,
            "BUFFER_SIZE": cfg.BUFFER_SIZE,
        }

        # ---------------- 2. Layout Structure ---------------- #
        # Top Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(15, 10))

        self.tab_camera = self.tabview.add("Camera")
        self.tab_visuals = self.tabview.add("Visuals")
        self.tab_model = self.tabview.add("Model")
        self.tab_gestures = self.tabview.add("Gestures")
        self.tab_physics = self.tabview.add("Timing & Physics")

        # Bottom Action Bar (Apply / Close)
        self._build_action_bar()

        # Build Tab Content
        self._build_camera_tab()
        self._build_visuals_tab()
        self._build_model_tab()
        self._build_gestures_tab()
        self._build_physics_tab()

    def _build_action_bar(self):
        """Fixed bottom bar with feedback text, Apply, and Cancel buttons."""
        self.bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bar_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.lbl_apply_status = ctk.CTkLabel(
            self.bar_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#28a745",
        )
        self.lbl_apply_status.pack(side="left", padx=10)

        # Cancel / Close Button
        self.btn_cancel = ctk.CTkButton(
            self.bar_frame,
            text="Close",
            width=90,
            height=34,
            fg_color="#3a3a3a",
            hover_color="#4f4f4f",
            command=self.destroy,
        )
        self.btn_cancel.pack(side="right", padx=(8, 0))

        # Apply Changes Button
        self.btn_apply = ctk.CTkButton(
            self.bar_frame,
            text="Apply Changes",
            width=120,
            height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.apply_all_changes,
        )
        self.btn_apply.pack(side="right")

    # ---------------- 1. Camera Tab (Fast / Non-blocking) ---------------- #
    def _build_camera_tab(self):
        tab = self.tab_camera

        lbl_cam_idx = ctk.CTkLabel(tab, text="Camera Device", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_cam_idx.pack(anchor="w", padx=20, pady=(15, 2))

        self.opt_camera = ctk.CTkOptionMenu(
            tab,
            values=["Camera 0", "Camera 1", "Camera 2"],
            command=self._on_draft_camera_idx,
        )
        self.opt_camera.set(f"Camera {self.draft['CAMERA_INDEX']}")
        self.opt_camera.pack(fill="x", padx=20, pady=(0, 15))

        lbl_res = ctk.CTkLabel(tab, text="Hardware Supported Resolutions", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_res.pack(anchor="w", padx=20, pady=(5, 2))

        self.opt_res = ctk.CTkOptionMenu(
            tab,
            values=["640x480 (Default)", "1280x720", "1920x1080"],
            command=self._on_draft_resolution,
        )
        current_res = f"{self.draft['FRAME_WIDTH']}x{self.draft['FRAME_HEIGHT']}"
        self.opt_res.set(current_res)
        self.opt_res.pack(fill="x", padx=20, pady=(0, 15))

        self.lbl_fps, self.sld_fps = self._create_slider(
            tab,
            "Target FPS",
            self.draft["TARGET_FPS"],
            15,
            60,
            9,
            lambda v: self._update_draft("TARGET_FPS", int(v), self.lbl_fps, "Target FPS"),
        )

        # Probe hardware in a background thread to prevent opening stutter
        self._async_probe_camera_modes(self.draft["CAMERA_INDEX"])

    def _async_probe_camera_modes(self, cam_idx: int):
        """Asynchronously probes camera hardware without conflicting with the active video stream."""
        if cam_idx in CAMERA_MODES_CACHE:
            self._update_res_dropdown(CAMERA_MODES_CACHE[cam_idx])
            return

        def worker():
            modes, max_fps = self.app.tracker.probe_supported_modes()
            CAMERA_MODES_CACHE[cam_idx] = (modes, max_fps)
            self.after(0, lambda: self._update_res_dropdown((modes, max_fps)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_res_dropdown(self, data):
        if not self.winfo_exists() or not self.opt_res.winfo_exists():
            return

        modes, max_fps = data
        self.opt_res.configure(values=modes)
        current_res = f"{self.draft['FRAME_WIDTH']}x{self.draft['FRAME_HEIGHT']}"
        if current_res in modes:
            self.opt_res.set(current_res)
        elif modes:
            self.opt_res.set(modes[0])
            self._on_draft_resolution(modes[0])

    def _on_draft_camera_idx(self, choice: str):
        idx = int(choice.split()[-1])
        self.draft["CAMERA_INDEX"] = idx
        self._async_probe_camera_modes(idx)

    def _on_draft_resolution(self, choice: str):
        res_str = choice.split()[0]
        w, h = map(int, res_str.split("x"))
        self.draft["FRAME_WIDTH"] = w
        self.draft["FRAME_HEIGHT"] = h

    # ---------------- 2. Visuals Tab ---------------- #
    def _build_visuals_tab(self):
        tab = self.tab_visuals

        self.sw_skeleton = ctk.CTkSwitch(
            tab,
            text="Draw Hand Skeleton & Joints",
            command=lambda: self.draft.update({"DRAW_SKELETON": self.sw_skeleton.get() == 1}),
        )
        if self.draft["DRAW_SKELETON"]:
            self.sw_skeleton.select()
        self.sw_skeleton.pack(anchor="w", padx=20, pady=15)

        self.sw_box = ctk.CTkSwitch(
            tab,
            text="Draw Active Boundary Box",
            command=lambda: self.draft.update({"DRAW_BOUNDING_BOX": self.sw_box.get() == 1}),
        )
        if self.draft["DRAW_BOUNDING_BOX"]:
            self.sw_box.select()
        self.sw_box.pack(anchor="w", padx=20, pady=15)

        self.sw_status = ctk.CTkSwitch(
            tab,
            text="Draw On-Screen Status Label",
            command=lambda: self.draft.update({"DRAW_STATUS_TEXT": self.sw_status.get() == 1}),
        )
        if self.draft["DRAW_STATUS_TEXT"]:
            self.sw_status.select()
        self.sw_status.pack(anchor="w", padx=20, pady=15)

    # ---------------- 3. Model Tab ---------------- #
    def _build_model_tab(self):
        tab = self.tab_model

        self.lbl_hand_conf, _ = self._create_slider(
            tab, "Hand Detection Confidence", self.draft["HAND_CONFIDENCE"], 0.1, 1.0, 18,
            lambda v: self._update_draft("HAND_CONFIDENCE", round(v, 2), self.lbl_hand_conf, "Hand Detection Confidence")
        )

        self.lbl_pres_conf, _ = self._create_slider(
            tab, "Presence Confidence", self.draft["PRESENCE_CONFIDENCE"], 0.1, 1.0, 18,
            lambda v: self._update_draft("PRESENCE_CONFIDENCE", round(v, 2), self.lbl_pres_conf, "Presence Confidence")
        )

        self.lbl_trk_conf, _ = self._create_slider(
            tab, "Tracking Confidence", self.draft["TRACKING_CONFIDENCE"], 0.1, 1.0, 18,
            lambda v: self._update_draft("TRACKING_CONFIDENCE", round(v, 2), self.lbl_trk_conf, "Tracking Confidence")
        )

        self.lbl_grace, _ = self._create_slider(
            tab, "Max Grace Frames (Blur Recovery)", self.draft["MAX_GRACE_FRAMES"], 0, 10, 10,
            lambda v: self._update_draft("MAX_GRACE_FRAMES", int(v), self.lbl_grace, "Max Grace Frames")
        )

    # ---------------- 4. Gestures Tab ---------------- #
    def _build_gestures_tab(self):
        tab = self.tab_gestures

        self.lbl_pinch, _ = self._create_slider(
            tab, "Move Cursor (Thumb <-> Index Dist)", self.draft["PINCH_DIST_MAX"], 15, 70, 55,
            lambda v: self._update_draft("PINCH_DIST_MAX", int(v), self.lbl_pinch, "Move Cursor")
        )

        self.lbl_click, _ = self._create_slider(
            tab, "Left Click (Index <-> Middle Dist)", self.draft["CLICK_DIST_MAX"], 15, 80, 65,
            lambda v: self._update_draft("CLICK_DIST_MAX", int(v), self.lbl_click, "Left Click")
        )

        self.lbl_rclick, _ = self._create_slider(
            tab, "Right Click (Index <-> Ring Dist)", self.draft["RIGHT_CLICK_DIST_MAX"], 20, 90, 70,
            lambda v: self._update_draft("RIGHT_CLICK_DIST_MAX", int(v), self.lbl_rclick, "Right Click")
        )

        self.lbl_spincher, _ = self._create_slider(
            tab, "Scroll Mode (Thumb <-> Ring Dist)", self.draft["SCROLL_PINCH_DIST_MAX"], 15, 70, 55,
            lambda v: self._update_draft("SCROLL_PINCH_DIST_MAX", int(v), self.lbl_spincher, "Scroll Mode")
        )

        self.lbl_mclick, _ = self._create_slider(
            tab, "Middle Click (Thumb <-> Pinky Dist)", self.draft["MIDDLE_CLICK_DIST_MAX"], 15, 70, 55,
            lambda v: self._update_draft("MIDDLE_CLICK_DIST_MAX", int(v), self.lbl_mclick, "Middle Click")
        )

    # ---------------- 5. Timing & Physics Tab ---------------- #
    def _build_physics_tab(self):
        tab = self.tab_physics

        self.lbl_margin, _ = self._create_slider(
            tab, "Boundary Margin (px)", self.draft["FRAME_MARGIN"], 20, 180, 32,
            lambda v: self._update_draft("FRAME_MARGIN", int(v), self.lbl_margin, "Boundary Margin (px)")
        )

        self.lbl_dbl, _ = self._create_slider(
            tab, "Double Click Window (s)", self.draft["DOUBLE_CLICK_TIME"], 0.2, 1.2, 20,
            lambda v: self._update_draft("DOUBLE_CLICK_TIME", round(v, 2), self.lbl_dbl, "Double Click Window (s)")
        )

        self.lbl_drag, _ = self._create_slider(
            tab, "Drag Threshold (px movement)", self.draft["DRAG_MOVE_THRESHOLD"], 5, 50, 45,
            lambda v: self._update_draft("DRAG_MOVE_THRESHOLD", int(v), self.lbl_drag, "Drag Threshold (px)")
        )

        self.lbl_deadzone, _ = self._create_slider(
            tab, "Cursor Jitter Deadzone (px)", self.draft["MOVE_DEADZONE"], 0.5, 10.0, 19,
            lambda v: self._update_draft("MOVE_DEADZONE", round(v, 1), self.lbl_deadzone, "Cursor Jitter Deadzone (px)")
        )

        self.lbl_scroll_speed, _ = self._create_slider(
            tab, "Scroll Speed Multiplier", self.draft["SCROLL_SPEED"], 5, 80, 75,
            lambda v: self._update_draft("SCROLL_SPEED", int(v), self.lbl_scroll_speed, "Scroll Speed Multiplier")
        )

        self.lbl_buffer, _ = self._create_slider(
            tab, "Smoothing Buffer Size", self.draft["BUFFER_SIZE"], 1, 15, 14,
            lambda v: self._update_draft("BUFFER_SIZE", int(v), self.lbl_buffer, "Smoothing Buffer Size")
        )

    # ---------------- Helpers & Apply Engine ---------------- #
    def _create_slider(self, parent, label_text, current_val, min_v, max_v, steps, cmd):
        lbl = ctk.CTkLabel(parent, text=f"{label_text}: {current_val}", font=ctk.CTkFont(size=12))
        lbl.pack(anchor="w", padx=20, pady=(10, 2))
        sld = ctk.CTkSlider(parent, from_=min_v, to=max_v, number_of_steps=steps, command=cmd)
        sld.set(current_val)
        sld.pack(fill="x", padx=20, pady=(0, 10))
        return lbl, sld

    def _update_draft(self, key, val, label, title):
        self.draft[key] = val
        label.configure(text=f"{title}: {val}")

    def apply_all_changes(self):
        """Commits all staged drafts into live runtime config and triggers hot-reloads."""
        cam_changed = (
            cfg.CAMERA_INDEX != self.draft["CAMERA_INDEX"]
            or cfg.FRAME_WIDTH != self.draft["FRAME_WIDTH"]
            or cfg.FRAME_HEIGHT != self.draft["FRAME_HEIGHT"]
            or cfg.TARGET_FPS != self.draft["TARGET_FPS"]
        )

        model_changed = (
            cfg.HAND_CONFIDENCE != self.draft["HAND_CONFIDENCE"]
            or cfg.PRESENCE_CONFIDENCE != self.draft["PRESENCE_CONFIDENCE"]
            or cfg.TRACKING_CONFIDENCE != self.draft["TRACKING_CONFIDENCE"]
        )

        buffer_changed = cfg.BUFFER_SIZE != self.draft["BUFFER_SIZE"]

        # Commit all variables to config
        for k, v in self.draft.items():
            setattr(cfg, k, v)

        # Hot-reload sub-systems only when their respective options changed
        if cam_changed:
            self.app.tracker.reinit_camera()

        if model_changed:
            self.app.tracker.reinit_detector()

        if buffer_changed:
            self.app.controller.coord_buffer_x = type(self.app.controller.coord_buffer_x)(maxlen=cfg.BUFFER_SIZE)
            self.app.controller.coord_buffer_y = type(self.app.controller.coord_buffer_y)(maxlen=cfg.BUFFER_SIZE)

        # Show feedback
        self.lbl_apply_status.configure(text="✓ Changes Applied!")
        self.after(2500, lambda: self.lbl_apply_status.configure(text=""))

class AirMouseGUI(ctk.CTk):
    """Main studio dashboard with robust state management and fallback-safe action buttons."""

    def __init__(self, app: AirMouseApp):
        super().__init__()
        self.app = app
        self.settings_window = None
        self._current_ctk_img = None

        self.title("AI Air Mouse")
        self.geometry("580x540")
        self.minsize(500, 480)

        self._load_icons()
        self._build_top_bar()
        self._build_camera_view()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_video_feed()

    def _load_icons(self):
        """Loads PNG assets into CTkImage with strict error handling."""
        def safe_load(path_attr, size=(24, 24)):
            if hasattr(cfg, path_attr):
                path = getattr(cfg, path_attr)
                if path and os.path.exists(path):
                    try:
                        pil_img = Image.open(path)
                        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                    except Exception:
                        pass
            return None

        self.icon_logo = safe_load("LOGO_ICON_PATH", size=(24, 24))
        self.icon_play = safe_load("PLAY_ICON_PATH", size=(24, 24))
        self.icon_pause = safe_load("PAUSE_ICON_PATH", size=(24, 24))
        self.icon_settings = safe_load("SETTINGS_ICON_PATH", size=(24, 24))
        self.icon_cam_on = safe_load("CAMERA_ON_ICON_PATH", size=(24, 24))
        self.icon_cam_off = safe_load("CAMERA_OFF_ICON_PATH", size=(24, 24))

    def _build_top_bar(self):
        """Header with logo on left and three action buttons on right."""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(14, 6))

        # Title / Branding
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_container.pack(side="left")

        if self.icon_logo:
            self.logo_label = ctk.CTkLabel(self.title_container, text="", image=self.icon_logo)
            self.logo_label.pack(side="left", padx=(0, 8))

        self.title_label = ctk.CTkLabel(
            self.title_container,
            text="AI Air Mouse",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.pack(side="left")

        # Action Buttons Container
        self.actions_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.actions_frame.pack(side="right")

        # 1. Camera Toggle Button
        cam_text = "" if self.icon_cam_off else "🚫"
        self.btn_cam_toggle = ctk.CTkButton(
            self.actions_frame,
            text=cam_text,
            image=self.icon_cam_off,
            width=36,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color="#333333",
            command=self.toggle_camera_view,
        )
        self.btn_cam_toggle.pack(side="left", padx=(0, 4))

        # 2. Play / Pause Button (Starts in Paused State)
        play_text = "" if self.icon_play else "▶"
        self.btn_toggle = ctk.CTkButton(
            self.actions_frame,
            text=play_text,
            image=self.icon_play,
            width=40,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="transparent",
            hover_color="#333333",
            command=self.toggle_tracking,
        )
        self.btn_toggle.pack(side="left", padx=(0, 4))

        # 3. Settings Button
        settings_text = "" if self.icon_settings else "⚙"
        self.btn_settings = ctk.CTkButton(
            self.actions_frame,
            text=settings_text,
            image=self.icon_settings,
            width=36,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color="#333333",
            command=self.open_settings,
        )
        self.btn_settings.pack(side="left")

    def _build_camera_view(self):
        """Constructs preview card with separate labels for video and standby."""
        self.video_frame = ctk.CTkFrame(self, corner_radius=12)
        self.video_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Container for video / placeholder
        self.display_container = ctk.CTkFrame(self.video_frame, fg_color="transparent")
        self.display_container.pack(expand=True, fill="both", padx=12, pady=(12, 6))

        # Live Video Label
        self.video_label = ctk.CTkLabel(self.display_container, text="")
        self.video_label.pack(expand=True, fill="both")

        # Hidden Standby Label (shown only when camera preview is disabled)
        self.standby_label = ctk.CTkLabel(
            self.display_container,
            text="⚡ Vision Feed Hidden\n\n(Tracking Active in High-Performance Mode)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#888888",
        )

        # Status Badge
        self.status_badge = ctk.CTkLabel(
            self.video_frame,
            text="Status: Paused",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6c757d",
            corner_radius=8,
            height=30,
        )
        self.status_badge.pack(fill="x", padx=12, pady=(0, 12))

    def toggle_camera_view(self):
        """Swaps UI preview without breaking CustomTkinter image handlers."""
        cfg.SHOW_CAMERA_VIEW = not cfg.SHOW_CAMERA_VIEW
        if cfg.SHOW_CAMERA_VIEW:
            self.btn_cam_toggle.configure(
                image=self.icon_cam_off,
                text="" if self.icon_cam_off else "🚫",
                fg_color="transparent",
            )
            self.standby_label.pack_forget()
            self.video_label.pack(expand=True, fill="both")
        else:
            self.btn_cam_toggle.configure(
                image=self.icon_cam_on,
                text="" if self.icon_cam_on else "📷",
                fg_color="transparent",
            )
            self.video_label.pack_forget()
            self.standby_label.pack(expand=True, fill="both")

    def toggle_tracking(self):
        self.app.toggle_pause()
        if self.app.is_paused:
            self.btn_toggle.configure(
                image=self.icon_play,
                text="" if self.icon_play else "▶",
                fg_color="transparent",
                hover_color="#333333",
            )
            self.status_badge.configure(text="Status: Paused", fg_color="#6c757d")
        else:
            self.btn_toggle.configure(
                image=self.icon_pause,
                text="" if self.icon_pause else "⏸",
                fg_color="transparent",
                hover_color="#333333",
            )
            self.status_badge.configure(text="Status: Active", fg_color="#1f538d")

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self, self.app)
        else:
            self.settings_window.lift()
            self.settings_window.focus_force()

    def update_video_feed(self):
        """Fetches and renders latest frame into CTkImage."""
        if cfg.SHOW_CAMERA_VIEW:
            if hasattr(self.app, "current_display_frame") and self.app.current_display_frame is not None:
                frame = self.app.current_display_frame.copy()
                h, w, _ = frame.shape
                target_w = 480
                target_h = int(h * (target_w / w))
                resized = cv2.resize(frame, (target_w, target_h))

                rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_img)

                # Use CTkImage to prevent Tk photo garbage collection issues
                self._current_ctk_img = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(target_w, target_h)
                )
                self.video_label.configure(image=self._current_ctk_img)

        # Update real-time status badge
        if not self.app.is_paused and hasattr(self.app, "latest_status"):
            current_status = self.app.latest_status
            badge_color = "#28a745" if "Tracking" in current_status else "#17a2b8"
            if "CLICK" in current_status or "DRAGGING" in current_status:
                badge_color = "#e0a800"
            self.status_badge.configure(text=f"Status: {current_status}", fg_color=badge_color)

        self.after(33, self.update_video_feed)

    def on_close(self):
        self.app.stop()
        self.destroy()