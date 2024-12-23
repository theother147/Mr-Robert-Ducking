"""
Session management module for handling client sessions.
Provides functionality for creating, tracking, and managing client sessions
and their associated message history.
"""

from uuid import uuid4
from typing import Optional, Dict
from modules.utils.logger import logger
from .types import Session

class SessionManager:
    """
    Manages client sessions and their associated data.
    Handles session lifecycle including creation, retrieval, and cleanup.
    """
    def __init__(self):
        """Initialize the session manager with an empty session store"""
        self.sessions: Dict[str, Session] = {}

    def create_session(self) -> str:
        """
        Create a new session and return its ID
        @returns: Unique identifier for the new session
        """
        session_id = str(uuid4())
        self.sessions[session_id] = Session(id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by its ID
        @param session_id: ID of the session to retrieve
        @returns: Session object if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    def save_message(self, session_id: str, message: str) -> None:
        """
        Save a message to a session's history
        @param session_id: ID of the session to save to
        @param message: Message content to save
        @raises ValueError: If session is not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")
        session.messages.append(message)

    def close_session(self, session_id: str) -> None:
        """
        Close and cleanup a session
        @param session_id: ID of the session to close
        @raises ValueError: If session is not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} closed.")
        else:
            raise ValueError(f"Session {session_id} not found.") 