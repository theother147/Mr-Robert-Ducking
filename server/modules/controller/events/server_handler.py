from modules.controller.main import controller
from modules.utils.logger import logger

@controller.on("server_start")
async def handle_server_start(event_data):
    """Handle server start event"""
    data = event_data.get('data', {})
    logger.info("Server is running. Press Ctrl+C to stop.")
    return data.get('api')

@controller.on("server_stop")
async def handle_server_stop(event_data):
    """Handle server stop event"""
    logger.info("Server stopped.") 