import cv2
import mediapipe as mp
import numpy as np
from enum import Enum

class Gesture(Enum):
    """Defined gestures for reading control"""
    NONE = 0
    ZOOM_IN = 1      # SPREAD gesture
    ZOOM_OUT = 2     # PINCH gesture
    NEXT_PAGE = 3    # Swipe right
    PREV_PAGE = 4    # Swipe left

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

        # For gesture tracking
        self.prev_wrist_position = None
        self.gesture_cooldown = 0
        self.gesture_hold_frames = 0
        self.last_gesture = Gesture.NONE
        self.gesture_threshold = 10  # Reduced from 15 for faster response

        # Swipe tracking
        self.swipe_start_x = None
        self.swipe_frames = 0

    def detect(self, frame):
        """Detect hand gestures from webcam frame"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        gesture = Gesture.NONE

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS
                )

                # Detect gestures
                if self.gesture_cooldown == 0:
                    detected = self._classify_gesture(hand_landmarks, frame.shape)

                    # Special handling for swipe (doesn't need hold)
                    if detected in [Gesture.NEXT_PAGE, Gesture.PREV_PAGE]:
                        gesture = detected
                        self.gesture_cooldown = 30  # Shorter cooldown for swipe
                        self.swipe_start_x = None
                        self.swipe_frames = 0
                    # Regular gestures need hold
                    elif detected == self.last_gesture and detected != Gesture.NONE:
                        self.gesture_hold_frames += 1
                        if self.gesture_hold_frames >= self.gesture_threshold:
                            gesture = detected
                            self.gesture_cooldown = 45
                            self.gesture_hold_frames = 0
                    else:
                        self.last_gesture = detected
                        self.gesture_hold_frames = 0
        else:
            # No hand detected
            self.gesture_hold_frames = 0
            self.last_gesture = Gesture.NONE
            self.swipe_start_x = None
            self.swipe_frames = 0

        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1

        return frame, gesture

    def _classify_gesture(self, landmarks, frame_shape):
        """Classify gestures"""
        # Extract key points
        thumb_tip = landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        pinky_tip = landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        wrist = landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        middle_mcp = landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]

        # Calculate distances
        thumb_index_dist = self._distance(thumb_tip, index_tip)
        finger_spread = self._distance(index_tip, pinky_tip)

        # SWIPE DETECTION (improved - check for fast horizontal movement)
        current_wrist_x = wrist.x

        if self.swipe_start_x is None:
            self.swipe_start_x = current_wrist_x
            self.swipe_frames = 0
        else:
            self.swipe_frames += 1

            # Check if hand moved significantly in short time
            if self.swipe_frames >= 5 and self.swipe_frames <= 20:  # 5-20 frames
                movement = current_wrist_x - self.swipe_start_x

                # More sensitive swipe detection
                if movement > 0.05:  # Moved right
                    return Gesture.NEXT_PAGE
                elif movement < -0.05:  # Moved left
                    return Gesture.PREV_PAGE

            # Reset if too slow
            if self.swipe_frames > 20:
                self.swipe_start_x = current_wrist_x
                self.swipe_frames = 0

        # SPREAD = ZOOM IN
        if thumb_index_dist > 0.20 and finger_spread > 0.15:
            return Gesture.ZOOM_IN

        # PINCH = ZOOM OUT
        if thumb_index_dist < 0.03 and finger_spread > 0.1:
            return Gesture.ZOOM_OUT

        return Gesture.NONE

    def _distance(self, point1, point2):
        """Calculate Euclidean distance"""
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    def release(self):
        """Release resources"""
        self.hands.close()