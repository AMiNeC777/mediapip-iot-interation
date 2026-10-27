"""
Interactive MQTT Diagnostic & Manual Control Tool
Use this to test the ESP32 connection independently of the webcam/MediaPipe!
"""

import sys
import time
import paho.mqtt.client as mqtt

import config

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[TEST TOOL] Connected to broker: {config.MQTT_BROKER}")
        client.subscribe(config.MQTT_TOPIC_STATUS)
        client.subscribe(config.MQTT_TOPIC_LED)
        print(f"[TEST TOOL] Subscribed to status: {config.MQTT_TOPIC_STATUS}")
    else:
        print(f"[TEST TOOL] Connection failed with code: {rc}")

def on_message(client, userdata, msg):
    print(f"\n<<< [INCOMING] Topic: {msg.topic} | Message: {msg.payload.decode('utf-8')}")
    print("Choice (1=ON, 0=OFF, q=Quit): ", end="", flush=True)

def main():
    print("=" * 60)
    print(" MQTT Diagnostic & Manual LED Controller")
    print(f" Target Topic: {config.MQTT_TOPIC_LED}")
    print("=" * 60)

    if hasattr(mqtt, "CallbackAPIVersion"):
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="Diagnostic_Tool")
    else:
        client = mqtt.Client(client_id="Diagnostic_Tool")

    client.on_connect = on_connect
    client.on_message = on_message

    if config.MQTT_USERNAME and config.MQTT_PASSWORD:
        client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)

    client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
    client.loop_start()

    time.sleep(1)

    print("\nCommands:")
    print("  '1' or 'on'  -> Turn LED ON")
    print("  '0' or 'off' -> Turn LED OFF")
    print("  'q'          -> Quit\n")

    try:
        while True:
            cmd = input("Choice (1=ON, 0=OFF, q=Quit): ").strip().lower()
            if cmd in ["1", "on"]:
                client.publish(config.MQTT_TOPIC_LED, "ON")
                print(">>> Published 'ON'")
            elif cmd in ["0", "off"]:
                client.publish(config.MQTT_TOPIC_LED, "OFF")
                print(">>> Published 'OFF'")
            elif cmd in ["q", "exit"]:
                break
            else:
                print("Invalid input. Enter '1', '0', or 'q'.")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print("\nTest tool closed.")

if __name__ == "__main__":
    main()
