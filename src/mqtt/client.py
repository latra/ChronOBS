import json
from typing import Optional, Callable, Any
import paho.mqtt.client as mqtt
from datetime import datetime

from models.types import MQTTConfig, SyncMessage, ReceivedMessage, MessageCallback, ConnectionCallback
from utils.helpers import format_timestamp


class MQTTManager:
    
    def __init__(self) -> None:
        self._client: Optional[mqtt.Client] = None
        self._is_connected: bool = False
        self._config: Optional[MQTTConfig] = None
        self._on_message_callback: Optional[MessageCallback] = None
        self._on_connection_callback: Optional[ConnectionCallback] = None
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def config(self) -> Optional[MQTTConfig]:
        return self._config
    
    def set_message_callback(self, callback: MessageCallback) -> None:
        self._on_message_callback = callback
    
    def set_connection_callback(self, callback: ConnectionCallback) -> None:
        self._on_connection_callback = callback
    
    def connect(self, config: MQTTConfig) -> None:

        try:
            self._config = config
            self._client = mqtt.Client()
            
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            
            self._client.connect(config.url, config.port, config.keepalive)
            self._client.loop_start()
            
        except Exception as e:
            self._is_connected = False
            raise Exception(f"Error connecting to the MQTT broker: {str(e)}")
    
    def disconnect(self) -> None:

        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        self._is_connected = False
        self._config = None
    
    def subscribe(self, topic: str) -> None:

        if not self._client or not self._is_connected:
            raise RuntimeError("Not connected to the MQTT broker")
        
        self._client.subscribe(topic)
    
    def publish_sync_message(self, room_id: str, username: str) -> SyncMessage:

        if not self._client or not self._is_connected:
            raise RuntimeError("Not connected to the MQTT broker")
        
        sync_message = SyncMessage.create(room_id)
        topic = f"{room_id}/{username}"
        payload = json.dumps({
            "action": "SYNC_REQ"
        })
        
        print(f"[DEBUG] Sending SYNC_REQ:")
        print(f"  Topic: {topic}")
        print(f"  Payload: {payload}")
        
        self._client.publish(topic, payload)
        return sync_message
    
    def publish(self, topic: str, payload: str) -> None:

        if not self._client or not self._is_connected:
            raise RuntimeError("No está conectado al broker MQTT")
        
        self._client.publish(topic, payload)
    
    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: dict, rc: int) -> None:

        self._is_connected = (rc == 0)
        if self._on_connection_callback:
            self._on_connection_callback(self._is_connected)
    
    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:

        self._is_connected = False
        if self._on_connection_callback:
            self._on_connection_callback(False)
    
    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:

        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            timestamp = format_timestamp()
            
            if self._on_message_callback:
                self._on_message_callback(topic, payload, timestamp)
                
        except Exception as e:
            print(f"Error processing MQTT message: {e}") 