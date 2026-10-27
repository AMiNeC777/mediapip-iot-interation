/*
 * ==============================================================================
 * ESP32 MediaPipe Hand Detection MQTT LED Receiver
 * ==============================================================================
 * Description:
 *   Subscribes to an MQTT topic controlled by Python MediaPipe Hand Tracking.
 *   Controls an on-board or external LED in real-time.
 * 
 * Hardware:
 *   - ESP32 Development Board (e.g. ESP32 NodeMCU, DevKit v1)
 *   - Built-in LED on GPIO 2 (or connect external LED with 220-330 ohm resistor)
 * 
 * Dependencies (install via Arduino IDE Library Manager):
 *   - PubSubClient by Nick O'Leary
 * ==============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// 1. NETWORK & MQTT CONFIGURATION
// ==========================================
// Replace with your Wi-Fi credentials
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// MQTT Broker Settings (Must match config.py in Python)
const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "";  // Leave empty if not using authentication
const char* MQTT_PASS     = "";

// MQTT Topics (Must match config.py in Python)
const char* TOPIC_LED     = "iot/m2_bdio/esp32/led";
const char* TOPIC_STATUS  = "iot/m2_bdio/esp32/status";

// Unique Client ID for ESP32
const char* MQTT_CLIENT_ID = "ESP32_MediaPipe_LED_Client";

// ==========================================
// 2. HARDWARE PIN DEFINITIONS
// ==========================================
// GPIO 2 is the built-in blue LED on most ESP32 DevKit boards.
// If your board uses a different pin, or an external LED, change it here.
const int LED_PIN = 2;

// Active level: set to HIGH if LED turns on with HIGH signal (standard)
// Set to LOW if active-low
const int LED_ACTIVE_STATE = HIGH;
const int LED_INACTIVE_STATE = LOW;


// ==========================================
// 3. OBJECTS & GLOBALS
// ==========================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastMqttReconnectAttempt = 0;
const unsigned long RECONNECT_INTERVAL_MS = 5000;


// ==========================================
// 4. MQTT MESSAGE CALLBACK
// ==========================================
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  // Convert payload to String
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();

  Serial.println();
  Serial.print("[MQTT] Received message on topic: ");
  Serial.println(topic);
  Serial.print("[MQTT] Payload: '");
  Serial.print(message);
  Serial.println("'");

  // Act on LED state
  if (message.equalsIgnoreCase("ON") || message == "1") {
    digitalWrite(LED_PIN, LED_ACTIVE_STATE);
    Serial.println("[ACTION] >>> LED turned ON (Open Hand Detected)");
    mqttClient.publish(TOPIC_STATUS, "LED_IS_ON");
  } 
  else if (message.equalsIgnoreCase("OFF") || message == "0") {
    digitalWrite(LED_PIN, LED_INACTIVE_STATE);
    Serial.println("[ACTION] >>> LED turned OFF (Fist Detected)");
    mqttClient.publish(TOPIC_STATUS, "LED_IS_OFF");
  } 
  else {
    Serial.println("[WARNING] Unknown command received. Expected 'ON' or 'OFF'.");
  }
}


// ==========================================
// 5. WI-FI INITIALIZATION
// ==========================================
void connectWiFi() {
  Serial.println();
  Serial.print("Connecting to Wi-Fi SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // Fast blink while attempting Wi-Fi connection
  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
    Serial.print(".");
  }

  Serial.println("\n[Wi-Fi] Connected successfully!");
  Serial.print("[Wi-Fi] IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("[Wi-Fi] Signal Strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");

  // Turn LED OFF after connection
  digitalWrite(LED_PIN, LED_INACTIVE_STATE);
}


// ==========================================
// 6. NON-BLOCKING MQTT RECONNECT
// ==========================================
boolean reconnectMQTT() {
  Serial.print("[MQTT] Attempting connection to broker: ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.println(MQTT_PORT);

  // Create unique client id with random suffix to avoid duplicate client conflicts
  String clientId = String(MQTT_CLIENT_ID) + "_" + String(random(0xffff), HEX);

  bool connected = false;
  if (strlen(MQTT_USER) > 0) {
    connected = mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS);
  } else {
    connected = mqttClient.connect(clientId.c_str());
  }

  if (connected) {
    Serial.println("[MQTT] Connected to broker!");
    
    // Subscribe to LED command topic
    if (mqttClient.subscribe(TOPIC_LED)) {
      Serial.print("[MQTT] Successfully subscribed to: ");
      Serial.println(TOPIC_LED);
    } else {
      Serial.println("[ERROR] Failed to subscribe to LED topic!");
    }

    // Publish boot online status
    mqttClient.publish(TOPIC_STATUS, "ESP32_ONLINE");

    // Success double flash
    for (int i = 0; i < 2; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(150);
      digitalWrite(LED_PIN, LOW);
      delay(150);
    }
    return true;
  } else {
    Serial.print("[MQTT] Connection failed, rc=");
    Serial.print(mqttClient.state());
    Serial.println(" (Will retry in 5s...)");
    return false;
  }
}


// ==========================================
// 7. SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=============================================");
  Serial.println(" ESP32 MediaPipe Hand Gesture LED Controller ");
  Serial.println("=============================================");

  // Initialize LED pin as OUTPUT
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LED_INACTIVE_STATE);

  // Connect to Wi-Fi
  connectWiFi();

  // Configure MQTT Client
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(onMqttMessage);
  mqttClient.setBufferSize(256);

  randomSeed(micros());
}


// ==========================================
// 8. MAIN LOOP
// ==========================================
void loop() {
  // Ensure Wi-Fi stays connected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[Wi-Fi] Connection lost. Reconnecting...");
    connectWiFi();
  }

  // Ensure MQTT client stays connected (non-blocking)
  if (!mqttClient.connected()) {
    unsigned long now = millis();
    if (now - lastMqttReconnectAttempt > RECONNECT_INTERVAL_MS) {
      lastMqttReconnectAttempt = now;
      if (reconnectMQTT()) {
        lastMqttReconnectAttempt = 0;
      }
    }
  } else {
    // Service MQTT incoming messages and keepalive pings
    mqttClient.loop();
  }
}
