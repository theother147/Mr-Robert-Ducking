# Description: Main entry point for the server. Starts the WebSocket server and listens for incoming requests.
import sys
from pathlib import Path

# Add server directory to Python path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

# First, verify and activate virtual environment
from modules.install.install import verify_installation, install_dependencies

def ensure_environment():
    """Ensure we're in the correct environment with all dependencies"""
    try:
        if not verify_installation():
            install_dependencies()
            # If we get here, it means we need to restart in the venv
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(0)

# Run environment check before any other imports
if __name__ == "__main__":
    ensure_environment()

# Only import the rest after environment is verified
import asyncio
from modules.controller.triggers.server_trigger import check_env, start_server, stop_server
from modules.utils.logger import logger

async def cleanup(api=None):
    """Cleanup function to ensure graceful shutdown"""
    if api:
        await stop_server(api)
    logger.info("Server stopped by user.")

async def main():
    api = None
    try:
        # Check environment using emitter
        await check_env()
        
        # Start the server
        result = await start_server()
        api = result[1]['api']
        
        # Run forever
        await asyncio.Future()
        
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await cleanup(api)

async def run_with_cleanup():
    """Run the main coroutine with proper cleanup on cancellation"""
    try:
        await main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt...")

if __name__ == "__main__":
    try:
        asyncio.run(run_with_cleanup())
    except KeyboardInterrupt:
        pass  # Already handled in run_with_cleanup
    except Exception as e:
        logger.error(f"Unexpected error: {e}")