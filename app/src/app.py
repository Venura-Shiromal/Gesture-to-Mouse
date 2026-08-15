import time
import cv2

import src.config as cfg
from src.controller import MouseController
from src.gestures import GestureEngine
from src.tracker import HandTracker


class AirMouseApp:
    """Core application orchestrator managing the vision pipeline and gesture loop."""

    def __init__(self, show_gui: bool = False):
        self.show_gui = show_gui
        self.is_running = False
        self.is_paused = True

        self.current_display_frame = None
        self.latest_status = "Paused"

        self.tracker = HandTracker()
        self.controller = MouseController()
        self.engine = GestureEngine(self.controller)

    def run(self):
        self.is_running = True
        print("🎯 Air Mouse Engine started.")

        try:
            while self.is_running:
                success, frame = self.tracker.read_frame()
                if not success:
                    time.sleep(0.01)
                    continue

                h, w, _ = frame.shape

                # Flip horizontally for natural mirror behavior
                frame = cv2.flip(frame, 1)

                status_text = "Paused"
                if not self.is_paused:
                    hand = self.tracker.process_frame(frame)
                    status_text = self.engine.process(hand, w, h)

                self.latest_status = status_text

                # Visual overlays
                if getattr(cfg, "DRAW_BOUNDING_BOX", True):
                    cv2.rectangle(
                        frame,
                        (cfg.FRAME_MARGIN, cfg.FRAME_MARGIN),
                        (w - cfg.FRAME_MARGIN, h - cfg.FRAME_MARGIN),
                        (200, 200, 200),
                        1,
                    )

                if getattr(cfg, "DRAW_STATUS_TEXT", True):
                    cv2.putText(
                        frame,
                        f"{status_text}",
                        (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0) if "Tracking" in status_text else (0, 165, 255),
                        2,
                    )

                self.current_display_frame = frame

                if self.show_gui:
                    cv2.imshow("Air Mouse - Debug View", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break

        except KeyboardInterrupt:
            print("\nShutting down Air Mouse...")

        finally:
            self.cleanup()

    def pause(self):
        self.is_paused = True
        self.engine._handle_idle()

    def resume(self):
        self.is_paused = False

    def toggle_pause(self):
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    def stop(self):
        self.is_running = False

    def cleanup(self):
        self.tracker.release()
        if self.show_gui:
            cv2.destroyAllWindows()
        self.controller.mouse_up()
        print("✅ Air Mouse cleanly stopped.")