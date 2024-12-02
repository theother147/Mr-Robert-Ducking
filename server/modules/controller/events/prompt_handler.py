# server/modules/controller/events/prompt_handler.py
from modules.controller.main import controller
from modules.utils.logger import logger

@controller.on("prompt_ready")
async def handle_message(event_data):
    """Handler for received text messages"""
    data = event_data.get('data', {})
    session_id = data.get('session_id')
    prompt = data.get('prompt')
    files = data.get('files', [])
    
    # Add debug logging to verify handler registration
    logger.info(f"Message handler registered for event: message_received")
    logger.debug(f"[MESSAGE HANDLER] Message received from session {session_id}: {prompt}")

    # Immediately emit a test response
    logger.info(f"Emitting test response for session: {session_id}")
    await controller.trigger("generate_response", {
        'data': {
            'session_id': session_id,
            'message': f"Test response to: {prompt}"
        }
    })