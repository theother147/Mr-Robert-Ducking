# Description: Configuration file for the server
from typing import Dict

class Config:
    # Server settings
    HOST = "0.0.0.0"
    PORT = 8765
    LOG_LEVEL = "DEBUG"

    # WebSocket settings
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
    MAX_CONNECTIONS = 100
    CONNECTION_TIMEOUT = 60.0
    PING_INTERVAL = None  # Disable ping/pong timeouts
    PING_TIMEOUT = None   # Disable ping/pong timeouts

    # LLM settings
    LLM_MODEL = "codellama"
    LLM_STREAM = False
    LLM_MAX_HISTORY = 100  # Maximum number of messages to keep in history

    # File handling settings
    LANGUAGE_EXTENSIONS: Dict[str, str] = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
    }

    # Message templates
    PROMPT_FILE_HEADER = "\n\nHere are the relevant files:\n\n"
    PROMPT_FILE_FORMAT = "File: {filename}\n```{language}\n{content}\n```\n\n"
    ERROR_INTERNAL = "Internal server error"
    ERROR_MESSAGE_REQUIRED = "Message is required"
    ACK_MESSAGE = "Prompt received and being processed"