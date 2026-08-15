# AI Air Mouse 🖐️🖱️

An experimental computer vision project that turns real-time hand gestures captured via a webcam into virtual mouse controls (cursor movement, clicking, dragging, scrolling, etc.).

> **Note:** This project documents my hands-on learning curve and iterative testing process with OpenCV, MediaPipe Tasks, and OS-level input automation.

---

## 📁 Repository Structure

```text
.
├── models/
│   └── hand_landmarker.task   # MediaPipe Hand Landmarker task bundle
│
└── tests/
    ├── 1_VideoCapture.ipynb   # Step 1: Camera capture, frame flipping, and display loop
    ├── 2_HandTracking.ipynb   # Step 2: MediaPipe task setup and landmark extraction
    ├── 3_CursorMapping.ipynb  # Step 3: Coordinate projection and cursor tracking
    ├── 4_FullMapping.ipynb    # Step 4: Complete gesture mapping (clicks, drag, scroll)
    └── 5_Optimization.ipynb   # Step 5: Jitter reduction, ctypes input, and performance tuning

```

---

## 🧭 Learning Curve & Test Breakdown

* **`VideoCapture.ipynb`** — Setting up OpenCV video capture (`cv2.VideoCapture`), frame sizing, horizontal mirroring, and latency benchmarking.
* **`HandTracking.ipynb`** — Integrating the MediaPipe Tasks Python API (`vision.HandLandmarker`), configuring confidence thresholds, and landmark extraction.
* **`CursorMapping.ipynb`** — Mapping bounding box coordinate spaces to monitor resolutions using interpolation (`numpy.interp`) and applying initial smoothing algorithms.
* **`FullMapping.ipynb`** — Designing and testing gesture distance thresholds:
  * **Move Cursor:** Thumb + Index pinch
  * **Left Click / Double Click:** Index + Middle tap
  * **Drag & Drop:** Index + Middle hold with movement threshold
  * **Right Click:** Index + Ring tap
  * **Touchpad Scroll:** Thumb + Ring pinch with vertical displacement
  * **Middle Click:** Thumb + Pinky pinch
* **`Optimization.ipynb`** — Advanced stability and latency improvements:
  * Removing software pauses (`pyautogui.PAUSE = 0.0`)
  * Low-latency Windows OS cursor control via `ctypes` (`SetCursorPos`)
  * Jitter filtering using moving average buffers (`collections.deque`) and dynamic alpha smoothing
  * Grace-frame caching for fast-motion recovery
  * Headless/background testing without UI render overhead

---

## ⚙️ Requirements

* Python 3.9+
* OpenCV (`opencv-python`)
* MediaPipe (`mediapipe`)
* PyAutoGUI (`pyautogui`)
* NumPy (`numpy`)
