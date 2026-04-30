"""
Main application file for the Vision-Controlled Bionic Hand.

This script initializes the camera, MediaPipe hand landmark detection,
serial communication, and runs the main state machine loop for controlling
the bionic hand.

Controls:
    'r': Start/Stop the hand recognition process.
    'q': Quit the application.
"""

import queue
import time
from enum import Enum, auto

from src.models import HandState
from src.gesture import GestureRecognizer
from src.mouse_logic import MouseController
from src.bt_server import BTDevice
from dbus.mainloop.glib import DBusGMainLoop
from src.serial_com import SerialManager
# --- Application State Machine ---
class State(Enum):
    """Defines the operational states of the application."""

    RUNNING = auto()
    WAITING = auto()

def main():
    """
    Main function to run the hand tracking and control application.
    """

    # 1. Configurations
    logic_queue = queue.Queue(maxsize=1)
    vis_queue = queue.Queue(maxsize=1)

    # 2. Initialize bluetooth and serial port
    DBusGMainLoop(set_as_default=True)
    bt_device = BTDevice()
    print("Please search and connect bluetooth device on PC...")
    bt_device.listen() 
    sm = SerialManager()
    is_running = True
    last_serial_time = 0

    # 3. Run recognition thread
    recognizer = GestureRecognizer(
        logic_queue=logic_queue, 
        vis_queue=vis_queue,
    )
    recognizer.start()

    # 4. Run mouse controller thread
    mouse_logic = MouseController(sensitivity=1800, smoothing=0.4)
    last_buttons = 0 
    print("Start to transfer gesture data...")
    try:
        while True:
            cmd = sm.read_command()
            if cmd == "START":
                is_running = True
                print("Received STM32 Command: Start running...")
            elif cmd == "STOP":
                is_running = False
                print("Received STM32 Command: Stop running...")

            try:
                state = logic_queue.get(timeout=0.1)
            except queue.Empty:
                state = HandState(is_detected=False)

            dx, dy = 0, 0
            if is_running:

                dx, dy, click_event = mouse_logic.process(state)
                buttons = 0x01 if mouse_logic.confirmed_clicking else 0x00

                dx_clamped = max(min(int(dx), 127), -127)
                dy_clamped = max(min(int(dy), 127), -127)
                
                if dx_clamped != 0 or dy_clamped != 0 or buttons != last_buttons:
                    bt_device.send_mouse(buttons, [dx_clamped & 0xFF, dy_clamped & 0xFF, 0])
                    last_buttons = buttons

            now = time.time()
            if now - last_serial_time > 0.05:
                direction = mouse_logic.get_direction_index(dx, dy)
                sm.send_packet(
                    is_running, 
                    state.is_detected, 
                    direction, 
                    mouse_logic.confirmed_clicking,
                    state.fps, 
                    state.latency_ms
                )
                last_serial_time = now
            debug_info = (
                f"Raw: {state.pinch_distance:.4f} | "
                f"Smooth: {mouse_logic.smoothed_dist:.4f} | "
                f"Status: {'[LOCKED]' if mouse_logic.confirmed_clicking else '  OPEN  '}"
            )
            print(f"\r{debug_info}", end="", flush=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        recognizer.stop()
        sm.close()
        bt_device.close()
        print("Cleanup finished.")


if __name__ == "__main__":
    main()