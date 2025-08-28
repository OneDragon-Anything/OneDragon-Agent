"""OdaSessionManager - Session Lifecycle Manager

Responsible for managing the complete lifecycle of all session instances in the system,
including creation, lookup, update, deletion, and resource management.
"""

import asyncio
import time

from google.adk.sessions import BaseSessionService, Session

from one_dragon_agent.core.agent.oda_agent_manager import OdaAgentManager
from one_dragon_agent.core.system import log

from one_dragon_agent.core.session.oda_session import OdaSession

logger = log.get_logger(__name__)


class OdaSessionManager:
    """Session Lifecycle Manager
    
    The core session management component held by OdaContext, responsible for the 
    complete lifecycle management of all session instances in the system.
    
    Attributes:
        session_service: ADK native session service for data storage
        agent_manager: Agent manager for creating OdaAgent instances
        _session_pool: In-memory cache of active OdaSession instances
        _lock: Async lock for thread-safe operations
        _max_concurrent_sessions: Maximum number of concurrent sessions allowed
        _session_last_access: Track last access time for session cleanup
    """
    
    def __init__(self, session_service: BaseSessionService, agent_manager: OdaAgentManager) -> None:
        """Initialize OdaSessionManager with SessionService and AgentManager instances
        
        Args:
            session_service: ADK native session service instance
            agent_manager: Agent manager instance for creating OdaAgent instances
        """
        self.session_service: BaseSessionService = session_service
        self.agent_manager: OdaAgentManager = agent_manager
        self._session_pool: dict[str, OdaSession] = {}
        self._lock = asyncio.Lock()
        self._max_concurrent_sessions: int | None = None
        self._session_last_access: dict[str, float] = {}
    
    async def create_session(
        self, 
        app_name: str, 
        user_id: str, 
        session_id: str | None = None,
    ) -> OdaSession:
        """Create a new session instance
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Optional session identifier (auto-generated if None)

        Returns:
            OdaSession: Created session instance
        """
        async with self._lock:
            # Check concurrent session limit
            if self._max_concurrent_sessions is not None:
                if len(self._session_pool) >= self._max_concurrent_sessions:
                    raise RuntimeError(f"Maximum concurrent sessions limit ({self._max_concurrent_sessions}) reached")
            
            # Create ADK session
            if session_id is not None:
                adk_session: Session = await self.session_service.create_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )
            else:
                adk_session: Session = await self.session_service.create_session(
                    app_name=app_name,
                    user_id=user_id
                )
            
            # Create OdaSession wrapper with injected agent_manager
            oda_session = OdaSession(
                app_name=app_name,
                user_id=user_id,
                session_id=adk_session.id,
                agent_manager=self.agent_manager
            )
            
            # Add to session pool
            session_key = self._get_session_key(app_name, user_id, adk_session.id)
            self._session_pool[session_key] = oda_session
            self._session_last_access[session_key] = time.time()
            
            logger.info("Created session: %s for user %s in app %s", adk_session.id, user_id, app_name)
            return oda_session
    
    async def get_session(
        self, 
        app_name: str, 
        user_id: str, 
        session_id: str
    ) -> OdaSession | None:
        """Get a specific session instance
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            OdaSession: Session instance or None if not found
        """
        async with self._lock:
            session_key = self._get_session_key(app_name, user_id, session_id)
            session = self._session_pool.get(session_key)
            if session:
                self._session_last_access[session_key] = time.time()
            return session
    
    async def list_sessions(
        self, 
        app_name: str, 
        user_id: str
    ) -> list[OdaSession]:
        """List all session instances for a user
        
        Args:
            app_name: Application name
            user_id: User identifier
            
        Returns:
            List[OdaSession]: List of session instances
        """
        async with self._lock:
            sessions = []
            for key, session in self._session_pool.items():
                key_parts = key.split(":")
                if len(key_parts) == 3 and key_parts[0] == app_name and key_parts[1] == user_id:
                    sessions.append(session)
            return sessions
    
    async def delete_session(
        self, 
        app_name: str, 
        user_id: str, 
        session_id: str
    ) -> None:
        """Delete a specific session instance
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session identifier
        """
        async with self._lock:
            session_key = self._get_session_key(app_name, user_id, session_id)
            
            # Clean up OdaSession resources
            if session_key in self._session_pool:
                oda_session = self._session_pool[session_key]
                await oda_session.cleanup()
            
            # Remove from session pool
            self._session_pool.pop(session_key, None)
            self._session_last_access.pop(session_key, None)
            
            # Delete ADK session
            await self.session_service.delete_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            logger.info("Deleted session: %s for user %s in app %s", session_id, user_id, app_name)
    
    async def cleanup_inactive_sessions(self, timeout_seconds: int) -> None:
        """Clean up inactive session instances
        
        Args:
            timeout_seconds: Session timeout in seconds
        """
        current_time = time.time()
        expired_sessions = []
        
        async with self._lock:
            # Find expired sessions
            for session_key, last_access in self._session_last_access.items():
                if current_time - last_access > timeout_seconds:
                    expired_sessions.append(session_key)
            
            # Clean up expired sessions
            for session_key in expired_sessions:
                # Extract session identifiers from key
                key_parts = session_key.split(":")
                if len(key_parts) == 3:
                    app_name, user_id, session_id = key_parts
                    
                    # Clean up OdaSession resources
                    if session_key in self._session_pool:
                        oda_session = self._session_pool[session_key]
                        await oda_session.cleanup()
                    
                    # Remove from session pool
                    self._session_pool.pop(session_key, None)
                    self._session_last_access.pop(session_key, None)
                    
                    # Delete ADK session
                    try:
                        await self.session_service.delete_session(
                            app_name=app_name,
                            user_id=user_id,
                            session_id=session_id
                        )
                        logger.info("Cleaned up expired session: %s for user %s in app %s", session_id, user_id, app_name)
                    except Exception as e:
                        logger.warning("Failed to delete expired ADK session %s: %s", session_id, e)
    
    async def set_concurrent_limit(self, max_concurrent_sessions: int) -> None:
        """Set concurrent session limit
        
        Args:
            max_concurrent_sessions: Maximum concurrent sessions allowed
        """
        async with self._lock:
            self._max_concurrent_sessions = max_concurrent_sessions
    
    def _get_session_key(self, app_name: str, user_id: str, session_id: str) -> str:
        """Generate a unique key for session identification
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            str: Unique session key
        """
        return f"{app_name}:{user_id}:{session_id}"