"""
Configuration settings for MediaPipe Hand Detection & MQTT ESP32 LED Controller
"""

# ==========================================
# MQTT BROKER CONFIGURATION
# ==========================================
# Public test brokers: "broker.hivemq.com", "broker.emqx.io", "test.mosquitto.org"
# Or your local broker IP (e.g., "192.168.1.50")
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "MediaPipe_Hand_Controller"

# Use a unique topic prefix so you don't clash with others on a public broker!
# Change "m2_bdio" to your team name or custom ID if desired
MQTT_TOPIC_LED = "iot/m2_bdio/esp32/led"
MQTT_TOPIC_STATUS = "iot/m2_bdio/esp32/status"

# MQTT Keepalive in seconds
MQTT_KEEPALIVE = 60

# Optional MQTT Auth (leave empty strings if not needed)
MQTT_USERNAME = ""
MQTT_PASSWORD = ""


# ==========================================
# CAMERA & MEDIAPIPE CONFIGURATION
# ==========================================
CAMERA_INDEX = 0          # 0 for default internal webcam, 1 or 2 for external USB webcam
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FLIP_CAMERA = True        # Mirror effect for natural hand movement

# MediaPipe Hands Model Parameters
MAX_NUM_HANDS = 1         # Tracking 1 hand is best for unambiguous control
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.7


# ==========================================
# GESTURE & CONTROL RULES
# ==========================================
# Finger Thresholds:
# Open Palm (>= 4 fingers up) -> Turn LED ON
# Closed Fist (<= 1 finger up) -> Turn LED OFF
FINGERS_ON_THRESHOLD = 4
FINGERS_OFF_THRESHOLD = 1

# Stability / Debounce:
# Number of consecutive identical frames required before triggering an MQTT state change
DEBOUNCE_FRAMES = 5
