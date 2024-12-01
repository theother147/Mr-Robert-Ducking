# controller/events/__init__.py
from pathlib import Path
from importlib import import_module
from modules.utils.logger import logger

def discover_handlers() -> None:
    """Auto-discover and import all event handlers"""
    events_dir = Path(__file__).parent
    logger.debug(f"Discovering handlers in: {events_dir}")
    
    for file in events_dir.glob("*_handler.py"):
        if file.stem != "__init__":
            module_name = f"modules.controller.events.{file.stem}"
            logger.debug(f"Importing handler module: {module_name}")
            import_module(module_name)