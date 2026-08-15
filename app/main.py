import threading
import sys
from src.app import AirMouseApp
from src.gui import AirMouseGUI


def main():
    # Initialize Core Engine
    app = AirMouseApp(show_gui=False)

    # Run the vision & gesture pipeline in a high-priority background worker thread
    engine_thread = threading.Thread(target=app.run, daemon=True)
    engine_thread.start()

    # Launch Modern GUI on the main thread
    gui = AirMouseGUI(app)
    gui.mainloop()

    # Ensure clean shutdown on exit
    app.stop()
    engine_thread.join(timeout=1.0)
    sys.exit(0)


if __name__ == "__main__":
    main()