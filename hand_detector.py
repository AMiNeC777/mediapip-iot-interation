"""
Hand Detector Module using MediaPipe
Supports both the modern MediaPipe Tasks API (MediaPipe 1.x / 0.10.x+)
and legacy mediapipe.solutions (for older versions).
"""

import math
import os
import urllib.request
import cv2
import mediapipe as mp

# Standard 21 Hand Landmark connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (9, 10), (10, 11), (11, 12),           # Middle
    (13, 14), (14, 15), (15, 16),          # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17)              # Palm base knuckles
]

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_FILENAME = "hand_landmarker.task"


class HandDetector:
    def __init__(
        self,
        max_hands: int = 1,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.7,
    ):
        """
        Initializes the Hand detector. Auto-detects whether the modern MediaPipe Tasks API
        or legacy solutions API is available.
        """
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        self.use_tasks_api = not hasattr(mp, "solutions")
        self.raw_landmarks_list = []

        if self.use_tasks_api:
            # Modern MediaPipe 1.x / 0.10+ Tasks API
            self._ensure_model_file()
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_hands=self.max_hands,
                min_hand_detection_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
        else:
            # Legacy mediapipe.solutions API
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self.max_hands,
                min_detection_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence,
            )

    def _ensure_model_file(self):
        """Ensures the hand_landmarker.task model is downloaded locally."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(script_dir, MODEL_FILENAME)
        if not os.path.exists(self.model_path):
            print(f"[INFO] Downloading MediaPipe hand model to {self.model_path} ...")
            urllib.request.urlretrieve(MODEL_URL, self.model_path)
            print("[INFO] Model downloaded successfully.")

    def find_hands(self, img, draw: bool = True):
        """
        Processes image frame and detects hands.
        Draws sleek landmarks and connections directly using OpenCV.
        """
        h, w, _ = img.shape
        self.raw_landmarks_list = []

        if self.use_tasks_api:
            # Modern Tasks API
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            result = self.landmarker.detect(mp_image)

            if result.hand_landmarks:
                for hand_lms in result.hand_landmarks:
                    coords = []
                    for lm in hand_lms:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        coords.append((cx, cy, lm.x, lm.y))
                    self.raw_landmarks_list.append(coords)
        else:
            # Legacy Solutions API
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)
            if results.multi_hand_landmarks:
                for hand_lms in results.multi_hand_landmarks:
                    coords = []
                    for lm in hand_lms.landmark:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        coords.append((cx, cy, lm.x, lm.y))
                    self.raw_landmarks_list.append(coords)

        # Draw hand skeletons
        if draw and self.raw_landmarks_list:
            for coords in self.raw_landmarks_list:
                # 1. Draw connections
                for p1_idx, p2_idx in HAND_CONNECTIONS:
                    x1, y1 = coords[p1_idx][0], coords[p1_idx][1]
                    x2, y2 = coords[p2_idx][0], coords[p2_idx][1]
                    cv2.line(img, (x1, y1), (x2, y2), (255, 120, 0), 2, cv2.LINE_AA)

                # 2. Draw landmarks
                for idx, (cx, cy, _, _) in enumerate(coords):
                    # Fingertip landmarks highlighted in neon green
                    if idx in [4, 8, 12, 16, 20]:
                        cv2.circle(img, (cx, cy), 6, (0, 255, 120), -1, cv2.LINE_AA)
                        cv2.circle(img, (cx, cy), 8, (255, 255, 255), 1, cv2.LINE_AA)
                    else:
                        cv2.circle(img, (cx, cy), 4, (0, 255, 220), -1, cv2.LINE_AA)

        return img

    def get_landmarks(self, img, hand_idx: int = 0):
        """
        Returns list of landmarks [{'id': i, 'x': px, 'y': py, ...}]
        and bounding box (xmin, ymin, xmax, ymax).
        """
        lm_list = []
        bbox = None

        if self.raw_landmarks_list and hand_idx < len(self.raw_landmarks_list):
            coords = self.raw_landmarks_list[hand_idx]
            x_list = []
            y_list = []

            for idx, (cx, cy, norm_x, norm_y) in enumerate(coords):
                x_list.append(cx)
                y_list.append(cy)
                lm_list.append({"id": idx, "x": cx, "y": cy, "norm_x": norm_x, "norm_y": norm_y})

            xmin, xmax = min(x_list), max(x_list)
            ymin, ymax = min(y_list), max(y_list)
            bbox = (xmin, ymin, xmax, ymax)

        return lm_list, bbox

    def count_fingers(self, lm_list) -> tuple[int, list[int]]:
        """
        Counts how many fingers are extended.
        Returns:
            total_fingers (int): 0 to 5
            fingers_status (list[int]): [Thumb, Index, Middle, Ring, Pinky] (1=up, 0=down)
        """
        if not lm_list or len(lm_list) < 21:
            return 0, [0, 0, 0, 0, 0]

        fingers = []

        # 1. Thumb detection:
        # Distance between Thumb Tip (4) and Pinky MCP (17) vs Thumb IP (3) and Pinky MCP (17)
        # When extended outward, distance(4, 17) > distance(3, 17)
        d_tip_pinky = math.hypot(lm_list[4]["x"] - lm_list[17]["x"], lm_list[4]["y"] - lm_list[17]["y"])
        d_ip_pinky = math.hypot(lm_list[3]["x"] - lm_list[17]["x"], lm_list[3]["y"] - lm_list[17]["y"])

        if d_tip_pinky > d_ip_pinky * 1.12:
            fingers.append(1)
        else:
            fingers.append(0)

        # 2. Four Fingers (Index, Middle, Ring, Pinky):
        # Finger is extended if Tip Y is higher (smaller value) than PIP joint Y
        # Tip IDs: 8, 12, 16, 20
        # PIP IDs: 6, 10, 14, 18
        for tip_id in [8, 12, 16, 20]:
            pip_id = tip_id - 2
            if lm_list[tip_id]["y"] < lm_list[pip_id]["y"]:
                fingers.append(1)
            else:
                fingers.append(0)

        total_fingers = fingers.count(1)
        return total_fingers, fingers
