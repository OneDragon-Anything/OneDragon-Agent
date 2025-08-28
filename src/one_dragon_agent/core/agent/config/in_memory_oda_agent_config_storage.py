"""InMemoryOdaAgentConfigStorage - In-memory implementation of agent configuration storage

This module provides an in-memory implementation of the agent configuration storage
interface, suitable for development and testing scenarios.
"""


from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager

from one_dragon_agent.core.agent.config.base_oda_agent_config_storage import (
    BaseOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig


class InMemoryOdaAgentConfigStorage(BaseOdaAgentConfigStorage):
    """In-memory implementation of agent configuration storage
    
    This implementation stores agent configurations in memory and is suitable for
    development and testing scenarios. Data will be lost when the process restarts.
    """
    
    def __init__(self, model_config_manager: OdaModelConfigManager) -> None:
        """Initialize the in-memory agent configuration storage
        
        Args:
            model_config_manager: The model configuration manager for validating model configurations
        """
        self._configs: dict[str, OdaAgentConfig] = {}
        self.model_config_manager = model_config_manager
    
    async def create_config(self, config: OdaAgentConfig) -> None:
        """Create a new agent configuration
        
        Args:
            config: The agent configuration object to create
            
        Raises:
            ValueError: If a configuration with the same agent_name already exists
        """
        if config.agent_name in self._configs:
            raise ValueError(f"Agent configuration with name '{config.agent_name}' already exists")
        
        self._configs[config.agent_name] = config
    
    async def get_config(self, agent_name: str) -> OdaAgentConfig | None:
        """Get an agent configuration by its name
        
        Args:
            agent_name: The unique identifier of the agent
            
        Returns:
            The configuration object if found, None otherwise
        """
        return self._configs.get(agent_name)
    
    async def update_config(self, config: OdaAgentConfig) -> None:
        """Update an existing agent configuration
        
        Args:
            config: The agent configuration object with updated values
        """
        # Check if the configuration exists
        if config.agent_name not in self._configs:
            raise ValueError(f"Agent configuration with name '{config.agent_name}' does not exist")
        
        self._configs[config.agent_name] = config
    
    async def delete_config(self, agent_name: str) -> None:
        """Delete an agent configuration
        
        Args:
            agent_name: The unique identifier of the agent to delete
        """
        self._configs.pop(agent_name, None)
    
    async def list_configs(self) -> list[OdaAgentConfig]:
        """List all agent configurations
        
        Returns:
            A list containing all configuration objects
        """
        return list(self._configs.values())
    
