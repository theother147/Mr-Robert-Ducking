from dataclasses import dataclass, field
from typing import List, Dict, TypedDict
from enum import Enum
from modules.config.config import Config

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
    max_size: int = Config.MAX_MESSAGE_SIZE
    max_connections: int = Config.MAX_CONNECTIONS
    timeout: float = Config.CONNECTION_TIMEOUT
    ping_interval: None = Config.PING_INTERVAL
    ping_timeout: None = Config.PING_TIMEOUT

@dataclass
class Session:
    id: str
    messages: List[str] = field(default_factory=list) 