"""OdaModelConfigManager - Model Configuration Manager

Provides service injection and unified interface for model configuration management.
"""

from one_dragon_agent.core.context.oda_context_config import OdaContextConfig

from one_dragon_agent.core.model.base_oda_model_config_storage import (
    BaseOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig

# Special ID for default LLM configuration
DEFAULT_LLM_CONFIG_ID = "__default_llm_config"


class OdaModelConfigManager:
    """Model Configuration Manager
    
    Provides service injection and unified interface for model configuration management,
    supporting different storage implementations through dependency injection.
    
    The manager supports both persistent configurations and a special default configuration
    that is loaded from OdaContextConfig at initialization time.
    """
    
    def __init__(self, config_service: BaseOdaModelConfigStorage, context_config: OdaContextConfig) -> None:
        """Initialize the model configuration manager
        
        Initializes the configuration manager and creates a default configuration instance
        from the injected OdaContextConfig if all required default LLM settings are present.
        The default configuration is cached in memory for efficient access.
        
        Args:
            config_service: Configuration service instance, can be any implementation
                           inheriting from BaseOdaModelConfigService
            context_config: Context configuration object containing default LLM settings
                           loaded from environment variables
        """
        self.config_service = config_service
        self._default_config: OdaModelConfig | None = None
        
        # Create default config from context config if all required fields are present
        if (context_config.default_llm_base_url and 
            context_config.default_llm_api_key and 
            context_config.default_llm_model):
            self._default_config = OdaModelConfig(
                app_name="__default_app",
                model_id=DEFAULT_LLM_CONFIG_ID,
                base_url=context_config.default_llm_base_url,
                api_key=context_config.default_llm_api_key,
                model=context_config.default_llm_model
            )
    
    async def create_config(self, config: OdaModelConfig) -> None:
        """Create a new model configuration
        
        Creates a persistent model configuration that will be stored in the underlying service.
        Default configuration cannot be created through this method as it is generated from
        environment variables.
        
        Args:
            config: The configuration object to create
            
        Raises:
            ValueError: If attempting to create a configuration with the default config ID
        """
        if config.model_id == DEFAULT_LLM_CONFIG_ID:
            raise ValueError("Default configuration cannot be created manually. "
                           "It is automatically generated from environment variables.")
        
        await self.config_service.create_config(config)
    
    async def get_config(self, model_id: str) -> OdaModelConfig | None:
        """Get a model configuration by its ID
        
        Supports retrieving both persistent configurations and the default configuration.
        When requesting the default configuration ID, returns the cached default configuration
        instance without performing a persistent lookup.
        
        Args:
            model_id: The unique identifier of the model, supports the special default 
                     configuration ID "__default_llm_config"
            
        Returns:
            The configuration object if found, None otherwise
            
        Note:
            The default configuration ID "__default_llm_config" is a reserved ID used to
            identify the environment variable-based default configuration.
        """
        # Return default config directly if requested
        if model_id == DEFAULT_LLM_CONFIG_ID:
            return self._default_config
        
        # Otherwise delegate to the config service
        return await self.config_service.get_config(model_id)
    
    def get_default_config(self) -> OdaModelConfig | None:
        """Get the default model configuration
        
        Returns the cached default configuration instance directly without any persistent
        operations. The default configuration is created once during manager initialization
        from the injected OdaContextConfig, which reads settings from environment variables
        ODA_DEFAULT_LLM_BASE_URL, ODA_DEFAULT_LLM_API_KEY, and ODA_DEFAULT_LLM_MODEL.
        
        Returns:
            The default configuration object if available, None otherwise
            
        Note:
            This method returns the cached instance directly for high performance and
            is suitable for frequent calls to retrieve the default configuration.
        """
        return self._default_config
    
    async def update_config(self, config: OdaModelConfig) -> None:
        """Update an existing model configuration
        
        Updates a persistent model configuration. The default configuration cannot be
        updated through this method as it is based on OdaContextConfig and requires
        environment variable changes and system restart to update.
        
        Args:
            config: The configuration object with updated values
            
        Raises:
            ValueError: If attempting to update the default configuration
        """
        if config.model_id == DEFAULT_LLM_CONFIG_ID:
            raise ValueError("Default configuration cannot be updated manually. "
                           "Update it through environment variables and restart the system.")
        
        await self.config_service.update_config(config)
    
    async def delete_config(self, model_id: str) -> None:
        """Delete a model configuration
        
        Deletes a persistent model configuration. The default configuration cannot be
        deleted as it is a system-level configuration based on OdaContextConfig.
        
        Args:
            model_id: The unique identifier of the model to delete
            
        Raises:
            ValueError: If attempting to delete the default configuration
        """
        if model_id == DEFAULT_LLM_CONFIG_ID:
            raise ValueError("Default configuration cannot be deleted as it is a system-level configuration.")
        
        await self.config_service.delete_config(model_id)
    
    async def validate_model_config(self, app_name: str, model_config: str) -> bool:
        """Validate if a model configuration is valid
        
        Args:
            app_name: The application name
            model_config: The model configuration identifier to validate
            
        Returns:
            True if the model configuration is valid, False otherwise
        """
        # Check if the model configuration exists
        config = await self.get_config(model_config)
        if config is None:
            return False
            
        # Special case for default model configuration - it can be used by any app
        if model_config == DEFAULT_LLM_CONFIG_ID:
            return True
            
        # For other configurations, check if the app_name matches
        return config.app_name == app_name
    
    async def list_configs(self) -> list[OdaModelConfig]:
        """List all model configurations
        
        Returns all available model configurations in the system, including:
        - Persistent configurations: Custom configurations created through create_config
        - Built-in default configuration: Generated from OdaContextConfig if available
        
        Returns:
            A list containing all configuration objects, with the default configuration
            always appearing at the end of the list if it exists
            
        Note:
            This method provides a complete view of all configurations and is useful
            for upper-level applications to understand all available model configurations.
        """
        # Get all persistent configurations
        configs = await self.config_service.list_configs()
        
        # Add default configuration if it exists
        if self._default_config:
            configs.append(self._default_config)
        
        return configs