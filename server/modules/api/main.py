# Description: WebSocket API handling incoming connections and data management
import asyncio
import websockets
import json
from uuid import uuid4
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TypedDict, Literal, AsyncGenerator
from enum import Enum
from contextlib import asynccontextmanager

from modules.config.config import Config 
from modules.utils.logger import logger
from modules.controller.main import controller
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

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
    connection_timeout: float = 60.0  # Connection timeout
    ping_interval: float = 20.0  # Keepalive ping interval
    ping_timeout: float = 10.0  # Time to wait for pong response

@dataclass
class Session:
    id: str
    audio_data: List[bytes] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)

class WebSocketAPI:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: ServerConfig = None):
        if not self._initialized:
            self.sessions: Dict[str, Session] = {}
            self.server: Optional[websockets.WebSocketServer] = None
            self.config = config or ServerConfig(
                host=Config.HOST,
                port=Config.PORT
            )
            self._initialized = True

    @classmethod
    async def get_instance(cls) -> 'WebSocketAPI':
        """Get or create singleton instance with initialized server"""
        if cls._instance is None:
            cls._instance = WebSocketAPI()
            await cls._instance._initialize_server()
        return cls._instance

    async def _initialize_server(self) -> None:
        """Initialize WebSocket server with timeout settings"""
        if not self.server:
            self.server = await websockets.serve(
                self.websocket_handler,
                self.config.host,
                self.config.port,
                max_size=self.config.max_size,
                max_queue=self.config.max_connections,
                ping_interval=self.config.ping_interval,
                ping_timeout=self.config.ping_timeout,
                close_timeout=self.config.connection_timeout
            )
            logger.info(f"WebSocket server started at ws://{self.config.host}:{self.config.port}")

    async def shutdown(self) -> None:
        """Cleanup server resources"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped.")

    def create_session(self) -> str:
        session_id = str(uuid4())
        self.sessions[session_id] = Session(id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    @controller.emits("audiofile_received")
    def save_audio_data(self, session_id: str, audio_chunk: bytes) -> tuple[str, str, bytes]:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")
        session.audio_data.append(audio_chunk)
        return (session_id, "audio", audio_chunk)
        
    @controller.emits("message_received")
    def save_message(self, session_id: str, message: str) -> tuple[str, str]:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")
        session.messages.append(message)
        return (session_id, message)

    def close_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} closed.")
        else:
            raise ValueError(f"Session {session_id} not found.")
        
    async def process_message(self, websocket: websockets.WebSocketServerProtocol, session_id: str, data: dict) -> None:
        """Process incoming websocket messages based on type"""
        if "type" not in data:
            await self.send_error(websocket, "Message type not specified", session_id)
            return
            
        if data["type"] == "audio":
            if "audio_chunk" not in data:
                await self.send_error(websocket, "Audio chunk missing", session_id)
                return
            self.save_audio_data(session_id, data["audio_chunk"])
            await self.send_acknowledgement(websocket, "Audio data received", session_id)
            
        elif data["type"] == "text":
            if "message" not in data:
                await self.send_error(websocket, "Text message missing", session_id)
                return
            self.save_message(session_id, data["message"])
            await self.send_acknowledgement(websocket, "Text message received", session_id)
            
        else:
            await self.send_error(websocket, f"Unknown message type: {data['type']}", session_id)
            
    async def websocket_handler(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        session_id = self.create_session()
        logger.info(f"New WebSocket connection established - Session ID: {session_id}")
        
        try:
            while True:
                try:
                    # Set timeout for receiving messages
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=self.config.connection_timeout
                    )
                    
                    if not message:
                        logger.warning(f"Empty message received - Session: {session_id}")
                        continue

                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON format - Session {session_id}: {str(e)}")
                        await self.send_error(websocket, "Invalid message format", session_id)
                        continue

                    # Process message based on type
                    await self.process_message(websocket, session_id, data)

                except asyncio.TimeoutError:
                    logger.warning(f"Connection timeout - Session: {session_id}")
                    await self.send_error(websocket, "Connection timeout", session_id)
                    break

        except ConnectionClosedOK:
            logger.info(f"Client disconnected normally - Session: {session_id}")
        except ConnectionClosedError as e:
            logger.warning(f"Connection closed with error - Session {session_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error - Session {session_id}: {str(e)}")
        finally:
            self.close_session(session_id)
            logger.info(f"Session closed: {session_id}")

    async def send_response(
        self, 
        websocket: websockets.WebSocketServerProtocol,
        message: str,
        session_id: str,
        type: MessageType
    ) -> None:
        """Generic method for sending websocket responses"""
        response: WebSocketResponse = {
            "type": type.value,
            "message": message,
            "session_id": session_id
        }
        log_level = logger.error if type == MessageType.ERROR else logger.info
        log_level(f"Sending {type.value} response: {response}")
        await websocket.send(json.dumps(response))

    async def send_error(self, *args, **kwargs) -> None:
        await self.send_response(*args, type=MessageType.ERROR, **kwargs)

    async def send_acknowledgement(self, *args, **kwargs) -> None:
        await self.send_response(*args, type=MessageType.ACK, **kwargs)

    @asynccontextmanager
    async def server_context(self) -> AsyncGenerator[websockets.WebSocketServer, None]:
        try:
            self.server = await websockets.serve(
                self.websocket_handler,
                self.config.host,
                self.config.port,
                max_size=self.config.max_size,
                max_queue=self.config.max_connections,
                timeout=self.config.timeout
            )
            logger.info(f"WebSocket server started at ws://{self.config.host}:{self.config.port}")
            yield self.server
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup server resources"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped.")

    async def run_server(self):
        async with self.server_context():
            await asyncio.Future()  # Run forever

def run_api() -> None:
    api = WebSocketAPI()
    asyncio.run(api.run_server())

if __name__ == "__main__":
    run_api()