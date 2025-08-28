"""Test OdaToolManager register_tool method."""

from unittest.mock import Mock

import pytest
from google.adk.tools import BaseTool

from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager


class TestOdaToolManagerRegisterTool:
    """Test cases for OdaToolManager.register_tool method."""

    @pytest.fixture
    def tool_manager(self) -> OdaToolManager:
        """Create an OdaToolManager instance for testing."""
        return OdaToolManager()

    @pytest.fixture
    def mock_tool(self) -> BaseTool:
        """Create a mock BaseTool for testing."""
        tool = Mock(spec=BaseTool)
        tool.name = "test_tool"
        tool.description = "Test tool for unit testing"
        return tool

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_tool_success(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test successful tool registration."""
        # Arrange
        app_name = "test_app"
        tool_id = "test_tool"

        # Act
        await tool_manager.register_tool(mock_tool, app_name, tool_id)

        # Assert
        registered_tool = await tool_manager.get_tool(app_name, tool_id)
        assert registered_tool is mock_tool
        assert registered_tool.name == "test_tool"
        assert registered_tool.description == "Test tool for unit testing"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_tool_invalid_type(self, tool_manager: OdaToolManager):
        """Test registration fails with non-BaseTool instance."""
        # Arrange
        invalid_tool = "not_a_tool"
        app_name = "test_app"
        tool_id = "invalid_tool"

        # Act & Assert
        with pytest.raises(TypeError, match="tool must be an instance of BaseTool"):
            await tool_manager.register_tool(invalid_tool, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_tool_empty_app_name(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test registration fails with empty app_name."""
        # Arrange
        app_name = ""
        tool_id = "test_tool"

        # Act & Assert
        with pytest.raises(ValueError, match="app_name cannot be empty"):
            await tool_manager.register_tool(mock_tool, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_tool_empty_tool_id(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test registration fails with empty tool_id."""
        # Arrange
        app_name = "test_app"
        tool_id = ""

        # Act & Assert
        with pytest.raises(ValueError, match="tool_id cannot be empty"):
            await tool_manager.register_tool(mock_tool, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_tool_duplicate_id_same_app(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test registration fails when tool_id already exists in same app."""
        # Arrange
        app_name = "test_app"
        tool_id = "duplicate_tool"
        
        # Register first tool
        await tool_manager.register_tool(mock_tool, app_name, tool_id)

        # Act & Assert - Register second tool with same id
        with pytest.raises(ValueError, match="Tool with ID 'test_app:duplicate_tool' already exists"):
            await tool_manager.register_tool(mock_tool, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_tool_same_id_different_apps(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test that same tool_id can be used in different apps."""
        # Arrange
        app1_name = "app1"
        app2_name = "app2"
        tool_id = "same_tool"

        # Act
        await tool_manager.register_tool(mock_tool, app1_name, tool_id)
        await tool_manager.register_tool(mock_tool, app2_name, tool_id)

        # Assert
        tool1 = await tool_manager.get_tool(app1_name, tool_id)
        tool2 = await tool_manager.get_tool(app2_name, tool_id)
        
        assert tool1 is mock_tool
        assert tool2 is mock_tool

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_tool_multiple_tools_same_app(self, tool_manager: OdaToolManager):
        """Test registering multiple tools in the same app."""
        # Arrange
        app_name = "test_app"
        tool1 = Mock(spec=BaseTool)
        tool1.name = "tool1"
        tool1.description = "First tool"
        
        tool2 = Mock(spec=BaseTool)
        tool2.name = "tool2"
        tool2.description = "Second tool"

        # Act
        await tool_manager.register_tool(tool1, app_name, "tool1")
        await tool_manager.register_tool(tool2, app_name, "tool2")

        # Assert
        registered_tool1 = await tool_manager.get_tool(app_name, "tool1")
        registered_tool2 = await tool_manager.get_tool(app_name, "tool2")
        
        assert registered_tool1 is tool1
        assert registered_tool2 is tool2
        assert registered_tool1.name == "tool1"
        assert registered_tool2.name == "tool2"