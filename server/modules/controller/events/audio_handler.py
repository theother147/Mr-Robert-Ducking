# controller/events/audio_handler.py
from modules.controller.main import controller
from modules.utils.logger import logger

@controller.on("audiofile_received")
def handle_audio(data):
    """Handler for received audio data"""
    session_id = data['session_id']
    audio = data['data']
    logger.info(f"Audio handler registered for event: message_received")
    logger.debug(f"[AUDIO HANDLER] Audio received from session {session_id}")