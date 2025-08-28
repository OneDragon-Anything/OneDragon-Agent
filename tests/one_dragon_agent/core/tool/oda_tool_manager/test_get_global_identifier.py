"""Test OdaToolManager get_global_identifier method."""


import pytest

from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager


class TestOdaToolManagerGetGlobalIdentifier:
    """Test cases for OdaToolManager.get_global_identifier method."""

    @pytest.fixture
    def tool_manager(self) -> OdaToolManager:
        """Create an OdaToolManager instance for testing."""
        return OdaToolManager()

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_normal_case(self, tool_manager: OdaToolManager):
        """Test global identifier generation with normal app_name and tool_id."""
        # Arrange
        app_name = "test_app"
        tool_id = "test_tool"

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == "test_app:test_tool"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_empty_app_name(self, tool_manager: OdaToolManager):
        """Test global identifier generation with empty app_name."""
        # Arrange
        app_name = ""
        tool_id = "test_tool"

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == ":test_tool"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_empty_tool_id(self, tool_manager: OdaToolManager):
        """Test global identifier generation with empty tool_id."""
        # Arrange
        app_name = "test_app"
        tool_id = ""

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == "test_app:"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_both_empty(self, tool_manager: OdaToolManager):
        """Test global identifier generation with both app_name and tool_id empty."""
        # Arrange
        app_name = ""
        tool_id = ""

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == ":"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_with_special_characters(self, tool_manager: OdaToolManager):
        """Test global identifier generation with special characters."""
        # Arrange
        app_name = "test-app.name"
        tool_id = "test.tool.id"

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == "test-app.name:test.tool.id"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_with_numbers(self, tool_manager: OdaToolManager):
        """Test global identifier generation with numbers."""
        # Arrange
        app_name = "app123"
        tool_id = "tool456"

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == "app123:tool456"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_case_sensitive(self, tool_manager: OdaToolManager):
        """Test that global identifier generation is case sensitive."""
        # Arrange
        app_name = "TestApp"
        tool_id = "TestTool"

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == "TestApp:TestTool"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_with_spaces(self, tool_manager: OdaToolManager):
        """Test global identifier generation with spaces."""
        # Arrange
        app_name = "test app"
        tool_id = "test tool"

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == "test app:test tool"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_unicode_characters(self, tool_manager: OdaToolManager):
        """Test global identifier generation with unicode characters."""
        # Arrange
        app_name = "测试应用"
        tool_id = "测试工具"

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result == "测试应用:测试工具"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_very_long_names(self, tool_manager: OdaToolManager):
        """Test global identifier generation with very long names."""
        # Arrange
        app_name = "a" * 100  # 100 character app name
        tool_id = "b" * 100  # 100 character tool id

        # Act
        result = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        expected = app_name + ":" + tool_id
        assert result == expected
        assert len(result) == 201  # 100 + 1 + 100

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_global_identifier_consistency(self, tool_manager: OdaToolManager):
        """Test that identical inputs produce identical outputs."""
        # Arrange
        app_name = "consistent_app"
        tool_id = "consistent_tool"

        # Act
        result1 = tool_manager.get_global_identifier(app_name, tool_id)
        result2 = tool_manager.get_global_identifier(app_name, tool_id)

        # Assert
        assert result1 == result2
        assert result1 == "consistent_app:consistent_tool"