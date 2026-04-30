---

# PiGesture-HID 🖱️✨

A high-performance, gesture-controlled intelligent peripheral that transforms hand movements into real-time mouse actions via Computer Vision and Bluetooth HID.

Built with **Raspberry Pi 5** for AI processing and **STM32 F446RE** for interactive feedback and system control.

## 📺 Project Overview
This project uses MediaPipe on a Raspberry Pi 5 to track hand landmarks, translates them into mouse movements (relative positioning, smoothing, and acceleration), and emulates a standard Bluetooth HID mouse. An STM32-powered OLED dashboard provides real-time telemetry (FPS, Latency, Directions) and physical control via buttons.


https://github.com/user-attachments/assets/c1ed6b2b-64f0-486d-948e-6f0801126c16


https://github.com/user-attachments/assets/20edd4bf-9211-4ed7-b41f-8eb7356fcad4


### Key Features
- **Vision-Powered Control**: Accurate hand tracking using MediaPipe Hands.
- **Bluetooth HID Emulation**: The RPi 5 acts as a native Bluetooth mouse compatible with PC/Mac.
- **OLED Dashboard**: Real-time display of system status, mouse actions, and performance metrics.
- **Low Latency Architecture**: Multi-threaded Python core + STM32 DMA Serial processing achieving ~30ms latency.
- **Physical Interaction**: STM32-based hardware interrupts for system start/stop/pause.

---

##  System Architecture

### 1. Raspberry Pi 5 (The Brain)
- **Visual Engine**: `Picamera2` + `MediaPipe` (Live Stream Mode).
- **Logic Engine**: 
    - **Smoothing**: Exponential Moving Average (EMA) to eliminate jitters.
    - **Gesture Mapping**: Pinch detection for clicking/dragging and palm-center tracking for stable movement.
    - **Acceleration**: Non-linear mapping for precise small moves and fast cross-screen flicks.
- **Communication**: 
    - **Bluetooth**: BlueZ profile management for HID emulation.
    - **Serial**: Custom structured protocol transmitted via USB-VCP to STM32.

### 2. STM32 F446RE (The Interface)
- **Display**: SSD1306 OLED via I2C (DMA driven).
- **Communication**: UART DMA with Idle Line Detection for robust packet parsing.
- **UI Logic**: Dynamic icons for 8-directional movement, clicking status, and loading animations.

---

##  Communication Protocol
Data is synchronized from RPi to STM32 using a specialized string format:
`#R,D,Dir,C,FPS,LAT!`
- `R`: Running Status (0/1)
- `D`: Detection Status (0/1)
- `Dir`: Direction Index (0-8: Idle, N, NE, E, SE, S, SW, W, NW)
- `C`: Clicking Status (0/1)
- `FPS`: Frames Per Second
- `LAT`: Inference Latency (ms)

---

##  Hardware Requirements
- **Raspberry Pi 5** (with Camera Module)
- **STM32 Nucleo-F446RE**
- **SSD1306 OLED** (128x64, I2C)
- **USB Cable** (Connecting Nucleo ST-LINK to RPi 5)

---

##  Installation & Setup

### Raspberry Pi Side
1. **Environment**: Use Python 3.11 with a virtual environment.
2. **Dependencies**:
   ```bash
   pip install mediapipe opencv-python-headless pyserial dbus-python evdev
   ```
3. **Bluetooth Configuration**: Enable compatibility mode in `/etc/systemd/system/dbus-org.bluez.service`:
   ```bash
   ExecStart=/usr/lib/bluetooth/bluetoothd -C --noplugin=input
   ```
4. **Run**:
   ```bash
   sudo -E python main.py
   ```

### STM32 Side
1. Open the project in **STM32CubeIDE**.
2. Ensure **USART2** is configured for **DMA with Idle Line Interrupt**.
3. Enable **I2C1** for the OLED screen.
4. Flash the firmware provided in `/stm32_firmware`.

---

##  Usage
1. Power up the system and pair your PC with the Bluetooth device named **"PiGestureMouse"**.
2. Once connected, the STM32 OLED will show `SEARCHING`.
3. Place your right hand in front of the camera (Palm facing the camera).
4. **Move**: Move your palm to move the cursor.
5. **Click/Drag**: Pinch your thumb and index finger.
6. **Pause**: Press the Blue User Button on the Nucleo board to pause/resume.

---

##  Repository Structure
- `/src`: Python source code for RPi (Gesture engine, Bluetooth server).
- `/stm32_firmware`: Full STM32CubeIDE project.
- `/models`: MediaPipe `.task` files.
- `/docs`: Schematics and protocol details.

---
