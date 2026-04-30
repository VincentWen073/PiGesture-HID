# src/mouse_logic.py
import math

class MouseController:
    def __init__(self, sensitivity=2500, smoothing=0.3):
        self.sensitivity = sensitivity
        self.smoothing = smoothing
        
        self.prev_x, self.prev_y = None, None
        self.confirmed_clicking = False
        self.potential_clicking = False
        self.smoothed_dist = 0.1
        
        self.PRESS_THRESH = 0.05
        self.RELEASE_THRESH = 0.07
        
        self.debounce_counter = 0
        self.CONFIRM_FRAMES = 2

        self.lock_active = False
        self.accumulated_dx = 0
        self.accumulated_dy = 0
        self.BREAKOUT_THRESHOLD = 15

    def process(self, hand_state):
        if not hand_state.is_detected:
            self.prev_x = self.prev_y = None
            event = None
            if self.confirmed_clicking:
                self.confirmed_clicking = False
                self.was_clicking = False
                self.debounce_counter = 0
                event = "RELEASE"
            return 0, 0, event

        dx, dy = self._calculate_movement(hand_state)

        click_event = self._calculate_click_event(hand_state.pinch_distance)

        return dx, dy, click_event
    def _calculate_click_event(self, raw_dist):
        self.smoothed_dist = self.smoothed_dist * 0.3 + raw_dist * 0.7
        
        current_candidate = self.confirmed_clicking
        if not self.confirmed_clicking:
            if self.smoothed_dist < self.PRESS_THRESH:
                current_candidate = True
        else:
            if self.smoothed_dist > self.RELEASE_THRESH:
                current_candidate = False

        event = None
        if current_candidate != self.confirmed_clicking:
            self.debounce_counter += 1
            if self.debounce_counter >= self.CONFIRM_FRAMES:
                self.confirmed_clicking = current_candidate
                self.debounce_counter = 0
                event = "PRESS" if self.confirmed_clicking else "RELEASE"
        else:
            self.debounce_counter = 0
            
        return event

    def _calculate_movement(self, hand_state):
            if self.prev_x is None:
                self.prev_x, self.prev_y = hand_state.x, hand_state.y
                return 0, 0
            
            raw_dx = (hand_state.x - self.prev_x) * self.sensitivity
            raw_dy = (hand_state.y - self.prev_y) * self.sensitivity
            
            distance = math.sqrt(raw_dx**2 + raw_dy**2)
            accel_multiplier = 1.0 + (distance / 50.0) 
            
            accel_multiplier = min(accel_multiplier, 3.0) 
            
            dx = raw_dx * accel_multiplier
            dy = raw_dy * accel_multiplier
            
            self.prev_x, self.prev_y = hand_state.x, hand_state.y
            return int(dx), int(dy)
    
    def get_direction_index(self, dx, dy):
        threshold = 5
        if abs(dx) < threshold and abs(dy) < threshold:
            return 0

        angle = math.atan2(-dy, dx)
        deg = math.degrees(angle)
        if deg < 0: deg += 360

        index = int((deg + 22.5) / 45) % 8
        return index + 1