import os
import time
import threading
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from picamera2 import Picamera2

from src.models import HandState

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode



class GestureRecognizer(threading.Thread):
    def __init__(self, logic_queue, vis_queue):

        # --- Configuration ---
        super().__init__(daemon=True)
        CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
        self.logic_queue = logic_queue
        self.vis_queue = vis_queue
        self.running = True
        self.is_processing = False
        self.last_timestamp = 0
        self.last_callback_time = time.perf_counter()
        self.current_fps = 0.0

        # --- Initialization ---
        print("Initializing camera...")
        self.picam2 = Picamera2()
        config = self.picam2.create_video_configuration(
            main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

        print("Initializing MediaPipe Hand Landmarker...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_asset_path = os.path.join(script_dir, "..", "models", "hand_landmarker.task")
        print(f"Attempting to load model from: {model_asset_path}")
        self.options = HandLandmarkerOptions(
            num_hands=1,
            min_hand_detection_confidence=0.5,
            base_options=BaseOptions(model_asset_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=self.result_callback,
        )
    
    def result_callback(self, result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms):

        self.is_processing = False
        now = time.perf_counter()
        frame_time = now - self.last_callback_time
        if frame_time > 0:
            self.current_fps = 1.0 / frame_time
        self.last_callback_time = now

        now_ms = int(now * 1000)
        latency = now_ms - timestamp_ms
        
        state = HandState.from_mediapipe(result)
        state.fps = self.current_fps
        state.latency_ms = latency
        if self.logic_queue.full():
            self.logic_queue.get_nowait()
        self.logic_queue.put(state)

    def run(self):
        with HandLandmarker.create_from_options(self.options) as landmarker:
            last_frame_time = 0
            frame_interval = 1.0 / 20
            while self.running:
                if self.is_processing:
                    time.sleep(0.001)
                    continue
                current_time = time.perf_counter()

                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue
                frame = self.picam2.capture_array("main") 
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                now_ms = int(time.perf_counter() * 1000)
                if now_ms <= self.last_timestamp:
                    now_ms = self.last_timestamp + 1
                self.last_timestamp = now_ms

                self.is_processing = True
                landmarker.detect_async(mp_image, now_ms)
    
    def stop(self):
        self.running = False
        time.sleep(0.2)
        if self.picam2:
            self.picam2.stop()
            print("Camera and Recognizer stopped.")