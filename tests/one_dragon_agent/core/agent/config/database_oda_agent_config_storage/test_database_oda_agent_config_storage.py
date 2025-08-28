"""Tests for DatabaseOdaAgentConfigStorage"""

from unittest.mock import Mock

import pytest

from one_dragon_agent.core.agent.config.database_oda_agent_config_storage import (
    DatabaseOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig
from one_dragon_agent.core.model.oda_model_config_manager import (
    OdaModelConfigManager,
)


class TestDatabaseOdaAgentConfigStorage:
    """Test suite for DatabaseOdaAgentConfigStorage"""
    
    @pytest.fixture
    def mock_model_config_manager(self) -> Mock:
        """Fixture to create a mock model config manager"""
        return Mock(spec=OdaModelConfigManager)
    
    @pytest.fixture
    def storage(self, mock_model_config_manager: Mock) -> DatabaseOdaAgentConfigStorage:
        """Fixture to create a DatabaseOdaAgentConfigStorage instance"""
        return DatabaseOdaAgentConfigStorage("sqlite:///:memory:", mock_model_config_manager)
    
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
    
    def test_initialization(self, storage: DatabaseOdaAgentConfigStorage, mock_model_config_manager: Mock) -> None:
        """Test that the storage initializes correctly"""
        assert storage.db_url == "sqlite:///:memory:"
        assert storage.model_config_manager == mock_model_config_manager
    
