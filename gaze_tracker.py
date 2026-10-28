import cv2
import mediapipe as mp
import numpy as np

class GazeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Eye landmark indices (MediaPipe face mesh)
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]

        # Gaze tracking data
        self.gaze_history = []
        self.fixation_threshold = 10  # frames

    def track(self, frame):
        """
        Track eye gaze based on iris position RELATIVE to eye corners
        Returns: (processed_frame, gaze_data)
        """
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        gaze_data = {
            'gaze_x': 0.5,
            'gaze_y': 0.5,
            'fixation_detected': False,
            'reading_line': 0
        }

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]

            # Get iris and eye corner positions for BOTH eyes
            left_iris = self._get_landmark_center(face_landmarks, self.LEFT_IRIS, w, h)
            right_iris = self._get_landmark_center(face_landmarks, self.RIGHT_IRIS, w, h)

            # Get eye corners to calculate relative iris position
            left_eye_corners = self._get_eye_corners(face_landmarks, "left", w, h)
            right_eye_corners = self._get_eye_corners(face_landmarks, "right", w, h)

            if all([left_iris, right_iris, left_eye_corners, right_eye_corners]):
                # Calculate gaze based on iris position WITHIN the eye
                left_gaze = self._calculate_relative_gaze(left_iris, left_eye_corners)
                right_gaze = self._calculate_relative_gaze(right_iris, right_eye_corners)

                # Average both eyes
                gaze_x = (left_gaze[0] + right_gaze[0]) / 2.0
                gaze_y = (left_gaze[1] + right_gaze[1]) / 2.0

                # Normalize and invert Y (looking up should be low Y value)
                gaze_data['gaze_x'] = np.clip(gaze_x, 0.0, 1.0)
                gaze_data['gaze_y'] = np.clip(1.0 - gaze_y, 0.0, 1.0)  # Invert Y

                # Draw eye regions for debugging
                if left_eye_corners and left_iris:
                    cv2.circle(frame, left_iris, 3, (0, 255, 255), -1)
                    cv2.rectangle(frame, 
                                (left_eye_corners['left'], left_eye_corners['top']),
                                (left_eye_corners['right'], left_eye_corners['bottom']),
                                (0, 255, 0), 1)

                if right_eye_corners and right_iris:
                    cv2.circle(frame, right_iris, 3, (0, 255, 255), -1)
                    cv2.rectangle(frame,
                                (right_eye_corners['left'], right_eye_corners['top']),
                                (right_eye_corners['right'], right_eye_corners['bottom']),
                                (0, 255, 0), 1)

                # Detect fixation
                self.gaze_history.append((gaze_data['gaze_x'], gaze_data['gaze_y']))
                if len(self.gaze_history) > 30:
                    self.gaze_history.pop(0)

                if self._is_fixating():
                    gaze_data['fixation_detected'] = True
                    gaze_data['reading_line'] = int(gaze_data['gaze_y'] * 20)

        return frame, gaze_data

    def _get_landmark_center(self, face_landmarks, indices, w, h):
        """Calculate center point of landmark group"""
        points = []
        for idx in indices:
            landmark = face_landmarks.landmark[idx]
            points.append((landmark.x * w, landmark.y * h))

        if points:
            center_x = sum([p[0] for p in points]) / len(points)
            center_y = sum([p[1] for p in points]) / len(points)
            return (int(center_x), int(center_y))
        return None

    def _get_eye_corners(self, face_landmarks, eye_side, w, h):
        """Get eye bounding box corners"""
        if eye_side == "left":
            indices = self.LEFT_EYE
        else:
            indices = self.RIGHT_EYE

        eye_points = []
        for idx in indices:
            landmark = face_landmarks.landmark[idx]
            eye_points.append((landmark.x * w, landmark.y * h))

        if eye_points:
            xs = [p[0] for p in eye_points]
            ys = [p[1] for p in eye_points]
            return {
                'left': int(min(xs)),
                'right': int(max(xs)),
                'top': int(min(ys)),
                'bottom': int(max(ys))
            }
        return None

    def _calculate_relative_gaze(self, iris_pos, eye_corners):
        """
        Calculate where iris is looking RELATIVE to eye corners
        Returns (x, y) normalized 0-1 within the eye
        """
        iris_x, iris_y = iris_pos

        eye_width = eye_corners['right'] - eye_corners['left']
        eye_height = eye_corners['bottom'] - eye_corners['top']

        if eye_width == 0 or eye_height == 0:
            return (0.5, 0.5)

        # Calculate relative position within eye
        rel_x = (iris_x - eye_corners['left']) / eye_width
        rel_y = (iris_y - eye_corners['top']) / eye_height

        # Apply some scaling to make it more sensitive
        # Eyes typically don't move to extreme corners
        rel_x = (rel_x - 0.5) * 2.0 + 0.5  # Amplify deviation from center
        rel_y = (rel_y - 0.5) * 2.0 + 0.5

        return (rel_x, rel_y)

    def _is_fixating(self):
        """Detect if eyes are fixating"""
        if len(self.gaze_history) < self.fixation_threshold:
            return False

        recent_gazes = self.gaze_history[-self.fixation_threshold:]
        x_coords = [g[0] for g in recent_gazes]
        y_coords = [g[1] for g in recent_gazes]

        # Check if variance is low
        x_var = np.var(x_coords)
        y_var = np.var(y_coords)

        return (x_var < 0.008 and y_var < 0.008)  # Slightly tighter threshold

    def release(self):
        """Release resources"""
        self.face_mesh.close()