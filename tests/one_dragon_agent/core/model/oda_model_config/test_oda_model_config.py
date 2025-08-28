"""Tests for OdaModelConfig dataclass"""

from one_dragon_agent.core.model.oda_model_config import OdaModelConfig


class TestOdaModelConfig:
    """Test suite for OdaModelConfig dataclass"""
    
    def test_oda_model_config_creation(self) -> None:
        """Test creating an OdaModelConfig instance"""
        config = OdaModelConfig(
            app_name="test_app",
            model_id="test-model-123",
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="gemini-pro"
        )
        
        assert config.app_name == "test_app"
        assert config.model_id == "test-model-123"
        assert config.base_url == "https://api.example.com"
        assert config.api_key == "sk-test123"
        assert config.model == "gemini-pro"
    
    def test_oda_model_config_equality(self) -> None:
        """Test equality comparison of OdaModelConfig instances"""
        config1 = OdaModelConfig(
            app_name="test_app",
            model_id="test-model-123",
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="gemini-pro"
        )
        
        config2 = OdaModelConfig(
            app_name="test_app",
            model_id="test-model-123",
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="gemini-pro"
        )
        
        config3 = OdaModelConfig(
            app_name="test_app",
            model_id="test-model-456",
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="gemini-pro"
        )
        
        assert config1 == config2
        assert config1 != config3
        assert config2 != config3
    
    def test_oda_model_config_repr(self) -> None:
        """Test string representation of OdaModelConfig"""
        config = OdaModelConfig(
            app_name="test_app",
            model_id="test-model-123",
            base_url="https://api.example.com",
            api_key="sk-test123",
            model="gemini-pro"
        )
        
        repr_str = repr(config)
        assert "test_app" in repr_str
        assert "test-model-123" in repr_str
        assert "https://api.example.com" in repr_str
        assert "sk-test123" in repr_str
        assert "gemini-pro" in repr_str