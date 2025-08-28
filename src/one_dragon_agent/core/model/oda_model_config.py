"""OdaModelConfig - Configuration data class for AI models

This module defines the OdaModelConfig data class, which encapsulates all the necessary
configuration parameters for AI model services. It follows the dataclass pattern for
concise and maintainable configuration management.
"""

from dataclasses import dataclass


@dataclass
class OdaModelConfig:
    """Configuration data class for AI models
    
    This data class holds all the necessary configuration parameters for AI model services.
    It provides a structured way to manage model configurations with type hints for clarity
    and maintainability.
    
    Attributes:
        app_name (str): Application name identifier, used to distinguish configurations
                       for different applications. Follows the same definition as in adk-python.
        model_id (str): Unique identifier for the model configuration. This should be unique
                       within the scope of an app_name.
        base_url (str): Base URL for the AI model API service endpoint.
        api_key (str): API key for authenticating with the AI model service.
        model (str): The specific model name to be used for API calls.
    """
    
    app_name: str
    model_id: str
    base_url: str
    api_key: str
    model: str
