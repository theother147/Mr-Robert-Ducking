# Description: Main entry point for the server. Starts the WebSocket server and listens for incoming requests.
import sys
import asyncio
from pathlib import Path

# Add server directory to Python path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

from modules.utils.logger import logger
from modules.api import WebSocketAPI
from modules.llm.llm import LLM
from modules.api.session import SessionManager

class Core:
    """
    Core application class that manages service initialization and lifecycle
    """
    def __init__(self):
        logger.info("Initializing application core")
        self.llm_service = None
        self.session_manager = None
        
    async def initialize(self):
        """Initialize all core services"""
        logger.info("Starting core services")
        
        # Initialize LLM first as other services depend on it
        self.llm_service = LLM()
        
        # Initialize session management
        self.session_manager = SessionManager()
        
        logger.info("Core services initialized successfully")
        
    async def shutdown(self):
        """Cleanup and shutdown all services"""
        logger.info("Shutting down core services")
        # Add cleanup for services that need it
        self.llm_service = None
        self.session_manager = None

async def cleanup(api=None, core=None):
    """Cleanup function to ensure graceful shutdown"""
    if api:
        await api.shutdown()
    if core:
        await core.shutdown()
    logger.info("Server stopped by user.")

async def main():
    api = None
    core = None
    try:
        # Initialize core services first
        core = Core()
        await core.initialize()
        
        # Start the API with initialized services
        api = WebSocketAPI(core)
        await api.run_server()
        
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await cleanup(api, core)

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