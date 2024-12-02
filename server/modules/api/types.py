from dataclasses import dataclass, field
from typing import List, Dict, TypedDict
from enum import Enum

class MessageType(Enum):
    ERROR = "error"
    ACK = "ack"

class WebSocketResponse(TypedDict):
    type: str
    message: str
    session_id: str

@dataclass
class ServerConfig:
    host: str
    port: int
    max_size: int = 1024 * 1024  # 1MB max message size
    max_connections: int = 100
    timeout: float = 60.0
    ping_interval: None = None  # Disable ping/pong timeouts
    ping_timeout: None = None   # Disable ping/pong timeouts

@dataclass
class Session:
    id: str
    messages: List[str] = field(default_factory=list) 