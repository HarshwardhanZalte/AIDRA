from typing import Dict, Optional
from backend.services.memory_service import SessionData
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class InMemorySessionService:
    """
    A simple in-memory session service to store and retrieve user session data.
    
    In a production system, this would be replaced with Redis, MongoDB, or a
    SQL database for persistence.
    """
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}
        logger.info("InMemorySessionService initialized.")

    def get_session(self, session_id: str) -> SessionData:
        """
        Retrieves a session or creates a new one if it doesn't exist.
        """
        if session_id not in self._sessions:
            logger.info(f"Creating new session: {session_id}")
            self._sessions[session_id] = SessionData(session_id=session_id)
        else:
            logger.debug(f"Retrieving existing session: {session_id}")
            
        return self._sessions[session_id]

    def save_session(self, session_data: SessionData):
        """
        Saves the state of a session.
        """
        self._sessions[session_data.session_id] = session_data
        logger.debug(f"Session saved: {session_data.session_id}")

    def get_all_sessions(self) -> Dict[str, SessionData]:
        """
        Helper method to inspect all current sessions (for debugging).
        """
        return self._sessions

# Create a single, shared instance to be used across the app
# This acts as a singleton.
session_service = InMemorySessionService()