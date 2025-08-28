"""Tests for BaseOdaAgentConfigStorage"""

import pytest

from one_dragon_agent.core.agent.config.base_oda_agent_config_storage import (
    BaseOdaAgentConfigStorage,
)


class TestBaseOdaAgentConfigStorage:
    """Test suite for BaseOdaAgentConfigStorage"""
    
    def test_abstract_class_cannot_be_instantiated(self) -> None:
        """Test that the abstract class cannot be instantiated directly"""
        # Attempting to instantiate an abstract class should raise a TypeError
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseOdaAgentConfigStorage()