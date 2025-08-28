"""BaseOdaAgentConfigStorage - Abstract base class for agent configuration storage

This module defines the abstract base class for agent configuration storage implementations.
All storage implementations must inherit from this class and implement all abstract methods.
"""

from abc import ABC, abstractmethod

from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig


class BaseOdaAgentConfigStorage(ABC):
    """Abstract base class for agent configuration storage
    
    Defines the unified interface for agent configuration management, which all storage
    implementations must inherit from and implement. This design follows the same pattern
    as ADK's BaseSessionService architecture.
    """
    
    @abstractmethod
    async def create_config(self, config: OdaAgentConfig) -> None:
        """Create a new agent configuration
        
        Args:
            config: The agent configuration object to create
        """
    
    @abstractmethod
    async def get_config(self, agent_name: str) -> OdaAgentConfig | None:
        """Get an agent configuration by its name
        
        Args:
            agent_name: The unique identifier of the agent
            
        Returns:
            The configuration object if found, None otherwise
        """
    
    @abstractmethod
    async def update_config(self, config: OdaAgentConfig) -> None:
        """Update an existing agent configuration
        
        Args:
            config: The agent configuration object with updated values
        """
    
    @abstractmethod
    async def delete_config(self, agent_name: str) -> None:
        """Delete an agent configuration
        
        Args:
            agent_name: The unique identifier of the agent to delete
        """
    
    @abstractmethod
    async def list_configs(self) -> list[OdaAgentConfig]:
        """List all agent configurations
        
        Returns:
            A list containing all configuration objects
        """
    
