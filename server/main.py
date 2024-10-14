# Description: Main entry point for the server. Starts the WebSocket server and listens for incoming requests.
import asyncio
from modules.api.main import WebSocketAPI
from modules.controller.main import Controller
from modules.utils.logger import logger

async def main():
    controller = Controller()
    api = WebSocketAPI(controller.handle_new_request)
    
    async with api.server_context():
        logger.info("Server is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")