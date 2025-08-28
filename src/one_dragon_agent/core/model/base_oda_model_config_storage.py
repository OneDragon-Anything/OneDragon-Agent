"""BaseOdaModelConfigStorage - Abstract base class for model configuration storage

Defines the unified interface for all model configuration storage implementations.
"""

from abc import ABC, abstractmethod

from one_dragon_agent.core.model.oda_model_config import OdaModelConfig


class BaseOdaModelConfigStorage(ABC):
    """Abstract base class for OdaModel configuration storage
    
    Defines the unified interface for all model configuration storage implementations,
    following the same design pattern as ADK's BaseSessionService.
    """
    
    @abstractmethod
    async def create_config(self, config: OdaModelConfig) -> None:
        """Create a new model configuration
        
        Args:
            config: The configuration object to create
        """
    
    @abstractmethod
    async def get_config(self, model_id: str) -> OdaModelConfig | None:
        """Get a model configuration by its ID
        
        Args:
            model_id: The unique identifier of the model
            
        Returns:
            The configuration object if found, None otherwise
        """
    
    @abstractmethod
    async def update_config(self, config: OdaModelConfig) -> None:
        """Update an existing model configuration
        
        Args:
            config: The configuration object with updated values
        """
    
    @abstractmethod
    async def delete_config(self, model_id: str) -> None:
        """Delete a model configuration
        
        Args:
            model_id: The unique identifier of the model to delete
        """
    
    @abstractmethod
    async def list_configs(self) -> list[OdaModelConfig]:
        """List all model configurations
        
        Returns:
            A list of all configuration objects
        """