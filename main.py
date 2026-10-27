"""
Main MediaPipe Hand Gesture Controller for ESP32 LED via MQTT
"""

import time
import cv2
import numpy as np

import config
from hand_detector import HandDetector
from mqtt_client import MqttPublisher


def draw_hud(
    img,
    fps: float,
    mqtt_connected: bool,
    finger_count: int,
    fingers_state: list[int],
    current_led_state: str,
    hand_detected: bool,
):
    """
    Renders a modern, HUD overlay on top of the webcam feed.
    """
    h, w, _ = img.shape

    # 1. Glassmorphic Status Card (Top Left)
    card_w, card_h = 340, 190
    card_x, card_y = 20, 20

    # Create semi-transparent overlay
    overlay = img.copy()
    cv2.rectangle(
        overlay,
        (card_x, card_y),
        (card_x + card_w, card_y + card_h),
        (20, 24, 30),
        -1,
    )
    # Blend overlay with original frame (alpha = 0.8)
    cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)

    # Rounded-look card border
    cv2.rectangle(
        img,
        (card_x, card_y),
        (card_x + card_w, card_y + card_h),
        (80, 90, 105),
        1,
        cv2.LINE_AA,
    )

    # Title
    cv2.putText(
        img,
        "ESP32 HAND CONTROLLER",
        (card_x + 15, card_y + 30),
        cv2.FONT_HERSHEY_DUPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # MQTT Indicator
    mqtt_status_text = "MQTT: ONLINE" if mqtt_connected else "MQTT: CONNECTING..."
    mqtt_color = (0, 255, 120) if mqtt_connected else (0, 140, 255)
    cv2.circle(img, (card_x + 22, card_y + 60), 6, mqtt_color, -1, cv2.LINE_AA)
    cv2.putText(
        img,
        mqtt_status_text,
        (card_x + 36, card_y + 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        mqtt_color,
        1,
        cv2.LINE_AA,
    )

    # Hand & Finger Count
    if hand_detected:
        finger_text = f"Fingers Detected: {finger_count}/5"
        cv2.putText(
            img,
            finger_text,
            (card_x + 15, card_y + 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

        # 5 Mini finger dots indicator [T, I, M, R, P]
        finger_names = ["T", "I", "M", "R", "P"]
        for idx, (f_name, is_up) in enumerate(zip(finger_names, fingers_state)):
            dot_x = card_x + 25 + idx * 32
            dot_y = card_y + 130
            dot_color = (0, 255, 200) if is_up else (70, 75, 85)
            cv2.circle(img, (dot_x, dot_y), 9, dot_color, -1, cv2.LINE_AA)
            cv2.putText(
                img,
                f_name,
                (dot_x - 4, dot_y + 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (10, 10, 10) if is_up else (160, 160, 160),
                1,
                cv2.LINE_AA,
            )
    else:
        cv2.putText(
            img,
            "No hand in frame",
            (card_x + 15, card_y + 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (120, 130, 140),
            1,
            cv2.LINE_AA,
        )

    # LED State Badge (Glowing box)
    badge_x = card_x + 15
    badge_y = card_y + 148
    badge_w = card_w - 30
    badge_h = 32

    if current_led_state == "ON":
        badge_bg = (30, 180, 80)      # Vibrant green
        badge_text = "LED STATUS: ON  (OPEN PALM)"
        text_color = (255, 255, 255)
    elif current_led_state == "OFF":
        badge_bg = (40, 45, 180)      # Crimson red
        badge_text = "LED STATUS: OFF (FIST)"
        text_color = (255, 255, 255)
    else:
        badge_bg = (50, 55, 65)       # Neutral gray
        badge_text = "LED STATUS: WAITING"
        text_color = (180, 180, 180)

    cv2.rectangle(
        img,
        (badge_x, badge_y),
        (badge_x + badge_w, badge_y + badge_h),
        badge_bg,
        -1,
    )
    cv2.putText(
        img,
        badge_text,
        (badge_x + 15, badge_y + 21),
        cv2.FONT_HERSHEY_DUPLEX,
        0.48,
        text_color,
        1,
        cv2.LINE_AA,
    )

    # 2. FPS indicator (Top Right)
    fps_text = f"FPS: {int(fps)}"
    cv2.putText(
        img,
        fps_text,
        (w - 110, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 200),
        2,
        cv2.LINE_AA,
    )

    # 3. Bottom Guide Bar
    footer_text = "Gesture Guide: Open Hand (>=4) = LED ON  |  Fist (<=1) = LED OFF  |  [Q]: Quit"
    footer_overlay = img.copy()
    cv2.rectangle(footer_overlay, (0, h - 35), (w, h), (15, 17, 22), -1)
    cv2.addWeighted(footer_overlay, 0.8, img, 0.2, 0, img)
    cv2.putText(
        img,
        footer_text,
        (20, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (200, 205, 215),
        1,
        cv2.LINE_AA,
    )


def main():
    print("=" * 60)
    print(" MediaPipe Hands -> MQTT ESP32 LED Controller")
    print(f" MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
    print(f" MQTT Topic:  {config.MQTT_TOPIC_LED}")
    print("=" * 60)

    # 1. Initialize MQTT Client
    mqtt = MqttPublisher(
        broker=config.MQTT_BROKER,
        port=config.MQTT_PORT,
        client_id=config.MQTT_CLIENT_ID,
        username=config.MQTT_USERNAME,
        password=config.MQTT_PASSWORD,
        keepalive=config.MQTT_KEEPALIVE,
    )
    mqtt.start()

    # 2. Initialize Hand Detector
    detector = HandDetector(
        max_hands=config.MAX_NUM_HANDS,
        detection_confidence=config.DETECTION_CONFIDENCE,
        tracking_confidence=config.TRACKING_CONFIDENCE,
    )

    # 3. Open Camera
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera at index {config.CAMERA_INDEX}.")
        print("Please check your webcam connection or change CAMERA_INDEX in config.py.")
        mqtt.stop()
        return

    current_led_state = "OFF"
    pending_state = None
    state_counter = 0

    prev_time = time.time()
    fps = 0.0

    print("\nStarting video stream. Press 'q' in the window to exit.")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("[WARNING] Failed to capture frame from webcam.")
                time.sleep(0.05)
                continue

            if config.FLIP_CAMERA:
                frame = cv2.flip(frame, 1)

            # Process frame with MediaPipe
            frame = detector.find_hands(frame, draw=True)
            lm_list, bbox = detector.get_landmarks(frame, hand_idx=0)

            finger_count = 0
            fingers_state = [0, 0, 0, 0, 0]
            hand_detected = len(lm_list) > 0

            target_state = None

            if hand_detected:
                finger_count, fingers_state = detector.count_fingers(lm_list)

                # Determine target state based on thresholds
                if finger_count >= config.FINGERS_ON_THRESHOLD:
                    target_state = "ON"
                elif finger_count <= config.FINGERS_OFF_THRESHOLD:
                    target_state = "OFF"

            # Debouncing state transitions
            if target_state is not None and target_state != current_led_state:
                if target_state == pending_state:
                    state_counter += 1
                    if state_counter >= config.DEBOUNCE_FRAMES:
                        # Confirmed state transition
                        current_led_state = target_state
                        print(f"[STATE CHANGE] -> Turning LED {current_led_state}")
                        mqtt.publish(config.MQTT_TOPIC_LED, current_led_state)
                        state_counter = 0
                        pending_state = None
                else:
                    pending_state = target_state
                    state_counter = 1
            else:
                state_counter = 0
                pending_state = None

            # Calculate FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time

            # Render UI
            draw_hud(
                frame,
                fps=fps,
                mqtt_connected=mqtt.is_connected,
                finger_count=finger_count,
                fingers_state=fingers_state,
                current_led_state=current_led_state,
                hand_detected=hand_detected,
            )

            cv2.imshow("MediaPipe Hand Controller - ESP32 MQTT", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Exit signal received.")
                break
            elif key == ord("1"):
                # Manual toggle ON
                current_led_state = "ON"
                mqtt.publish(config.MQTT_TOPIC_LED, "ON")
            elif key == ord("0"):
                # Manual toggle OFF
                current_led_state = "OFF"
                mqtt.publish(config.MQTT_TOPIC_LED, "OFF")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        mqtt.stop()
        print("Application terminated cleanly.")


if __name__ == "__main__":
    main()
