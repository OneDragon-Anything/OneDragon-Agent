"""Tests for OdaContext module"""

import os
from unittest.mock import patch

import pytest

from one_dragon_agent.core.context.oda_context import OdaContext
from one_dragon_agent.core.context.oda_context_config import OdaContextConfig


class TestOdaContext:
    """Test cases for OdaContext class"""

    @pytest.mark.asyncio
    async def test_init_with_default_config(self) -> None:
        """Test OdaContext initialization with default config from environment variables"""
        # Mock environment variables
        with patch.dict(os.environ, {
            'ODA_DEFAULT_LLM_BASE_URL': 'https://api.openai.com/v1',
            'ODA_DEFAULT_LLM_API_KEY': 'test-key',
            'ODA_DEFAULT_LLM_MODEL': 'gpt-3.5-turbo'
        }):
            context = OdaContext()
            assert context.config.default_llm_base_url == 'https://api.openai.com/v1'
            assert context.config.default_llm_api_key == 'test-key'
            assert context.config.default_llm_model == 'gpt-3.5-turbo'

    @pytest.mark.asyncio
    async def test_init_with_custom_config(self) -> None:
        """Test OdaContext initialization with custom config"""
        config = OdaContextConfig(
            default_llm_base_url='https://api.openai.com/v1',
            default_llm_api_key='test-key',
            default_llm_model='gpt-3.5-turbo'
        )
        context = OdaContext(config=config)
        assert context.config.default_llm_base_url == 'https://api.openai.com/v1'
        assert context.config.default_llm_api_key == 'test-key'
        assert context.config.default_llm_model == 'gpt-3.5-turbo'

    @pytest.mark.asyncio
    async def test_start_initializes_services(self) -> None:
        """Test that start method initializes all services"""
        context = OdaContext()
        await context.start()
        
        # Check that all services are initialized
        assert context.session_service is not None
        assert context.artifact_service is not None
        assert context.memory_service is not None
        assert context.model_config_manager is not None
        assert context.tool_manager is not None
        assert context.mcp_manager is not None
        assert context.agent_config_manager is not None
        assert context.agent_manager is not None
        assert context.session_manager is not None

    @pytest.mark.asyncio
    async def test_start_initializes_default_model_config(self) -> None:
        """Test that start method initializes default model config when provided"""
        config = OdaContextConfig(
            default_llm_base_url='https://api.openai.com/v1',
            default_llm_api_key='test-key',
            default_llm_model='gpt-3.5-turbo'
        )
        context = OdaContext(config=config)
        await context.start()
        
        # Check that the default config is initialized
        default_config = context.model_config_manager.get_default_config()
        assert default_config is not None
        assert default_config.base_url == 'https://api.openai.com/v1'
        assert default_config.api_key == 'test-key'
        assert default_config.model == 'gpt-3.5-turbo'

    @pytest.mark.asyncio
    async def test_stop_cleans_up_resources(self) -> None:
        """Test that stop method cleans up all resources"""
        context = OdaContext()
        await context.start()
        
        # Ensure services are initialized
        assert context.session_service is not None
        assert context.agent_manager is not None
        assert context.session_manager is not None
        
        # Stop the context
        await context.stop()
        
        # Check that all services are cleaned up
        assert context.session_manager is None
        assert context.agent_manager is None
        assert context.agent_config_manager is None
        assert context.mcp_manager is None
        assert context.tool_manager is None
        assert context.model_config_manager is None
        assert context.session_service is None
        assert context.artifact_service is None
        assert context.memory_service is None