import json
import websockets
from typing import Dict, Optional
from modules.utils.logger import logger
from modules.controller.main import controller
from .session import SessionManager
from datetime import datetime

class MessageHandler:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        # Register the response handler
        controller.on("response_generated")(self.handle_response)

    def register_connection(self, session_id: str, websocket: websockets.WebSocketServerProtocol) -> None:
        """Register an active WebSocket connection for a session"""
        self.active_connections[session_id] = websocket

    def unregister_connection(self, session_id: str) -> None:
        """Unregister a WebSocket connection when it's closed"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def handle_response(self, event_data: dict) -> None:
        """Handle AI response and send it to the appropriate session"""
        data = event_data.get('data', {})
        session_id = data.get('session_id')
        message = data.get('message', '')
        
        if not session_id or session_id not in self.active_connections:
            logger.error(f"Cannot send response - Session not found: {session_id}")
            return

        try:
            websocket = self.active_connections[session_id]
            await websocket.send(json.dumps({
                "type": "response",
                "message": message,
                "session_id": session_id
            }))
        except Exception as e:
            logger.error(f"Error sending response to session {session_id}: {str(e)}")

    @controller.emits("prompt_ready")
    async def process_message(self, websocket: websockets.WebSocketServerProtocol, session_id: str, data: dict) -> dict:
        """Process incoming websocket messages"""
        try:
            if "message" not in data:
                await self.send_error(websocket, "Message is required", session_id)
                return {
                    "session_id": session_id,
                    "prompt": "",
                    "files": [],
                    "type": "text",
                    "timestamp": datetime.now().isoformat()
                }
                
            # Format the prompt with any provided files
            prompt = data["message"]
            files = []
            
            if "files" in data and isinstance(data["files"], list):
                files = data["files"]
                prompt += "\n\nHere are the relevant files:\n\n"
                for file in files:
                    # Detect language from filename extension
                    ext = file["filename"].split(".")[-1] if "." in file["filename"] else ""
                    language = {
                        "py": "python",
                        "js": "javascript",
                        "ts": "typescript",
                        "java": "java",
                        "cpp": "cpp",
                        "c": "c",
                    }.get(ext, "")
                    
                    prompt += f"File: {file['filename']}\n"
                    prompt += f"```{language}\n"
                    prompt += f"{file['content']}\n"
                    prompt += "```\n\n"
            
            # Save the formatted prompt
            self.session_manager.save_message(session_id, prompt)
            
            # Register the connection for later response
            self.register_connection(session_id, websocket)
            
            # Send acknowledgment that prompt was received and is being processed
            await self.send_acknowledgement(websocket, "Prompt received and being processed", session_id)
            
            # Return event data
            return {
                "session_id": session_id,
                "prompt": prompt,
                "files": files,
                "type": data.get("type", "text"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(websocket, "Internal server error", session_id)
            return {
                "session_id": session_id,
                "prompt": "",
                "files": [],
                "type": "text",
                "timestamp": datetime.now().isoformat()
            }

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