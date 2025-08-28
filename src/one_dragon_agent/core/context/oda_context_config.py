"""
Configuration module for OdaContext.

This module contains the runtime configuration classes and factory functions
for creating runtime configurations from environment variables.
"""

import os
from dataclasses import dataclass


@dataclass
class OdaContextConfig:
    """
    Global configuration for OdaContext.
    
    This configuration class holds all the global settings for the OdaContext,
    including default LLM configuration that can be loaded from environment variables.
    
    Attributes:
        storage (str): Storage type, 'memory' or 'mysql'
        default_llm_base_url (str | None): Default base URL for LLM service
        default_llm_api_key (str | None): Default API key for LLM service
        default_llm_model (str | None): Default model name for LLM service
    """
    
    storage: str = "memory"
    default_llm_base_url: str | None = None
    default_llm_api_key: str | None = None
    default_llm_model: str | None = None
    
    @classmethod
    def from_env(cls) -> 'OdaContextConfig':
        """
        Create OdaContextConfig instance from environment variables.
        
        Returns:
            OdaContextConfig: Configuration instance with values from environment variables
        """
        return cls(
            storage=os.getenv('ODA_STORAGE', 'memory'),
            default_llm_base_url=os.getenv('ODA_DEFAULT_LLM_BASE_URL'),
            default_llm_api_key=os.getenv('ODA_DEFAULT_LLM_API_KEY'),
            default_llm_model=os.getenv('ODA_DEFAULT_LLM_MODEL')
        )


