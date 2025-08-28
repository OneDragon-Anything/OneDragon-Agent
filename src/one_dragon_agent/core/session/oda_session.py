"""OdaSession - Session Instance Layer

Represents an independent, isolated user conversation session, serving as a 
business wrapper for ADK native components.
"""

import asyncio

from one_dragon_agent.core.agent.oda_agent import OdaAgent
from one_dragon_agent.core.agent.oda_agent_manager import OdaAgentManager
from one_dragon_agent.core.system import log

logger = log.get_logger(__name__)


class OdaSession:
    """Session Instance Layer
    
    Represents an independent, isolated user conversation session, serving as a 
    business wrapper for ADK native components.
    
    Attributes:
        app_name: Application name
        user_id: User identifier
        session_id: Session identifier
        agent_manager: Agent manager instance
        _agent_pool: Pool of cached OdaAgent instances
        _lock: Async lock for thread-safe operations
        _session_state: Session business state and context
    """
    
    def __init__(
        self, 
        app_name: str, 
        user_id: str, 
        session_id: str, 
        agent_manager: OdaAgentManager
    ) -> None:
        """Initialize OdaSession with session identifiers and agent manager
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session identifier
            agent_manager: Agent manager instance
        """
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id
        self.agent_manager = agent_manager
        self._agent_pool: dict[str, OdaAgent] = {}
        self._lock = asyncio.Lock()
        self._session_state: dict = {}
    
    async def process_message(self, message: str, agent_name: str | None = None):
        """Process user message and return async generator of events
        
        Args:
            message: User input message
            agent_name: Optional agent name, uses default if None
            
        Returns:
            AsyncGenerator[Event, None]: Event stream generator from the agent
        """
        if self.agent_manager is None:
            raise RuntimeError("Agent manager not initialized")
        
        async with self._lock:
            # Get or create agent instance
            agent = await self._get_or_create_agent(agent_name or "default")
            
            # Return the async generator directly
            async for event in agent.run_async(message):
                yield event
    
    async def cleanup(self) -> None:
        """Clean up session resources"""
        async with self._lock:
            # Clean up all agents in the pool
            for agent_name, agent in self._agent_pool.items():
                try:
                    await agent.cleanup()
                    logger.info("Cleaned up agent %s for session %s", agent_name, self.session_id)
                except Exception as e:
                    logger.warning("Failed to clean up agent %s for session %s: %s", agent_name, self.session_id, e)
            
            # Clear agent pool
            self._agent_pool.clear()
            self._session_state.clear()
    
    async def _get_or_create_agent(self, agent_name: str) -> OdaAgent:
        """Get or create agent instance from pool
        
        Args:
            agent_name: Name of the agent to get or create
            
        Returns:
            OdaAgent: Agent instance
        """
        # Check if agent exists in pool
        if agent_name in self._agent_pool:
            return self._agent_pool[agent_name]
        
        # Create new agent instance
        agent = await self.agent_manager.create_agent(
            agent_name=agent_name,
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id
        )
        
        # Add to pool
        self._agent_pool[agent_name] = agent
        logger.info("Created agent %s for session %s", agent_name, self.session_id)
        
        return agent