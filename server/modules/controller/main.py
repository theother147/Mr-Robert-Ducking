# Description: Controller module for handling new requests from clients.
from typing import Any
from modules.utils.logger import logger


class Controller:
    def handle_new_request(self, session_id: str, data_type: str, data: Any) -> None:
        logger.info(f"New {data_type} data received for session {session_id}")
        logger.info(f"Data: {data}")
        # Verarbeitung hier