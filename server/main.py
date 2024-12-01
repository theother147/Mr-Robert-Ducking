# Description: Main entry point for the server. Starts the WebSocket server and listens for incoming requests.
import asyncio
import sys
from pathlib import Path

# Add server directory to Python path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

from modules.controller.triggers.server_trigger import check_env, start_server, stop_server
from modules.utils.logger import logger

async def main():
    try:
        # Check environment using emitter
        await check_env()
        
        # Start the server
        result = await start_server()
        api = result[1]['api']
        
        # Run forever
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if 'api' in locals():
            await stop_server(api)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")