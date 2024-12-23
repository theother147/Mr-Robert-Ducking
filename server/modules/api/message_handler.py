# Message handler module for processing WebSocket messages and managing client communication.
# Handles message routing, file processing, and response generation.

import json
import websockets
from typing import Dict, Optional
from modules.utils.logger import logger
from modules.config.config import Config
from .session import SessionManager
from datetime import datetime

class MessageHandler:
    """
    Handles processing and routing of WebSocket messages.
    Manages active connections and coordinates with LLM service for response generation.
    """
    def __init__(self, session_manager: SessionManager, llm_service):
        """
        Initialize message handler with required services
        @param session_manager: Manager for client sessions
        @param llm_service: Service for LLM interactions
        """
        self.session_manager = session_manager
        self.llm_service = llm_service
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}

    def register_connection(self, session_id: str, websocket: websockets.WebSocketServerProtocol) -> None:
        """
        Register an active WebSocket connection for a session
        @param session_id: Unique identifier for the session
        @param websocket: WebSocket connection to register
        """
        self.active_connections[session_id] = websocket

    def unregister_connection(self, session_id: str) -> None:
        """
        Unregister a WebSocket connection when it's closed
        @param session_id: ID of the session to unregister
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def process_message(self, websocket: websockets.WebSocketServerProtocol, session_id: str, data: dict) -> None:
        """
        Process incoming websocket messages and generate responses
        @param websocket: Active WebSocket connection
        @param session_id: Current session identifier
        @param data: Message data to process
        """
        try:
            # Validate required message field
            if "message" not in data:
                await self.send_error(websocket, Config.ERROR_MESSAGE_REQUIRED, session_id)
                return
                
            # Extract message content and prepare for processing
            prompt = data["message"]
            files = []
            
            # Process attached files if present
            if "files" in data and isinstance(data["files"], list) and data["files"]:
                files = data["files"]
                prompt += Config.PROMPT_FILE_HEADER
                for file in files:
                    # Validate file data structure
                    if not isinstance(file, dict) or 'filename' not in file or 'content' not in file:
                        continue
                    # Extract language from file extension
                    ext = file["filename"].split(".")[-1] if "." in file["filename"] else ""
                    language = Config.LANGUAGE_EXTENSIONS.get(ext, "")
                    
                    # Format file content into prompt
                    prompt += Config.PROMPT_FILE_FORMAT.format(
                        filename=file['filename'],
                        language=language,
                        content=file['content']
                    )
            
            # Save the formatted prompt to session history
            self.session_manager.save_message(session_id, prompt)
            
            # Register connection for response delivery
            self.register_connection(session_id, websocket)
            
            # Optional acknowledgment of message receipt
            #await self.send_acknowledgement(websocket, Config.ACK_MESSAGE, session_id)
            
            # Generate response using LLM service
            response = await self.llm_service.generate_response(session_id, prompt)
            
            # Send response to client
            await websocket.send(json.dumps({
                "type": "response",
                "message": response["message"],
                "session_id": session_id
            }))
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(websocket, Config.ERROR_INTERNAL, session_id)

    async def send_error(self, websocket: websockets.WebSocketServerProtocol, message: str, session_id: str) -> None:
        """
        Send error message to client
        @param websocket: Active WebSocket connection
        @param message: Error message to send
        @param session_id: Current session identifier
        """
        response = {
            "type": "error",
            "message": message,
            "session_id": session_id
        }
        logger.error(f"Sending error response: {response}")
        await websocket.send(json.dumps(response))

    async def send_acknowledgement(self, websocket: websockets.WebSocketServerProtocol, message: str, session_id: str) -> None:
        """
        Send acknowledgement message to client
        @param websocket: Active WebSocket connection
        @param message: Acknowledgement message to send
        @param session_id: Current session identifier
        """
        response = {
            "type": "ack",
            "message": message,
            "session_id": session_id
        }
        logger.info(f"Sending acknowledgement: {response}")
        await websocket.send(json.dumps(response)) 