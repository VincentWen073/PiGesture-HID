from dataclasses import dataclass
from typing import Optional
import math
import numpy as np

@dataclass
class HandState:
    is_detected: bool = False
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    is_clicking: bool = False
    pinch_distance: float = 1.0
    handedness: str = ""
    fps: float = 0.0
    latency_ms: float = 0.0

    @classmethod
    def from_mediapipe(cls, result):
        if not result or not result.hand_landmarks:
            return cls(is_detected=False)

        # Ignore the lift hand
        target_idx = -1
        for i, handedness_list in enumerate(result.handedness):

            label = handedness_list[0].category_name 
            if label == "Right": 
                target_idx = i
                break
        
        if target_idx == -1:
            return cls(is_detected=False)

        landmarks = result.hand_landmarks[target_idx]
        handedness_info = result.handedness[target_idx][0].category_name
        # --- 1. Filter out hand poses with excessive tilt to avoid accidental triggers.
        p0 = np.array([landmarks[0].x, landmarks[0].y, landmarks[0].z])
        p5 = np.array([landmarks[5].x, landmarks[5].y, landmarks[5].z])
        p17 = np.array([landmarks[17].x, landmarks[17].y, landmarks[17].z])

        v1 = p5 - p0
        v2 = p17 - p0
        
        palm_normal = np.cross(v1, v2)
        palm_normal /= np.linalg.norm(palm_normal)
        
        camera_axis = np.array([0, 0, -1])
        cos_theta = np.dot(palm_normal, camera_axis)
        if cos_theta < 0.707:
                return cls(is_detected=False)
        
        # --- 2. Calculate the middle point of palm ---
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        
        palm_x = (wrist.x + middle_mcp.x) / 2
        palm_y = (wrist.y + middle_mcp.y) / 2
        palm_z = (wrist.z + middle_mcp.z) / 2

        # --- 3. Mirror the horizonal direction ---
        mirrored_x = 1.0 - palm_x

        # --- 4. Click logic ---
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        dist = math.sqrt(
            (index_tip.x - thumb_tip.x)**2 + 
            (index_tip.y - thumb_tip.y)**2 + 
            (index_tip.z - thumb_tip.z)**2
        )        
        return cls(
            is_detected=True,
            x=mirrored_x,
            y=palm_y,
            z=palm_z,
            pinch_distance=dist,
            handedness=handedness_info
        )

@dataclass
class DisplayData:
    is_running: bool
    is_detected: bool
    direction: int  # 0-8
    is_clicking: bool
    fps: int
    latency: int