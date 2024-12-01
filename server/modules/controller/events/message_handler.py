# server/modules/controller/events/message_handler.py
from modules.controller.main import controller
from modules.utils.logger import logger

@controller.on("message_received")
def handle_message(data):
    """Handler for received text messages"""
    session_id = data['session_id']
    message = data['data']
    # Add debug logging to verify handler registration
    logger.info(f"Message handler registered for event: message_received")
    logger.debug(f"[MESSAGE HANDLER] Message received from session {session_id}: {message}")