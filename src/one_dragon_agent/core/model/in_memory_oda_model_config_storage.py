"""InMemoryOdaModelConfigStorage - In-memory implementation of model configuration storage

Suitable for development and testing scenarios where persistence is not required.
"""

from one_dragon_agent.core.model.base_oda_model_config_storage import BaseOdaModelConfigStorage
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig


class InMemoryOdaModelConfigStorage(BaseOdaModelConfigStorage):
    """In-memory implementation of OdaModel configuration storage
    
    Stores configurations in memory, suitable for development and testing.
    Data is lost when the process restarts.
    """
    
    def __init__(self) -> None:
        """Initialize the in-memory configuration storage"""
        self._configs: dict[str, OdaModelConfig] = {}
    
    async def create_config(self, config: OdaModelConfig) -> None:
        """Create a new model configuration
        
        Args:
            config: The configuration object to create
        """
        self._configs[config.model_id] = config
    
    async def get_config(self, model_id: str) -> OdaModelConfig | None:
        """Get a model configuration by its ID
        
        Args:
            model_id: The unique identifier of the model
            
        Returns:
            The configuration object if found, None otherwise
        """
        return self._configs.get(model_id)
    
    async def update_config(self, config: OdaModelConfig) -> None:
        """Update an existing model configuration
        
        Args:
            config: The configuration object with updated values
        """
        if config.model_id in self._configs:
            self._configs[config.model_id] = config
    
    async def delete_config(self, model_id: str) -> None:
        """Delete a model configuration
        
        Args:
            model_id: The unique identifier of the model to delete
        """
        self._configs.pop(model_id, None)
    
    async def list_configs(self) -> list[OdaModelConfig]:
        """List all model configurations
        
        Returns:
            A list of all configuration objects
        """
        return list(self._configs.values())