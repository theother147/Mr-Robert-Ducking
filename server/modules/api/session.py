from uuid import uuid4
from typing import Optional, Dict
from modules.utils.logger import logger
from .types import Session

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def create_session(self) -> str:
        """Create a new session and return its ID"""
        session_id = str(uuid4())
        self.sessions[session_id] = Session(id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by its ID"""
        return self.sessions.get(session_id)
    
    def save_message(self, session_id: str, message: str) -> None:
        """Save a message to a session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")
        session.messages.append(message)

    def close_session(self, session_id: str) -> None:
        """Close and cleanup a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} closed.")
        else:
            raise ValueError(f"Session {session_id} not found.") 