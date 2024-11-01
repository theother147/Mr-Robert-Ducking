from typing import Any, Dict, Callable, List
from modules.utils.logger import logger
import functools
from datetime import datetime
from .events import discover_handlers
class Controller:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, '_handlers'):
            self._handlers: Dict[str, List[Callable]] = {}
            
    def trigger(self, event: str, data: Any) -> None:
        """Trigger an event and execute all registered handlers"""
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event}: {e}")
        else:
            logger.debug(f"No handlers registered for event: {event}")
            
    def emits(self, event: str):
        """Decorator that marks a method as an event emitter"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                session_id = result[0]
                data = result[2] if len(result) > 2 else result[1]
                
                self.trigger(event, {
                    'session_id': session_id,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
                
                return result
            return wrapper
        return decorator

    def on(self, event: str):
        """Decorator for registering event handlers"""
        def decorator(func):
            if event not in self._handlers:
                self._handlers[event] = []
            self._handlers[event].append(func)
            return func
        return decorator

# Create singleton instance
controller = Controller()

# Auto-discover event handlers
discover_handlers()
logger.debug("Event handlers discovery completed")
