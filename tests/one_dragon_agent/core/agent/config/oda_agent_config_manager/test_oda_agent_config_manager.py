"""Tests for OdaAgentConfigManager"""

from unittest.mock import AsyncMock, Mock

import pytest

from one_dragon_agent.core.agent.config.base_oda_agent_config_storage import (
    BaseOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig
from one_dragon_agent.core.agent.config.oda_agent_config_manager import (
    OdaAgentConfigManager,
)
from one_dragon_agent.core.model.oda_model_config_manager import (
    OdaModelConfigManager,
)
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager


class TestOdaAgentConfigManager:
    """Test suite for OdaAgentConfigManager"""
    
    @pytest.fixture
    def mock_config_service(self) -> Mock:
        """Fixture to create a mock config service"""
        return Mock(spec=BaseOdaAgentConfigStorage)
    
    @pytest.fixture
    def mock_model_config_manager(self) -> Mock:
        """Fixture to create a mock model config manager"""
        return Mock(spec=OdaModelConfigManager)
    
    @pytest.fixture
    def mock_mcp_manager(self) -> Mock:
        """Fixture to create a mock MCP manager"""
        return Mock(spec=OdaMcpManager)
    
    @pytest.fixture
    def agent_config_manager(
        self,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
    ) -> OdaAgentConfigManager:
        """Fixture to create an OdaAgentConfigManager with mock services"""
        return OdaAgentConfigManager(
            mock_config_service, mock_model_config_manager, mock_mcp_manager
        )
    
    @pytest.fixture
    def sample_config(self) -> OdaAgentConfig:
        """Fixture to create a sample OdaAgentConfig"""
        return OdaAgentConfig(
            app_name="test_app",
            agent_name="test-agent",
            agent_type="llm_agent",
            description="Test agent",
            instruction="Test instruction",
            model_config="test-model-config",
            tool_list=["tool1", "tool2"],
            mcp_list=["mcp1", "mcp2"],
            sub_agent_list=["sub-agent1"],
        )
    
    def test_initialization(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
    ) -> None:
        """Test that the manager initializes correctly with all services"""
        assert agent_config_manager.config_service == mock_config_service
        assert agent_config_manager.model_config_manager == mock_model_config_manager
        assert agent_config_manager.mcp_manager == mock_mcp_manager
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
        sample_config: OdaAgentConfig,
    ) -> None:
        """Test creating a configuration through the manager"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=True)
        mock_mcp_manager.get_mcp_config = AsyncMock(return_value=Mock())
        
        # Call the method
        await agent_config_manager.create_config(sample_config)
        
        # Verify the service method was called with the correct arguments
        mock_config_service.create_config.assert_awaited_once_with(sample_config)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config_invalid_model(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
        sample_config: OdaAgentConfig,
    ) -> None:
        """Test creating a configuration with invalid model raises ValueError"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=False)
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Invalid model configuration"):
            await agent_config_manager.create_config(sample_config)
        
        # Verify the service method was not called
        mock_config_service.create_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config_invalid_mcp(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
        sample_config: OdaAgentConfig,
    ) -> None:
        """Test creating a configuration with invalid MCP raises ValueError"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=True)
        mock_mcp_manager.get_mcp_config = AsyncMock(side_effect=[Mock(), None])  # First MCP exists, second doesn't
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Invalid MCP configuration"):
            await agent_config_manager.create_config(sample_config)
        
        # Verify the service method was not called
        mock_config_service.create_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        sample_config: OdaAgentConfig,
    ) -> None:
        """Test getting a configuration through the manager"""
        # Setup mock
        mock_config_service.get_config = AsyncMock(return_value=sample_config)
        
        # Call the method
        result = await agent_config_manager.get_config("test-agent")
        
        # Verify the service method was called with the correct arguments
        mock_config_service.get_config.assert_awaited_once_with("test-agent")
        assert result == sample_config
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_not_found(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
    ) -> None:
        """Test getting a non-existent configuration through the manager"""
        # Setup mock to return None
        mock_config_service.get_config = AsyncMock(return_value=None)
        
        # Call the method
        result = await agent_config_manager.get_config("non-existent-agent")
        
        # Verify the service method was called with the correct arguments
        mock_config_service.get_config.assert_awaited_once_with("non-existent-agent")
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
        sample_config: OdaAgentConfig,
    ) -> None:
        """Test updating a configuration through the manager"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=True)
        mock_mcp_manager.get_mcp_config = AsyncMock(return_value=Mock())
        
        # Call the method
        await agent_config_manager.update_config(sample_config)
        
        # Verify the service method was called with the correct arguments
        mock_config_service.update_config.assert_awaited_once_with(sample_config)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config_invalid_model(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
        sample_config: OdaAgentConfig,
    ) -> None:
        """Test updating a configuration with invalid model raises ValueError"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=False)
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Invalid model configuration"):
            await agent_config_manager.update_config(sample_config)
        
        # Verify the service method was not called
        mock_config_service.update_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config_invalid_mcp(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
        sample_config: OdaAgentConfig,
    ) -> None:
        """Test updating a configuration with invalid MCP raises ValueError"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=True)
        mock_mcp_manager.get_mcp_config = AsyncMock(side_effect=[Mock(), None])  # First MCP exists, second doesn't
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Invalid MCP configuration"):
            await agent_config_manager.update_config(sample_config)
        
        # Verify the service method was not called
        mock_config_service.update_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
    ) -> None:
        """Test deleting a configuration through the manager"""
        # Setup mock
        mock_config_service.delete_config = AsyncMock()
        
        # Call the method
        await agent_config_manager.delete_config("test-agent")
        
        # Verify the service method was called with the correct arguments
        mock_config_service.delete_config.assert_awaited_once_with("test-agent")
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
    ) -> None:
        """Test listing configurations through the manager"""
        # Setup mock with sample data
        sample_configs = [
            OdaAgentConfig(
                app_name="test_app",
                agent_name="agent-1",
                agent_type="llm_agent",
                description="Agent 1",
                instruction="Instruction 1",
                model_config="model-1",
                tool_list=[],
                mcp_list=[],
                sub_agent_list=[],
            ),
            OdaAgentConfig(
                app_name="test_app",
                agent_name="agent-2",
                agent_type="llm_agent",
                description="Agent 2",
                instruction="Instruction 2",
                model_config="model-2",
                tool_list=[],
                mcp_list=[],
                sub_agent_list=[],
            ),
        ]
        
        mock_config_service.list_configs = AsyncMock(return_value=sample_configs)
        
        # Call the method
        result = await agent_config_manager.list_configs()
        
        # Verify the service method was called
        mock_config_service.list_configs.assert_awaited_once()
        assert result == sample_configs
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_validate_model_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_model_config_manager: Mock,
    ) -> None:
        """Test validating a model configuration through the manager"""
        # Setup mock
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=True)
        
        # Call the method
        result = await agent_config_manager.validate_model_config("test_app", "test-model-config")
        
        # Verify the model config manager method was called with the correct arguments
        mock_model_config_manager.validate_model_config.assert_awaited_once_with("test_app", "test-model-config")
        assert result is True
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_validate_mcp_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_mcp_manager: Mock,
    ) -> None:
        """Test validating MCP configurations through the manager"""
        # Setup mock
        mock_mcp_manager.get_mcp_config = AsyncMock(return_value=Mock())  # All MCPs exist
        
        # Call the method
        result = await agent_config_manager.validate_mcp_config("test_app", ["mcp1", "mcp2"])
        
        # Verify the MCP manager method was called with the correct arguments
        assert mock_mcp_manager.get_mcp_config.await_count == 2
        assert result is True
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_validate_mcp_config_invalid(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_mcp_manager: Mock,
    ) -> None:
        """Test validating MCP configurations with an invalid one"""
        # Setup mock - first MCP exists, second doesn't
        mock_mcp_manager.get_mcp_config = AsyncMock(side_effect=[Mock(), None])
        
        # Call the method
        result = await agent_config_manager.validate_mcp_config("test_app", ["mcp1", "mcp2"])
        
        # Verify the result
        assert result is False
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_default_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
    ) -> None:
        """Test getting built-in default configuration"""
        # Call method
        result = await agent_config_manager.get_config("default")
        
        # Verify result
        assert result is not None
        assert result.agent_name == "default"
        assert result.model_config == "__default_llm_config"
        assert result.tool_list == []
        assert result.mcp_list == []
        assert result.sub_agent_list == []
        
        # Verify storage service was not called (default config is built-in)
        agent_config_manager.config_service.get_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_default_config_multiple_calls(
        self,
        agent_config_manager: OdaAgentConfigManager,
    ) -> None:
        """Test that multiple calls to get default config return same instance"""
        # Call method multiple times
        result1 = await agent_config_manager.get_config("default")
        result2 = await agent_config_manager.get_config("default")
        result3 = await agent_config_manager.get_config("default")
        
        # Verify all results are same instance (lazy loading)
        assert result1 is result2 is result3
        
        # Verify storage service was not called
        agent_config_manager.config_service.get_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config_default_forbidden(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
    ) -> None:
        """Test that creating a config named 'default' raises ValueError"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=True)
        mock_mcp_manager.get_mcp_config = AsyncMock(return_value=Mock())
        
        # Create a config named 'default'
        default_config = OdaAgentConfig(
            app_name="test_app",
            agent_name="default",
            agent_type="llm_agent",
            description="Test default config",
            instruction="Test instruction",
            model_config="test-model",
            tool_list=[],
            mcp_list=[],
            sub_agent_list=[],
        )
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Cannot create built-in default configuration"):
            await agent_config_manager.create_config(default_config)
        
        # Verify service method was not called
        mock_config_service.create_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config_default_forbidden(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
        mock_model_config_manager: Mock,
        mock_mcp_manager: Mock,
    ) -> None:
        """Test that updating a config named 'default' raises ValueError"""
        # Setup mocks
        mock_model_config_manager.validate_model_config = AsyncMock(return_value=True)
        mock_mcp_manager.get_mcp_config = AsyncMock(return_value=Mock())
        
        # Create a config named 'default'
        default_config = OdaAgentConfig(
            app_name="test_app",
            agent_name="default",
            agent_type="llm_agent",
            description="Test default config",
            instruction="Test instruction",
            model_config="test-model",
            tool_list=[],
            mcp_list=[],
            sub_agent_list=[],
        )
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Cannot update built-in default configuration"):
            await agent_config_manager.update_config(default_config)
        
        # Verify service method was not called
        mock_config_service.update_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config_default_forbidden(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
    ) -> None:
        """Test that deleting a config named 'default' raises ValueError"""
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Cannot delete built-in default configuration"):
            await agent_config_manager.delete_config("default")
        
        # Verify service method was not called
        mock_config_service.delete_config.assert_not_called()
    
    def test_is_built_in_config(
        self,
        agent_config_manager: OdaAgentConfigManager,
    ) -> None:
        """Test checking if a config is built-in"""
        # Test with default config name
        assert agent_config_manager.is_built_in_config("default") is True
        
        # Test with other config names
        assert agent_config_manager.is_built_in_config("other") is False
        assert agent_config_manager.is_built_in_config("test-agent") is False
        assert agent_config_manager.is_built_in_config("") is False
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs_excludes_default(
        self,
        agent_config_manager: OdaAgentConfigManager,
        mock_config_service: Mock,
    ) -> None:
        """Test that list_configs does not include built-in default configuration"""
        # Setup mock with some configs
        sample_configs = [
            OdaAgentConfig(
                app_name="test_app",
                agent_name="agent-1",
                agent_type="llm_agent",
                description="Agent 1",
                instruction="Instruction 1",
                model_config="model-1",
                tool_list=[],
                mcp_list=[],
                sub_agent_list=[],
            ),
            OdaAgentConfig(
                app_name="test_app",
                agent_name="agent-2",
                agent_type="llm_agent",
                description="Agent 2",
                instruction="Instruction 2",
                model_config="model-2",
                tool_list=[],
                mcp_list=[],
                sub_agent_list=[],
            ),
        ]
        
        mock_config_service.list_configs = AsyncMock(return_value=sample_configs)
        
        # Call method
        result = await agent_config_manager.list_configs()
        
        # Verify result contains only persistent configs
        assert len(result) == 2
        assert result[0].agent_name == "agent-1"
        assert result[1].agent_name == "agent-2"
        
        # Verify no config named 'default' is in list
        for config in result:
            assert config.agent_name != "default"
