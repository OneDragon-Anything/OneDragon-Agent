"""Tests for BaseOdaModelConfigStorage abstract base class"""

from abc import ABC

from one_dragon_agent.core.model.base_oda_model_config_storage import (
    BaseOdaModelConfigStorage,
)


class TestBaseOdaModelConfigStorage:
    """Test suite for BaseOdaModelConfigStorage abstract base class"""
    
    def test_base_class_is_abstract(self) -> None:
        """Test that BaseOdaModelConfigStorage is an abstract base class"""
        # This should not raise an error - it's testing that the class is properly defined
        assert issubclass(BaseOdaModelConfigStorage, ABC)
    
    def test_abstract_methods_exist(self) -> None:
        """Test that all required abstract methods are defined"""
        abstract_methods = [
            'create_config',
            'get_config', 
            'update_config',
            'delete_config',
            'list_configs'
        ]
        
        for method_name in abstract_methods:
            assert hasattr(BaseOdaModelConfigStorage, method_name)
            method = getattr(BaseOdaModelConfigStorage, method_name)
            # Check that it's marked as abstract
            assert getattr(method, '__isabstractmethod__', False)