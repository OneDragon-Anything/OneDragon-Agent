"""Tests for InMemoryOdaModelConfigStorage"""

import pytest

from one_dragon_agent.core.model.in_memory_oda_model_config_storage import (
    InMemoryOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig


class TestInMemoryOdaModelConfigStorage:
    """Test suite for InMemoryOdaModelConfigStorage"""
    
    @pytest.fixture
    def config_storage(self) -> InMemoryOdaModelConfigStorage:
        """Fixture to create a new InMemoryOdaModelConfigStorage instance for each test"""
        return InMemoryOdaModelConfigStorage()
    
    @pytest.fixture
    def sample_config(self) -> OdaModelConfig:
        """Fixture to create a sample OdaModelConfig"""
        return OdaModelConfig(
            app_name="test_app",
            model_id="test-model-123",
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="gemini-pro"
        )
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config(self, config_storage: InMemoryOdaModelConfigStorage, sample_config: OdaModelConfig) -> None:
        """Test creating a new configuration"""
        await config_storage.create_config(sample_config)
        
        # Verify the config was stored
        retrieved_config = await config_storage.get_config("test-model-123")
        assert retrieved_config is not None
        assert retrieved_config == sample_config
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_exists(self, config_storage: InMemoryOdaModelConfigStorage, sample_config: OdaModelConfig) -> None:
        """Test getting an existing configuration"""
        await config_storage.create_config(sample_config)
        
        retrieved_config = await config_storage.get_config("test-model-123")
        assert retrieved_config is not None
        assert retrieved_config == sample_config
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_not_exists(self, config_storage: InMemoryOdaModelConfigStorage) -> None:
        """Test getting a non-existent configuration"""
        retrieved_config = await config_storage.get_config("non-existent-model")
        assert retrieved_config is None
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config(self, config_storage: InMemoryOdaModelConfigStorage, sample_config: OdaModelConfig) -> None:
        """Test updating an existing configuration"""
        # First create the config
        await config_storage.create_config(sample_config)
        
        # Update the config
        updated_config = OdaModelConfig(
            app_name="test_app",
            model_id="test-model-123",
            base_url="https://api.updated-example.com",
            api_key="sk-updated123",
            model="gemini-pro-turbo"
        )
        
        await config_storage.update_config(updated_config)
        
        # Verify the update
        retrieved_config = await config_storage.get_config("test-model-123")
        assert retrieved_config is not None
        assert retrieved_config == updated_config
        assert retrieved_config.base_url == "https://api.updated-example.com"
        assert retrieved_config.api_key == "sk-updated123"
        assert retrieved_config.model == "gemini-pro-turbo"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config_not_exists(self, config_storage: InMemoryOdaModelConfigStorage, sample_config: OdaModelConfig) -> None:
        """Test updating a non-existent configuration (should not raise an error)"""
        # This should not raise an error
        await config_storage.update_config(sample_config)
        
        # Verify the config was not created by update
        retrieved_config = await config_storage.get_config("test-model-123")
        assert retrieved_config is None
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config(self, config_storage: InMemoryOdaModelConfigStorage, sample_config: OdaModelConfig) -> None:
        """Test deleting an existing configuration"""
        # First create the config
        await config_storage.create_config(sample_config)
        
        # Verify it exists
        retrieved_config = await config_storage.get_config("test-model-123")
        assert retrieved_config is not None
        
        # Delete the config
        await config_storage.delete_config("test-model-123")
        
        # Verify it's deleted
        retrieved_config = await config_storage.get_config("test-model-123")
        assert retrieved_config is None
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config_not_exists(self, config_storage: InMemoryOdaModelConfigStorage) -> None:
        """Test deleting a non-existent configuration (should not raise an error)"""
        # This should not raise an error
        await config_storage.delete_config("non-existent-model")
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs(self, config_storage: InMemoryOdaModelConfigStorage) -> None:
        """Test listing all configurations"""
        # Initially empty
        configs = await config_storage.list_configs()
        assert configs == []
        
        # Add some configs
        config1 = OdaModelConfig(
            app_name="test_app",
            model_id="model-1",
            base_url="https://api1.example.com",
            api_key="sk-1",
            model="model-1"
        )
        
        config2 = OdaModelConfig(
            app_name="test_app",
            model_id="model-2",
            base_url="https://api2.example.com",
            api_key="sk-2",
            model="model-2"
        )
        
        await config_storage.create_config(config1)
        await config_storage.create_config(config2)
        
        # Verify the list
        configs = await config_storage.list_configs()
        assert len(configs) == 2
        assert config1 in configs
        assert config2 in configs
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_isolation_between_instances(self) -> None:
        """Test that different storage instances are isolated"""
        storage1 = InMemoryOdaModelConfigStorage()
        storage2 = InMemoryOdaModelConfigStorage()
        
        config = OdaModelConfig(
            app_name="test_app",
            model_id="test-model",
            base_url="https://api.example.com",
            api_key="sk-test",
            model="test-model"
        )
        
        # Add config to storage1 only
        await storage1.create_config(config)
        
        # Verify it exists in storage1
        retrieved_config1 = await storage1.get_config("test-model")
        assert retrieved_config1 is not None
        
        # Verify it doesn't exist in storage2
        retrieved_config2 = await storage2.get_config("test-model")
        assert retrieved_config2 is None