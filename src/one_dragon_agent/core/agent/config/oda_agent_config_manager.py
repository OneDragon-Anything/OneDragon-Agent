"""OdaAgentConfigManager - Agent Configuration Manager

Provides service injection and unified interface for agent configuration management.
"""


from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager

from one_dragon_agent.core.agent.config.base_oda_agent_config_storage import (
    BaseOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig, create_default_agent_config


class OdaAgentConfigManager:
    """Agent Configuration Manager
    
    Provides service injection and unified interface for agent configuration management,
    supporting different storage implementations through dependency injection.
    
    The manager integrates with OdaModelConfigManager and OdaMcpManager to validate
    agent configurations and ensure referential integrity.
    """
    
    def __init__(
        self,
        config_service: BaseOdaAgentConfigStorage,
        model_config_manager: OdaModelConfigManager,
        mcp_manager: OdaMcpManager,
    ) -> None:
        """Initialize the agent configuration manager
        
        Args:
            config_service: Configuration storage service, can be any implementation
                           inheriting from BaseOdaAgentConfigStorage
            model_config_manager: Model configuration manager for validating model configurations
            mcp_manager: MCP manager for validating MCP configurations
        """
        self.config_service = config_service
        self.model_config_manager = model_config_manager
        self.mcp_manager = mcp_manager
        self._default_config = None
    
    async def create_config(self, config: OdaAgentConfig) -> None:
        """Create a new agent configuration
        
        Creates a persistent agent configuration that will be stored in the underlying service.
        The configuration will be validated to ensure all referenced model and MCP configurations
        exist and are valid.
        
        Args:
            config: The agent configuration object to create
            
        Raises:
            ValueError: If the configuration is invalid or references non-existent configurations
        """
        # Prevent creating built-in default configuration
        if config.agent_name == "default":
            raise ValueError("Cannot create built-in default configuration")
        
        # Validate model configuration
        if not await self.validate_model_config(config.app_name, config.model_config):
            raise ValueError(f"Invalid model configuration: {config.model_config}")
        
        # Validate MCP configurations
        if not await self.validate_mcp_config(config.app_name, config.mcp_list):
            raise ValueError(f"Invalid MCP configuration in mcp_list: {config.mcp_list}")
        
        # Create the configuration
        await self.config_service.create_config(config)
    
    async def get_config(self, agent_name: str) -> OdaAgentConfig | None:
        """Get an agent configuration by its name
        
        Args:
            agent_name: The unique identifier of the agent
            
        Returns:
            The configuration object if found, None otherwise
        """
        # Check if requesting the default agent
        if agent_name == "default":
            # Lazy load the default configuration
            if self._default_config is None:
                self._default_config = create_default_agent_config("default")
            return self._default_config
        
        # Get persistent configuration from storage service
        return await self.config_service.get_config(agent_name)
    
    async def update_config(self, config: OdaAgentConfig) -> None:
        """Update an existing agent configuration
        
        Updates a persistent agent configuration. The configuration will be validated
        to ensure all referenced model and MCP configurations exist and are valid.
        
        Args:
            config: The agent configuration object with updated values
            
        Raises:
            ValueError: If the configuration is invalid or references non-existent configurations
        """
        # Prevent updating built-in default configuration
        if config.agent_name == "default":
            raise ValueError("Cannot update built-in default configuration")
        
        # Validate model configuration
        if not await self.validate_model_config(config.app_name, config.model_config):
            raise ValueError(f"Invalid model configuration: {config.model_config}")
        
        # Validate MCP configurations
        if not await self.validate_mcp_config(config.app_name, config.mcp_list):
            raise ValueError(f"Invalid MCP configuration in mcp_list: {config.mcp_list}")
        
        # Update the configuration
        await self.config_service.update_config(config)
    
    async def delete_config(self, agent_name: str) -> None:
        """Delete an agent configuration
        
        Args:
            agent_name: The unique identifier of the agent to delete
        """
        # Prevent deleting built-in default configuration
        if agent_name == "default":
            raise ValueError("Cannot delete built-in default configuration")
        
        await self.config_service.delete_config(agent_name)
    
    async def list_configs(self) -> list[OdaAgentConfig]:
        """List all agent configurations
        
        Returns:
            A list containing all persistent configuration objects (excluding built-in default)
        """
        return await self.config_service.list_configs()
    
    async def validate_model_config(self, app_name: str, model_config: str) -> bool:
        """Validate if a model configuration is valid
        
        Args:
            app_name: The application name
            model_config: The model configuration identifier to validate
            
        Returns:
            True if the model configuration is valid, False otherwise
        """
        return await self.model_config_manager.validate_model_config(app_name, model_config)
    
    async def validate_mcp_config(self, app_name: str, mcp_list: list[str]) -> bool:
        """Validate if all MCP configurations in the list are valid
        
        Args:
            app_name: The application name
            mcp_list: The list of MCP configuration identifiers to validate
            
        Returns:
            True if all MCP configurations are valid, False otherwise
        """
        # Check each MCP configuration in the list
        for mcp_id in mcp_list:
            config = await self.mcp_manager.get_mcp_config(app_name, mcp_id)
            if config is None:
                return False
        return True
    
    def is_built_in_config(self, agent_name: str) -> bool:
        """Check if agent name corresponds to a built-in configuration
        
        Args:
            agent_name: The agent name to check
            
        Returns:
            True if the agent name is a built-in configuration, False otherwise
        """
        return agent_name == "default"