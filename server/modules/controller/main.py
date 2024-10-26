import functools
from typing import Any
from modules.utils import logger


class Controller:
    def __init__(self):
        self.modules = {}
        self.handlers = {}

    def handle_new_request(self, session_id: str, data_type: str, data: Any) -> None:
        logger.info(f"New {data_type} data received for session {session_id}")
        logger.info(f"Data: {data}")
        # Verarbeitung hier

    def send(self, event):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                print(f"sent from decorator {result}")
                

            return wrapper

        return decorator


controller = Controller()


class Test:
    def __init__(self, controller):
        self.controller = controller

    @controller.send(event="audio_received")
    def receive_audio(self):
        print("API empfängt Audiodaten")
        return "AUDIO RECEIVED"


test = Test(controller)

test.receive_audio()
