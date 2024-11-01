# Description: Main entry point for the server. Starts the WebSocket server and listens for incoming requests.
import asyncio
from modules.api.main import WebSocketAPI
from modules.controller.main import controller  # Import singleton instance
from modules.utils.logger import logger

async def main():
    api = await WebSocketAPI.get_instance()
    try:
        await asyncio.Future()  # Run forever
    finally:
        await api.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")