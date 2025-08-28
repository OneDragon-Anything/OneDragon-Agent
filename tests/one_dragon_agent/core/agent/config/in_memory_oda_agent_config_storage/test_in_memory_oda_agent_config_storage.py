"""Tests for InMemoryOdaAgentConfigStorage"""

from unittest.mock import Mock

import pytest

from one_dragon_agent.core.agent.config.in_memory_oda_agent_config_storage import (
    InMemoryOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig
from one_dragon_agent.core.model.oda_model_config_manager import (
    OdaModelConfigManager,
)


class TestInMemoryOdaAgentConfigStorage:
    """Test suite for InMemoryOdaAgentConfigStorage"""
    
    @pytest.fixture
    def mock_model_config_manager(self) -> Mock:
        """Fixture to create a mock model config manager"""
        return Mock(spec=OdaModelConfigManager)
    
    @pytest.fixture
    def storage(self, mock_model_config_manager: Mock) -> InMemoryOdaAgentConfigStorage:
        """Fixture to create an InMemoryOdaAgentConfigStorage instance"""
        return InMemoryOdaAgentConfigStorage(mock_model_config_manager)
    
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
    
    def test_initialization(self, storage: InMemoryOdaAgentConfigStorage, mock_model_config_manager: Mock) -> None:
        """Test that the storage initializes correctly"""
        assert storage.model_config_manager == mock_model_config_manager
        assert storage._configs == {}
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config(self, storage: InMemoryOdaAgentConfigStorage, sample_config: OdaAgentConfig) -> None:
        """Test creating a configuration"""
        # Call the method
        await storage.create_config(sample_config)
        
        # Verify the config was stored
        assert storage._configs[sample_config.agent_name] == sample_config
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config_duplicate(self, storage: InMemoryOdaAgentConfigStorage, sample_config: OdaAgentConfig) -> None:
        """Test creating a duplicate configuration raises ValueError"""
        # First create the config
        await storage.create_config(sample_config)
        
        # Attempt to create the same config again
        with pytest.raises(ValueError, match="already exists"):
            await storage.create_config(sample_config)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config(self, storage: InMemoryOdaAgentConfigStorage, sample_config: OdaAgentConfig) -> None:
        """Test getting a configuration"""
        # First create the config
        await storage.create_config(sample_config)
        
        # Call the method
        result = await storage.get_config(sample_config.agent_name)
        
        # Verify the result
        assert result == sample_config
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_not_found(self, storage: InMemoryOdaAgentConfigStorage) -> None:
        """Test getting a non-existent configuration"""
        # Call the method
        result = await storage.get_config("non-existent-agent")
        
        # Verify the result
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config(self, storage: InMemoryOdaAgentConfigStorage, sample_config: OdaAgentConfig) -> None:
        """Test updating a configuration"""
        # First create the config
        await storage.create_config(sample_config)
        
        # Create an updated config
        updated_config = OdaAgentConfig(
            app_name="test_app",
            agent_name="test-agent",
            agent_type="llm_agent",
            description="Updated test agent",
            instruction="Updated instruction",
            model_config="updated-model-config",
            tool_list=["tool3", "tool4"],
            mcp_list=["mcp3", "mcp4"],
            sub_agent_list=["sub-agent2"],
        )
        
        # Call the method
        await storage.update_config(updated_config)
        
        # Verify the config was updated
        assert storage._configs[updated_config.agent_name] == updated_config
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config_not_found(self, storage: InMemoryOdaAgentConfigStorage, sample_config: OdaAgentConfig) -> None:
        """Test updating a non-existent configuration raises ValueError"""
        # Attempt to update a config that doesn't exist
        with pytest.raises(ValueError, match="does not exist"):
            await storage.update_config(sample_config)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config(self, storage: InMemoryOdaAgentConfigStorage, sample_config: OdaAgentConfig) -> None:
        """Test deleting a configuration"""
        # First create the config
        await storage.create_config(sample_config)
        
        # Call the method
        await storage.delete_config(sample_config.agent_name)
        
        # Verify the config was deleted
        assert sample_config.agent_name not in storage._configs
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config_not_found(self, storage: InMemoryOdaAgentConfigStorage) -> None:
        """Test deleting a non-existent configuration"""
        # Call the method (should not raise an error)
        await storage.delete_config("non-existent-agent")
        
        # Verify no error was raised
        assert True
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs(self, storage: InMemoryOdaAgentConfigStorage, sample_config: OdaAgentConfig) -> None:
        """Test listing configurations"""
        # First create the config
        await storage.create_config(sample_config)
        
        # Create another config
        another_config = OdaAgentConfig(
            app_name="test_app",
            agent_name="another-agent",
            agent_type="llm_agent",
            description="Another test agent",
            instruction="Another instruction",
            model_config="another-model-config",
            tool_list=[],
            mcp_list=[],
            sub_agent_list=[],
        )
        await storage.create_config(another_config)
        
        # Call the method
        result = await storage.list_configs()
        
        # Verify the result
        assert len(result) == 2
        assert sample_config in result
        assert another_config in result
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs_empty(self, storage: InMemoryOdaAgentConfigStorage) -> None:
        """Test listing configurations when there are none"""
        # Call the method
        result = await storage.list_configs()
        
        # Verify the result
        assert result == []
    
