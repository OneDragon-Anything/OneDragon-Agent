"""Tests for OdaModelConfigManager"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

import pytest

from one_dragon_agent.core.model.base_oda_model_config_storage import (
    BaseOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig
from one_dragon_agent.core.model.oda_model_config_manager import (
    DEFAULT_LLM_CONFIG_ID,
    OdaModelConfigManager,
)


# Simple mock for OdaContextConfig to avoid circular imports
@dataclass
class OdaContextConfig:
    """Mock OdaContextConfig for testing"""
    default_llm_base_url: str | None = None
    default_llm_api_key: str | None = None
    default_llm_model: str | None = None


class TestOdaModelConfigManager:
    """Test suite for OdaModelConfigManager"""
    
    @pytest.fixture
    def mock_config_service(self) -> Mock:
        """Fixture to create a mock config service"""
        return Mock(spec=BaseOdaModelConfigStorage)
    
    @pytest.fixture
    def context_config(self) -> OdaContextConfig:
        """Fixture to create a context config without default LLM settings"""
        return OdaContextConfig()
    
    @pytest.fixture
    def context_config_with_defaults(self) -> OdaContextConfig:
        """Fixture to create a context config with default LLM settings"""
        return OdaContextConfig(
            default_llm_base_url="https://api.default.com",
            default_llm_api_key="sk-default123",
            default_llm_model="default-model"
        )
    
    @pytest.fixture
    def config_manager(self, mock_config_service: Mock, context_config: OdaContextConfig) -> OdaModelConfigManager:
        """Fixture to create an OdaModelConfigManager with a mock service"""
        return OdaModelConfigManager(mock_config_service, context_config)
    
    @pytest.fixture
    def config_manager_with_defaults(self, mock_config_service: Mock, context_config_with_defaults: OdaContextConfig) -> OdaModelConfigManager:
        """Fixture to create an OdaModelConfigManager with default LLM settings"""
        return OdaModelConfigManager(mock_config_service, context_config_with_defaults)
    
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
    
    def test_initialization(self, mock_config_service: Mock, context_config: OdaContextConfig) -> None:
        """Test that the manager initializes correctly with a config service"""
        manager = OdaModelConfigManager(mock_config_service, context_config)
        assert manager.config_service == mock_config_service
        assert manager.get_default_config() is None
    
    def test_initialization_with_defaults(self, mock_config_service: Mock, context_config_with_defaults: OdaContextConfig) -> None:
        """Test that the manager initializes correctly with default LLM settings"""
        manager = OdaModelConfigManager(mock_config_service, context_config_with_defaults)
        assert manager.config_service == mock_config_service
        
        default_config = manager.get_default_config()
        assert default_config is not None
        assert default_config.model_id == DEFAULT_LLM_CONFIG_ID
        assert default_config.base_url == "https://api.default.com"
        assert default_config.api_key == "sk-default123"
        assert default_config.model == "default-model"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config(self, config_manager: OdaModelConfigManager, mock_config_service: Mock, sample_config: OdaModelConfig) -> None:
        """Test creating a configuration through the manager"""
        # Setup mock
        mock_config_service.create_config = AsyncMock()
        
        # Call the method
        await config_manager.create_config(sample_config)
        
        # Verify the service method was called with the correct arguments
        mock_config_service.create_config.assert_awaited_once_with(sample_config)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config_default_not_allowed(self, config_manager: OdaModelConfigManager, mock_config_service: Mock) -> None:
        """Test that creating a default configuration is not allowed"""
        default_config = OdaModelConfig(
            app_name="__default_app",
            model_id=DEFAULT_LLM_CONFIG_ID,
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="test-model"
        )
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Default configuration cannot be created manually"):
            await config_manager.create_config(default_config)
        
        # Verify the service method was not called
        mock_config_service.create_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config(self, config_manager: OdaModelConfigManager, mock_config_service: Mock, sample_config: OdaModelConfig) -> None:
        """Test getting a configuration through the manager"""
        # Setup mock
        mock_config_service.get_config = AsyncMock(return_value=sample_config)
        
        # Call the method
        result = await config_manager.get_config("test-model-123")
        
        # Verify the service method was called with the correct arguments
        mock_config_service.get_config.assert_awaited_once_with("test-model-123")
        assert result == sample_config
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_default(self, config_manager_with_defaults: OdaModelConfigManager) -> None:
        """Test getting the default configuration"""
        # Call the method
        result = await config_manager_with_defaults.get_config(DEFAULT_LLM_CONFIG_ID)
        
        # Verify the result is the default config
        assert result is not None
        assert result.model_id == DEFAULT_LLM_CONFIG_ID
        assert result.base_url == "https://api.default.com"
        assert result.api_key == "sk-default123"
        assert result.model == "default-model"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_default_not_found(self, config_manager: OdaModelConfigManager) -> None:
        """Test getting the default configuration when it doesn't exist"""
        # Call the method
        result = await config_manager.get_config(DEFAULT_LLM_CONFIG_ID)
        
        # Verify the result is None
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_not_found(self, config_manager: OdaModelConfigManager, mock_config_service: Mock) -> None:
        """Test getting a non-existent configuration through the manager"""
        # Setup mock to return None
        mock_config_service.get_config = AsyncMock(return_value=None)
        
        # Call the method
        result = await config_manager.get_config("non-existent-model")
        
        # Verify the service method was called with the correct arguments
        mock_config_service.get_config.assert_awaited_once_with("non-existent-model")
        assert result is None
    
    def test_get_default_config(self, config_manager_with_defaults: OdaModelConfigManager) -> None:
        """Test getting the default configuration through the dedicated method"""
        # Call the method
        result = config_manager_with_defaults.get_default_config()
        
        # Verify the result is the default config
        assert result is not None
        assert result.model_id == DEFAULT_LLM_CONFIG_ID
        assert result.base_url == "https://api.default.com"
        assert result.api_key == "sk-default123"
        assert result.model == "default-model"
    
    def test_get_default_config_not_found(self, config_manager: OdaModelConfigManager) -> None:
        """Test getting the default configuration when it doesn't exist"""
        # Call the method
        result = config_manager.get_default_config()
        
        # Verify the result is None
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config(self, config_manager: OdaModelConfigManager, mock_config_service: Mock, sample_config: OdaModelConfig) -> None:
        """Test updating a configuration through the manager"""
        # Setup mock
        mock_config_service.update_config = AsyncMock()
        
        # Call the method
        await config_manager.update_config(sample_config)
        
        # Verify the service method was called with the correct arguments
        mock_config_service.update_config.assert_awaited_once_with(sample_config)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config_default_not_allowed(self, config_manager: OdaModelConfigManager, mock_config_service: Mock) -> None:
        """Test that updating the default configuration is not allowed"""
        default_config = OdaModelConfig(
            app_name="__default_app",
            model_id=DEFAULT_LLM_CONFIG_ID,
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="test-model"
        )
        
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Default configuration cannot be updated manually"):
            await config_manager.update_config(default_config)
        
        # Verify the service method was not called
        mock_config_service.update_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config(self, config_manager: OdaModelConfigManager, mock_config_service: Mock) -> None:
        """Test deleting a configuration through the manager"""
        # Setup mock
        mock_config_service.delete_config = AsyncMock()
        
        # Call the method
        await config_manager.delete_config("test-model-123")
        
        # Verify the service method was called with the correct arguments
        mock_config_service.delete_config.assert_awaited_once_with("test-model-123")
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config_default_not_allowed(self, config_manager: OdaModelConfigManager, mock_config_service: Mock) -> None:
        """Test that deleting the default configuration is not allowed"""
        # Expect ValueError to be raised
        with pytest.raises(ValueError, match="Default configuration cannot be deleted"):
            await config_manager.delete_config(DEFAULT_LLM_CONFIG_ID)
        
        # Verify the service method was not called
        mock_config_service.delete_config.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs(self, config_manager: OdaModelConfigManager, mock_config_service: Mock) -> None:
        """Test listing configurations through the manager"""
        # Setup mock with sample data
        sample_configs = [
            OdaModelConfig(
                app_name="test_app",
                model_id="model-1",
                base_url="https://api1.example.com",
                api_key="sk-1",
                model="model-1"
            ),
            OdaModelConfig(
                app_name="test_app",
                model_id="model-2",
                base_url="https://api2.example.com",
                api_key="sk-2",
                model="model-2"
            )
        ]
        
        mock_config_service.list_configs = AsyncMock(return_value=sample_configs)
        
        # Call the method
        result = await config_manager.list_configs()
        
        # Verify the service method was called
        mock_config_service.list_configs.assert_awaited_once()
        assert result == sample_configs
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs_with_default(self, config_manager_with_defaults: OdaModelConfigManager, mock_config_service: Mock) -> None:
        """Test listing configurations when default configuration exists"""
        # Setup mock with sample data
        sample_configs = [
            OdaModelConfig(
                app_name="test_app",
                model_id="model-1",
                base_url="https://api1.example.com",
                api_key="sk-1",
                model="model-1"
            ),
            OdaModelConfig(
                app_name="test_app",
                model_id="model-2",
                base_url="https://api2.example.com",
                api_key="sk-2",
                model="model-2"
            )
        ]
        
        mock_config_service.list_configs = AsyncMock(return_value=sample_configs)
        
        # Call the method
        result = await config_manager_with_defaults.list_configs()
        
        # Verify the service method was called
        mock_config_service.list_configs.assert_awaited_once()
        
        # Verify the result includes both persistent configs and the default config
        assert len(result) == 3
        assert result[0] == sample_configs[0]
        assert result[1] == sample_configs[1]
        assert result[2].model_id == DEFAULT_LLM_CONFIG_ID