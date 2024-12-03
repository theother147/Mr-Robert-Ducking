# Description: WebSocket API handling incoming connections and data management
import asyncio
import websockets
import json
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from modules.config.config import Config 
from modules.utils.logger import logger
from .types import ServerConfig
from .message_handler import MessageHandler

class WebSocketAPI:
    _instance = None
    
    def __new__(cls, core=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, core=None):
        if not getattr(self, '_initialized', False):
            if core is None:
                raise ValueError("Core services must be provided for initialization")
            
            logger.info("Initializing WebSocket API")
            self.core = core
            self.message_handler = MessageHandler(
                self.core.session_manager,
                self.core.llm_service
            )
            
            # Initialize server config
            self.server: Optional[websockets.WebSocketServer] = None
            self.config = ServerConfig(
                host=Config.HOST,
                port=Config.PORT
            )
            
            self._initialized = True
            logger.info("WebSocket API initialized")

    async def _initialize_server(self) -> None:
        """Initialize WebSocket server"""
        if not self.server:
            self.server = await websockets.serve(
                self.websocket_handler,
                self.config.host,
                self.config.port,
                max_size=self.config.max_size,
                max_queue=self.config.max_connections,
                ping_interval=None,  # Disable ping/pong timeouts
                ping_timeout=None    # Disable ping/pong timeouts
            )
            logger.info(f"WebSocket server started at ws://{self.config.host}:{self.config.port}")

    async def shutdown(self) -> None:
        """Cleanup server resources"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped.")
            
    async def websocket_handler(self, websocket: websockets.WebSocketServerProtocol, path: str = '/') -> None:
        """Handle incoming WebSocket connections"""
        session_id = self.core.session_manager.create_session()
        logger.info(f"New WebSocket connection established - Session ID: {session_id}")
        
        try:
            while True:
                try:
                    # Receive messages without timeout
                    message = await websocket.recv()
                    
                    if not message:
                        logger.warning(f"Empty message received - Session: {session_id}")
                        continue

                    try:
                        data = json.loads(message)
                        logger.debug(f"Received message: {data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON format - Session {session_id}: {str(e)}")
                        await self.message_handler.send_error(websocket, "Invalid message format", session_id)
                        continue

                    # Process message
                    await self.message_handler.process_message(websocket, session_id, data)

                except websockets.exceptions.ConnectionClosedOK:
                    logger.info(f"Client disconnected normally - Session: {session_id}")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    logger.warning(f"Connection closed with error - Session {session_id}: {str(e)}")
                    break
                except Exception as e:
                    if "no close frame received or sent" in str(e):
                        logger.info(f"Connection closed by client - Session: {session_id}")
                        break
                    logger.error(f"Error receiving message - Session {session_id}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Unexpected error - Session {session_id}: {str(e)}")
        finally:
            try:
                await websocket.close()
            except:
                pass
            self.core.session_manager.close_session(session_id)
            self.message_handler.unregister_connection(session_id)
            logger.info(f"Session closed: {session_id}")

    @asynccontextmanager
    async def server_context(self) -> AsyncGenerator[websockets.WebSocketServer, None]:
        try:
            await self._initialize_server()
            yield self.server
        finally:
            await self.shutdown()

    async def run_server(self):
        async with self.server_context():
            await asyncio.Future()  # Run forever