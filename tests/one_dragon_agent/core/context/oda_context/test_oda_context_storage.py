"""Tests for OdaContext storage handling"""

import pytest

from one_dragon_agent.core.context.oda_context import OdaContext
from one_dragon_agent.core.context.oda_context_config import OdaContextConfig


class TestOdaContextStorage:
    """Test cases for OdaContext storage handling"""

    @pytest.mark.asyncio
    async def test_start_with_memory_storage(self) -> None:
        """Test that start method works with memory storage"""
        config = OdaContextConfig(
            storage='memory',
            default_llm_base_url='https://api.openai.com/v1',
            default_llm_api_key='test-key',
            default_llm_model='gpt-3.5-turbo'
        )
        context = OdaContext(config=config)
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
    async def test_start_with_unsupported_storage(self) -> None:
        """Test that start method raises exception with unsupported storage"""
        config = OdaContextConfig(
            storage='mysql',
            default_llm_base_url='https://api.openai.com/v1',
            default_llm_api_key='test-key',
            default_llm_model='gpt-3.5-turbo'
        )
        context = OdaContext(config=config)
        
        # Check that starting with unsupported storage raises an exception
        with pytest.raises(ValueError, match="Storage type 'mysql' is not yet supported"):
            await context.start()