from typing import Dict, Optional, Protocol, Any, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class AppView(Enum):
    """Enumeración de vistas de la aplicación"""
    CONNECTION = "connection"
    MODE_SELECTION = "mode_selection"
    PRODUCER = "producer"
    OBSERVER = "observer"


class ConnectionStatus(Enum):
    """Estados de conexión MQTT"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MQTTConfig:
    """Configuración de conexión MQTT"""
    url: str
    port: int
    keepalive: int = 60


@dataclass
class SyncMessage:
    """Mensaje de sincronización"""
    type: str

    @classmethod
    def create(cls, room_id: str) -> 'SyncMessage':
        """Crear un nuevo mensaje de sincronización"""
        return cls(
            type="SYNC_REQ",
        )


@dataclass
class ReceivedMessage:
    """Mensaje recibido por MQTT"""
    topic: str
    payload: str
    timestamp: str


class StyleColors:
    """Colores del tema de la aplicación"""
    BG_PRIMARY = '#1a1a2e'
    BG_SECONDARY = '#16213e'
    BG_ACCENT = '#0f3460'
    PURPLE_PRIMARY = '#9b59b6'
    PURPLE_SECONDARY = '#8e44ad'
    PURPLE_LIGHT = '#bb86fc'
    TEXT_PRIMARY = '#ffffff'
    TEXT_SECONDARY = '#b3b3b3'


class MQTTClientProtocol(Protocol):
    """Protocol para el cliente MQTT"""
    def connect(self, host: str, port: int, keepalive: int) -> None: ...
    def disconnect(self) -> None: ...
    def loop_start(self) -> None: ...
    def loop_stop(self) -> None: ...
    def subscribe(self, topic: str) -> None: ...
    def publish(self, topic: str, payload: str) -> None: ...


# Type aliases
MessageCallback = Callable[[str, str, str], None]
ConnectionCallback = Callable[[bool], None] 