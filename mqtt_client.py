"""
MQTT Client Wrapper using Paho-MQTT (supports v2.x and v1.x)
Handles connection, publication, and connection state tracking.
"""

import logging
import time
import paho.mqtt.client as mqtt

logger = logging.getLogger("MQTTClient")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")


class MqttPublisher:
    def __init__(
        self,
        broker: str,
        port: int = 1883,
        client_id: str = "MediaPipe_Hand_Controller",
        username: str = "",
        password: str = "",
        keepalive: int = 60,
    ):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keepalive = keepalive

        self.is_connected = False

        # Support paho-mqtt v2.0+ and legacy v1.x
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id,
            )
        else:
            self.client = mqtt.Client(client_id=self.client_id)

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self._setup_callbacks()

    def _setup_callbacks(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                self.is_connected = True
                logger.info(f"Connected to MQTT Broker at {self.broker}:{self.port}")
            else:
                self.is_connected = False
                logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

        def on_disconnect(client, userdata, flags_or_rc, *args):
            self.is_connected = False
            logger.warning("Disconnected from MQTT Broker")

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect

    def start(self):
        """Connects and starts non-blocking background loop."""
        try:
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port} ...")
            self.client.connect(self.broker, self.port, keepalive=self.keepalive)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Error starting MQTT client: {e}")

    def stop(self):
        """Stops background loop and disconnects."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Client stopped.")
        except Exception as e:
            logger.error(f"Error stopping MQTT client: {e}")

    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False) -> bool:
        """
        Publishes a payload to the given topic.
        Returns True if successfully queued, False otherwise.
        """
        if not self.is_connected:
            logger.warning("MQTT not connected yet. Attempting message delivery...")

        try:
            result = self.client.publish(topic, payload=payload, qos=qos, retain=retain)
            # result[0] == 0 means MQTT_ERR_SUCCESS
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published '{payload}' -> [{topic}]")
                return True
            else:
                logger.warning(f"Publish returned error code: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False
