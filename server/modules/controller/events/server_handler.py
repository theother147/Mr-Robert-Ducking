from modules.controller.main import controller
from modules.utils.logger import logger

@controller.on("server_start")
async def handle_server_start(data):
    """Handle server start event"""
    logger.info("Server is running. Press Ctrl+C to stop.")
    return data.get('data', {}).get('api')

@controller.on("server_stop")
async def handle_server_stop(data):
    """Handle server stop event"""
    logger.info("Server stopped.") 