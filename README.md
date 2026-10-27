# 🖐️ MediaPipe Hand Gesture Control for ESP32 LED via MQTT

Control an LED connected to an ESP32 microcontroller using hand gestures detected from your computer's webcam via Google MediaPipe and MQTT.

---

## 🌟 System Overview & Architecture

```
+--------------------------+       MQTT Pub       +------------------------+
|   Python Application     | -------------------> |      MQTT Broker       |
|  - OpenCV Video Stream   |   Topic:             |  (e.g., HiveMQ / EMQX) |
|  - MediaPipe Hands Model |   iot/m2_bdio/...    |   broker.hivemq.com    |
|  - Gesture Recognition   |                      +------------------------+
+--------------------------+                                   |
                                                               | MQTT Sub
                                                               v
                                                  +------------------------+
                                                  |     ESP32 Board        |
                                                  |  - Wi-Fi Station       |
                                                  |  - PubSubClient MQTT   |
                                                  |  - Controls GPIO 2     |
                                                  +------------------------+
                                                               |
                                                               v
                                                          [ 💡 LED ]
```

---

## 📁 Project Structure

```
mediapip/
├── config.py                 # Central configuration (MQTT broker, camera, thresholds)
├── hand_detector.py          # MediaPipe hand tracking & finger counting module
├── mqtt_client.py            # Paho-MQTT publisher client with auto-reconnect
├── main.py                   # Main real-time OpenCV webcam application with HUD
├── test_mqtt.py              # CLI diagnostic tool to test ESP32 without camera
├── requirements.txt          # Python dependencies
├── README.md                 # Project guide
└── esp32_firmware/
    ├── esp32_firmware.ino    # Arduino sketch for ESP32
    └── platformio.ini        # PlatformIO configuration (optional)
```

---

## 🖐️ Gesture Mappings

| Gesture | Finger Count | Action | MQTT Payload | Visual HUD |
| :--- | :--- | :--- | :--- | :--- |
| **Open Palm / Hand** | $\ge 4$ fingers extended | Turn LED **ON** | `"ON"` | Green Badge `[LED STATUS: ON]` |
| **Closed Fist** | $\le 1$ finger extended | Turn LED **OFF** | `"OFF"` | Red Badge `[LED STATUS: OFF]` |
| **Intermediate** | 2–3 fingers | Holds last state | None (debounced) | Status unchanged |

---

## ⚡ Quick Start

### 1. Python Setup (Host PC)

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Required packages: `opencv-python`, `mediapipe`, `paho-mqtt`)*

2. **Verify Configuration**:
   Open [`config.py`](config.py) and check:
   - `MQTT_BROKER`: `"broker.hivemq.com"` (free, public cloud broker)
   - `MQTT_TOPIC_LED`: `"iot/m2_bdio/esp32/led"` (customize prefix to avoid collisions)
   - `CAMERA_INDEX`: `0` (built-in webcam) or `1` / `2` (USB external webcam)

---

### 2. ESP32 Firmware Setup

#### Hardware:
- **Board**: ESP32 DevKit v1, NodeMCU-32S, or similar ESP32 board.
- **LED**: 
  - **Option A (Built-in)**: Uses on-board blue LED on **GPIO 2** (no extra wiring required).
  - **Option B (External)**: Anode (+) connected to **GPIO 2** through a 220Ω resistor, Cathode (-) to **GND**.

#### Flashing via Arduino IDE:
1. Open Arduino IDE.
2. Go to **Tools > Board > esp32 > ESP32 Dev Module** (install `esp32` via Boards Manager if needed).
3. Install the MQTT library:
   - Go to **Sketch > Include Library > Manage Libraries...**
   - Search for **`PubSubClient`** by *Nick O'Leary* and click **Install**.
4. Open [`esp32_firmware/esp32_firmware.ino`](esp32_firmware/esp32_firmware.ino).
5. Edit your Wi-Fi credentials:
   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   ```
6. Verify that `MQTT_BROKER` and `TOPIC_LED` match [`config.py`](config.py).
7. Connect your ESP32 via USB and click **Upload**.
8. Open the **Serial Monitor** (set baud rate to **115200**):
   - You should see the ESP32 connect to Wi-Fi and subscribe to the MQTT topic.

---

### 3. Testing Communication (Diagnostic Tool)

Before running the webcam, test if your ESP32 is receiving MQTT commands:

```bash
python test_mqtt.py
```
- Press `1` then Enter: ESP32 LED turns **ON**.
- Press `0` then Enter: ESP32 LED turns **OFF**.
- Press `q` to exit.

---

### 4. Run Hand Tracking Controller

Run the main application:

```bash
python main.py
```

- A video window opens with a real-time HUD showing:
  - **MQTT Connection Status** (green dot when online)
  - **Active Fingers Tracker** (dots for Thumb, Index, Middle, Ring, Pinky)
  - **Current LED State**
  - **FPS Counter**
- Show an **open hand** to turn the LED **ON**.
- Make a **fist** to turn the LED **OFF**.
- Press keyboard `q` to quit safely.

---

## 🛠️ Troubleshooting

- **ESP32 won't connect to Wi-Fi**:
  - ESP32 only supports **2.4 GHz Wi-Fi** networks (it does not connect to 5 GHz-only SSIDs).
- **MQTT messages not received**:
  - Ensure both PC and ESP32 are using the exact same `MQTT_BROKER` and `MQTT_TOPIC_LED`.
  - Check your firewall if using a local broker instead of `broker.hivemq.com`.
- **Webcam not opening**:
  - In [`config.py`](config.py), try changing `CAMERA_INDEX = 1` or `2`.
- **LED logic inverted on your board**:
  - Some ESP32 development boards have active-low LEDs. In [`esp32_firmware.ino`](esp32_firmware/esp32_firmware.ino), swap `LED_ACTIVE_STATE = LOW` and `LED_INACTIVE_STATE = HIGH`.
