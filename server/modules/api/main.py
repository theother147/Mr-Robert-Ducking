import asyncio
import websockets
import json
from uuid import uuid4

from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional
from contextlib import asynccontextmanager

from modules.config.config import Config 
from modules.utils.logger import logger


@dataclass
class Session:
    id: str
    audio_data: List[bytes] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)

class WebSocketAPI:
    def __init__(self, controller_callback: Callable[[str, str, Any], None]):
        self.sessions: Dict[str, Session] = {}
        self.controller_callback = controller_callback
        self.server: Optional[websockets.WebSocketServer] = None

    def create_session(self) -> str:
        session_id = str(uuid4())
        self.sessions[session_id] = Session(id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    def save_audio_data(self, session_id: str, audio_chunk: bytes) -> None:
        session = self.get_session(session_id)
        if session:
            session.audio_data.append(audio_chunk)
            self._notify_controller(session_id, "audio", audio_chunk)
        else:
            raise ValueError(f"Session {session_id} not found.")

    def save_message(self, session_id: str, message: str) -> None:
        session = self.get_session(session_id)
        if session:
            session.messages.append(message)
            self._notify_controller(session_id, "message", message)
        else:
            raise ValueError(f"Session {session_id} not found.")

    def _notify_controller(self, session_id: str, data_type: str, data: Any) -> None:
        self.controller_callback(session_id, data_type, data)

    def close_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} closed.")
        else:
            raise ValueError(f"Session {session_id} not found.")

    async def websocket_handler(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        session_id = self.create_session()
        logger.info(f"New WebSocket connection, session created with ID: {session_id}")

        try:
            async for message in websocket:
                if not message:
                    logger.warning(f"Empty message received for session {session_id}")
                    continue

                try:
                    data = json.loads(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    await self.send_error(websocket, "Invalid JSON format", session_id)
                    continue

                if "type" not in data:
                    await self.send_error(websocket, "Message type not specified", session_id)
                    continue

                if data["type"] == "audio":
                    if "audio_chunk" not in data:
                        await self.send_error(websocket, "Audio chunk missing", session_id)
                        continue
                    self.save_audio_data(session_id, data["audio_chunk"])
                    await self.send_acknowledgement(websocket, "Audio data received", session_id)

                elif data["type"] == "text":
                    if "message" not in data:
                        await self.send_error(websocket, "Text message missing", session_id)
                        continue
                    self.save_message(session_id, data["message"])
                    await self.send_acknowledgement(websocket, "Text message received", session_id)

                else:
                    await self.send_error(websocket, f"Unknown message type: {data['type']}", session_id)

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Connection closed for session {session_id}: {e}")

        finally:
            self.close_session(session_id)

    async def send_error(self, websocket: websockets.WebSocketServerProtocol, message: str, session_id: str) -> None:
        response = json.dumps({
            "type": "error",
            "message": message,
            "session_id": session_id
        })
        await websocket.send(response)

    async def send_acknowledgement(self, websocket: websockets.WebSocketServerProtocol, message: str, session_id: str) -> None:
        response = json.dumps({
            "type": "ack",
            "message": message,
            "session_id": session_id
        })
        await websocket.send(response)

    @asynccontextmanager
    async def server_context(self):
        try:
            self.server = await websockets.serve(
                self.websocket_handler,
                Config.HOST,
                Config.PORT
            )
            logger.info(f"WebSocket server started at ws://{Config.HOST}:{Config.PORT}")
            yield self.server
        finally:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                logger.info("WebSocket server stopped.")

    async def run_server(self):
        async with self.server_context():
            await asyncio.Future()  # Run forever

def run_api(controller_callback: Callable[[str, str, Any], None]) -> None:
    api = WebSocketAPI(controller_callback)
    asyncio.run(api.run_server())

if __name__ == "__main__":
    def example_callback(session_id: str, data_type: str, data: Any) -> None:
        logger.info(f"Received {data_type} data for session {session_id}")

    run_api(example_callback)