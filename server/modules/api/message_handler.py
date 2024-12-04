import json
import websockets
from typing import Dict, Optional
from modules.utils.logger import logger
from modules.config.config import Config
from .session import SessionManager
from datetime import datetime

class MessageHandler:
    def __init__(self, session_manager: SessionManager, llm_service):
        self.session_manager = session_manager
        self.llm_service = llm_service
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}

    def register_connection(self, session_id: str, websocket: websockets.WebSocketServerProtocol) -> None:
        """Register an active WebSocket connection for a session"""
        self.active_connections[session_id] = websocket

    def unregister_connection(self, session_id: str) -> None:
        """Unregister a WebSocket connection when it's closed"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def process_message(self, websocket: websockets.WebSocketServerProtocol, session_id: str, data: dict) -> None:
        """Process incoming websocket messages"""
        try:
            if "message" not in data:
                await self.send_error(websocket, Config.ERROR_MESSAGE_REQUIRED, session_id)
                return
                
            # Format the prompt with any provided files
            prompt = data["message"]
            files = []
            
            if "files" in data and isinstance(data["files"], list):
                files = data["files"]
                prompt += Config.PROMPT_FILE_HEADER
                for file in files:
                    # Detect language from filename extension
                    ext = file["filename"].split(".")[-1] if "." in file["filename"] else ""
                    language = Config.LANGUAGE_EXTENSIONS.get(ext, "")
                    
                    prompt += Config.PROMPT_FILE_FORMAT.format(
                        filename=file['filename'],
                        language=language,
                        content=file['content']
                    )
            
            # Save the formatted prompt
            self.session_manager.save_message(session_id, prompt)
            
            # Register the connection for later response
            self.register_connection(session_id, websocket)
            
            # Send acknowledgment that prompt was received and is being processed
            await self.send_acknowledgement(websocket, Config.ACK_MESSAGE, session_id)
            
            # Get response from LLM
            response = await self.llm_service.generate_response(session_id, prompt, files)
            
            # Send response back to client
            await websocket.send(json.dumps({
                "type": "response",
                "message": response["message"],
                "session_id": session_id
            }))
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(websocket, Config.ERROR_INTERNAL, session_id)

    async def send_error(self, websocket: websockets.WebSocketServerProtocol, message: str, session_id: str) -> None:
        """Send error message to client"""
        response = {
            "type": "error",
            "message": message,
            "session_id": session_id
        }
        logger.error(f"Sending error response: {response}")
        await websocket.send(json.dumps(response))

    async def send_acknowledgement(self, websocket: websockets.WebSocketServerProtocol, message: str, session_id: str) -> None:
        """Send acknowledgement message to client"""
        response = {
            "type": "ack",
            "message": message,
            "session_id": session_id
        }
        logger.info(f"Sending acknowledgement: {response}")
        await websocket.send(json.dumps(response)) 