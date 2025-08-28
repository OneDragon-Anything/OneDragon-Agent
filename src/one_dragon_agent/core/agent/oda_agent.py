"""OdaAgent - Agent Adapter Layer

A lightweight wrapper for ADK native Runner instances, providing session isolation
and a consistent interface with ADK Runner while adding error retry mechanisms.
"""

import asyncio
import time
from collections.abc import AsyncGenerator, Generator

from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.genai.types import Content, Part

from one_dragon_agent.core.system import log

logger = log.get_logger(__name__)


class OdaAgent:
    """Agent Adapter Layer
    
    A lightweight wrapper for ADK native Runner instances, providing session isolation
    and a consistent interface with ADK Runner while adding error retry mechanisms.
    
    Attributes:
        runner: ADK native Runner instance
        app_name: Application name for session binding
        user_id: User identifier for session binding
        session_id: Session identifier for session binding
        max_retries: Maximum number of retry attempts
    """
    
    def __init__(
        self, 
        runner: Runner,
        app_name: str, 
        user_id: str, 
        session_id: str, 
        max_retries: int = 3
    ) -> None:
        """Initialize OdaAgent with Runner instance and session identifiers
        
        Args:
            runner: ADK Runner instance
            app_name: Application name
            user_id: User identifier
            session_id: Session identifier
            max_retries: Maximum retry attempts, default is 3
        """
        self.runner = runner
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id
        self.max_retries = max_retries
        self._retry_count = 0
    
    async def run_async(
        self, 
        new_message: str
    ) -> AsyncGenerator[Event, None]:
        """Asynchronously execute agent and return Event stream generator
        
        Provides the same interface as ADK Runner with built-in error retry mechanism:
        - First execution uses original user message, ensuring message is submitted only once
        - Detects execution errors and automatically retries with increasing intervals
        - Does not duplicate user message during retries, resumes from current session state
        - Generates ADK-native standard events to notify retry status
        - Produces final error event after maximum retries exceeded
        
        Args:
            new_message: User message content
            
        Returns:
            AsyncGenerator: Event stream generator
        """
        self._retry_count = 0
        
        while True:
            try:
                # First execution uses original message, retries use None to resume from session state
                if self._retry_count == 0:
                    # Convert string to Content for Runner
                    message_to_use = Content(role="user", parts=[Part(text=new_message)])
                else:
                    message_to_use = None
                
                # Use Runner's run_async method to execute agent
                async for event in self.runner.run_async(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    new_message=message_to_use
                ):
                    yield event
                
                # Successful execution completed, exit loop
                break
                
            except Exception as e:
                # Increment retry count first
                self._retry_count += 1
                
                # Check if maximum retries reached
                if self._retry_count > self.max_retries:
                    # Generate final error event
                    final_error_event = Event(
                        author="system",
                        error_code="MAX_RETRIES_EXCEEDED",
                        error_message=f"Maximum retries exceeded: {e!s}",
                        actions=EventActions(escalate=True)
                    )
                    yield final_error_event
                    break
                
                # Generate retry event (when exception occurs)
                retry_event = Event(
                    author="system",
                    error_code="RETRY_ATTEMPT",
                    error_message=f"Retry attempt {self._retry_count}/{self.max_retries}",
                    actions=EventActions()
                )
                yield retry_event
                
                # Calculate increasing interval (exponential backoff)
                retry_delay = 2 ** (self._retry_count - 1)
                logger.error(
                    f"Agent execution failed, retrying in {retry_delay}s "
                    f"(attempt {self._retry_count}/{self.max_retries}): {e!s}",
                    exc_info=True,
                )
                
                # Wait for retry interval
                await asyncio.sleep(retry_delay)
    
    def run(self, new_message: str) -> Generator[Event, None, None]:
        """Synchronously execute agent and return Event stream generator
        
        Provides the same interface as ADK Runner with built-in error retry mechanism.
        Implements synchronous retry logic with exponential backoff.
        
        Args:
            new_message: User message content
            
        Returns:
            Generator: Event stream generator
        """
        self._retry_count = 0
        
        while True:
            try:
                # First execution uses original message, retries use None to resume from session state
                if self._retry_count == 0:
                    # Convert string to Content for Runner
                    message_to_use = Content(role="user", parts=[Part(text=new_message)])
                else:
                    message_to_use = None
                
                # Use Runner's run method to execute agent
                yield from self.runner.run(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    new_message=message_to_use
                )
                
                # Successful execution completed, exit loop
                break
                
            except Exception as e:
                # Increment retry count first
                self._retry_count += 1
                
                # Check if maximum retries reached
                if self._retry_count > self.max_retries:
                    # Generate final error event
                    final_error_event = Event(
                        author="system",
                        error_code="MAX_RETRIES_EXCEEDED",
                        error_message=f"Maximum retries exceeded: {e!s}",
                        actions=EventActions(escalate=True)
                    )
                    yield final_error_event
                    break
                
                # Generate retry event (when exception occurs)
                retry_event = Event(
                    author="system",
                    error_code="RETRY_ATTEMPT",
                    error_message=f"Retry attempt {self._retry_count}/{self.max_retries}",
                    actions=EventActions()
                )
                yield retry_event
                
                # Calculate increasing interval (exponential backoff)
                retry_delay = 2 ** (self._retry_count - 1)
                logger.warning(
                    f"Agent execution failed, retrying in {retry_delay}s "
                    f"(attempt {self._retry_count}/{self.max_retries}): {e!s}"
                )
                
                # Wait for retry interval (synchronous)
                time.sleep(retry_delay)
    
    async def cleanup(self) -> None:
        """Clean up agent resources"""
        # Clean up Runner resources
        if hasattr(self.runner, 'cleanup'):
            await self.runner.cleanup()
        
        # Reset state
        self._retry_count = 0

    
    def get_agent_info(self) -> dict:
        """Get agent information
        
        Returns:
            dict: Agent information
        """
        return {
            "app_name": self.app_name,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "max_retries": self.max_retries,
            "retry_count": self._retry_count,
        }

    def is_ready(self) -> bool:
        """Check if agent is ready
        
        Returns:
            bool: True if agent is ready, False otherwise
        """
        # Simple implementation, check if runner exists
        return self.runner is not None