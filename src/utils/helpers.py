import string
import random
from datetime import datetime
from typing import Optional


def generate_room_id(length: int = 5) -> str:

    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


def format_timestamp(dt: Optional[datetime] = None) -> str:

    if dt is None:
        dt = datetime.now()
    return dt.strftime("%H:%M:%S")


def validate_room_id(room_id: str, expected_length: int = 5) -> bool:
    if not room_id:
        return False
    
    room_id = room_id.strip().upper()
    return len(room_id) == expected_length and room_id.isalnum()


def validate_username(username: str, min_length: int = 3, max_length: int = 20) -> bool:

    if not username:
        return False
    
    username = username.strip()
    
    # Verificar longitud
    if len(username) < min_length or len(username) > max_length:
        return False
    
    # Verificar caracteres permitidos: letras, números y guiones
    allowed_chars = string.ascii_letters + string.digits + '-'
    return all(char in allowed_chars for char in username)


def validate_mqtt_config(url: str, port: str) -> tuple[bool, Optional[str]]:

    if not url or not url.strip():
        return False, "The broker URL is required"
    
    if not port or not port.strip():
        return False, "The port is required"
    
    try:
        port_int = int(port)
        if port_int <= 0 or port_int > 65535:
            return False, "The port must be between 1 and 65535"
    except ValueError:
        return False, "The port must be a valid number"
    
    return True, None 