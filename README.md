# AI Air Mouse 🖐️🖱️

An AI-powered computer vision desktop application that transforms real-time webcam hand gestures into fluid, low-latency virtual mouse controls (cursor tracking, left/right/double clicks, drag-and-drop, touchpad scrolling, and middle click).

Built with **OpenCV**, **MediaPipe Tasks**, and a modern **CustomTkinter** dashboard interface.

---

## ✨ Key Features

* **Modern Dark-Themed GUI Dashboard:** Clean CustomTkinter interface with live vision preview, dynamic real-time status badges, and icon controls.
* **Low-Latency Direct OS Control:** Direct Windows Win32 API cursor positioning via `ctypes` (`SetCursorPos`) bypassing software latency limits.
* **Jitter Smoothing & Deadzone Physics:** Moving-average coordinate buffers and velocity-based deadzones for steady, non-shaky cursor tracking.
* **State-Machine Gesture Engine:** Accurately distinguishes quick taps from sustained holds for flawless drag-and-drop and double-click handling.
* **Dynamic Hardware Prober & Calibration Suite:**
  * Background hardware scanning for camera-supported resolutions and FPS targets.
  * In-app preferences tab for model confidence, visual overlays, and gesture distances.
  * Non-blocking staged settings with an **Apply Changes** commitment workflow.
* **High-Performance Headless Mode:** Toggle camera preview off in the GUI to reduce CPU/GPU load while keeping hand tracking active.

---

## ✋ Gesture Control Guide

> **Note:** The **Thumb + Index pinch** acts as the master cursor engagement posture. Clicks and drag actions are triggered using other fingers *while* maintaining active cursor control.

| Action | Hand Posture | Description |
| :--- | :--- | :--- |
| **Move Cursor** | **Thumb + Index** Pinch | Pinch thumb and index tips together to activate cursor tracking and move across the screen. |
| **Left Click** | **Index + Middle** Tap | While tracking cursor, tap index and middle fingertips together once. |
| **Double Click** | **Index + Middle** Double Tap | While tracking cursor, tap index and middle fingertips together rapidly twice. |
| **Drag & Drop** | **Index + Middle** Hold + Move | While tracking cursor, hold index and middle fingers together and move past the drag threshold; separate fingers to drop. |
| **Right Click** | **Index + Ring** Tap | While tracking cursor, tap index and ring fingertips together. |
| **Scroll Mode** | **Thumb + Ring** Pinch | Pinch thumb and ring fingertips together and move your hand vertically up or down. |
| **Middle Click** | **Thumb + Pinky** Pinch | Pinch thumb and pinky fingertips together once. |

---

## 📁 Repository Structure

```text
.
├── models/
│   └── hand_landmarker.task   # MediaPipe Hand Landmarker task bundle
│
├── tests/
│   ├── 1_VideoCapture.ipynb   # Step 1: Camera capture, mirroring, and display loop
│   ├── 2_HandTracking.ipynb   # Step 2: MediaPipe task setup and landmark extraction
│   ├── 3_CursorMapping.ipynb  # Step 3: Coordinate interpolation and smoothing
│   ├── 4_FullMapping.ipynb    # Step 4: Gesture threshold state machine & actions
│   └── 5_Optimization.ipynb   # Step 5: Jitter reduction, ctypes input, and latency tuning
│
├── app/
│   ├── assets/                # App icons, UI graphics, and task models
│   ├── src/
│   │   ├── __init__.py
│   │   ├── app.py             # Main background tracking loop & state coordinator
│   │   ├── config.py          # Centralized configuration & resource paths
│   │   ├── controller.py      # Low-level OS input driver & smoothing buffers
│   │   ├── gestures.py        # Gesture recognition state machine
│   │   ├── gui.py             # CustomTkinter dashboard & preferences window
│   │   └── tracker.py         # MediaPipe inference & hardware capability probing
│   └── main.py                # Application entry point
│
├── .gitattributes
├── .gitignore
├── README.md
├── LICENSE
└── requirements.txt

```
---

## 🧭 Learning Curve & Test Breakdown

* **`1_VideoCapture.ipynb`** — OpenCV frame capture (`cv2.VideoCapture`), horizontal mirroring for natural hand interaction, and FPS measurement.
* **`2_HandTracking.ipynb`** — Integrating the MediaPipe Tasks Python API (`vision.HandLandmarker`), confidence tuning, and joint landmark extraction.
* **`3_CursorMapping.ipynb`** — Mapping bounding box coordinate spaces to monitor resolutions using interpolation (`numpy.interp`) and smoothing algorithms.
* **`4_FullMapping.ipynb`** — Designing and validating gesture distance thresholds and posture logic for click, drag, right-click, and scroll operations.
* **`5_Optimization.ipynb`** — Core performance engineering:
  * Eliminating framework pauses (`pyautogui.PAUSE = 0.0`).
  * Direct OS cursor manipulation via `ctypes.windll.user32.SetCursorPos`.
  * Moving-average smoothing buffers (`collections.deque`) with jitter deadzones.
  * Grace-frame caching for high-speed motion blur recovery.

---

## 🚀 Getting Started

### Prerequisites
* **OS:** Windows 10 / 11 (64-bit) *(Required for Win32 `ctypes` driver)*
* **Python:** 3.10 or 3.11 (64-bit)
* **Hardware:** Built-in or external USB webcam

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Venura-Shiromal/Gesture-to-Mouse.git](https://github.com/Venura-Shiromal/Gesture-to-Mouse.git)
   cd Gesture-to-Mouse
   ```

2. **Create and Activate Virtual Environments**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate.ps1
   ```
   
3. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```
   
4. **Launch the Application**
   ```bash
   python app/main.py
   ```

---

### Add a Standalone Pre-Built Binary Section *(For Non-Developers)*
Direct non-developer users straight to your GitHub Releases so they don't have to install Python.

## 📦 Download Standalone Executable (Windows x64)

Don't want to install Python? Download the pre-packaged release:

1. Grab the latest `AI-Air-Mouse-v1.0.0-Win64.zip` from the [Releases](https://github.com/Venura-Shiromal/Gesture-to-Mouse/releases) page.
2. Extract the archive.
3. Run `AI-Air-Mouse.exe`.
