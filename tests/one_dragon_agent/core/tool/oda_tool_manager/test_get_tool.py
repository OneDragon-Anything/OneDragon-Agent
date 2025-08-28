"""Test OdaToolManager get_tool method."""

from unittest.mock import Mock

import pytest
from google.adk.tools import BaseTool, FunctionTool

from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager


class TestOdaToolManagerGetTool:
    """Test cases for OdaToolManager.get_tool method."""

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
    async def test_get_tool_existing_tool(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test getting an existing tool."""
        # Arrange
        app_name = "test_app"
        tool_id = "existing_tool"
        await tool_manager.register_tool(mock_tool, app_name, tool_id)

        # Act
        result = await tool_manager.get_tool(app_name, tool_id)

        # Assert
        assert result is not None
        assert result is mock_tool
        assert result.name == "test_tool"
        assert result.description == "Test tool for unit testing"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_tool_non_existing_app(self, tool_manager: OdaToolManager):
        """Test getting tool from non-existing app."""
        # Arrange
        app_name = "non_existing_app"
        tool_id = "any_tool"

        # Act
        result = await tool_manager.get_tool(app_name, tool_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_tool_non_existing_tool(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test getting non-existing tool from existing app."""
        # Arrange
        app_name = "test_app"
        tool_id = "non_existing_tool"
        # Register a different tool in the app
        await tool_manager.register_tool(mock_tool, app_name, "different_tool")

        # Act
        result = await tool_manager.get_tool(app_name, tool_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_tool_empty_app_name(self, tool_manager: OdaToolManager):
        """Test getting tool with empty app_name."""
        # Arrange
        app_name = ""
        tool_id = "any_tool"

        # Act
        result = await tool_manager.get_tool(app_name, tool_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_tool_empty_tool_id(self, tool_manager: OdaToolManager):
        """Test getting tool with empty tool_id."""
        # Arrange
        app_name = "test_app"
        tool_id = ""

        # Act
        result = await tool_manager.get_tool(app_name, tool_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_tool_after_function_registration(self, tool_manager: OdaToolManager):
        """Test getting tool that was registered via register_function."""
        # Arrange
        app_name = "test_app"
        tool_id = "func_tool"
        
        def test_function(param: str) -> dict:
            """Test function."""
            return {"result": param}

        await tool_manager.register_function(test_function, app_name, tool_id)

        # Act
        result = await tool_manager.get_tool(app_name, tool_id)

        # Assert
        assert result is not None
        assert isinstance(result, FunctionTool)
        assert result.func is test_function
        assert result.name == "test_function"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_tool_multiple_apps_same_tool_id(self, tool_manager: OdaToolManager, mock_tool: BaseTool):
        """Test getting tools with same tool_id from different apps."""
        # Arrange
        app1_name = "app1"
        app2_name = "app2"
        tool_id = "same_tool"
        
        tool1 = Mock(spec=BaseTool)
        tool1.name = "tool1"
        tool1.description = "First tool"
        
        tool2 = Mock(spec=BaseTool)
        tool2.name = "tool2"
        tool2.description = "Second tool"

        await tool_manager.register_tool(tool1, app1_name, tool_id)
        await tool_manager.register_tool(tool2, app2_name, tool_id)

        # Act
        result1 = await tool_manager.get_tool(app1_name, tool_id)
        result2 = await tool_manager.get_tool(app2_name, tool_id)

        # Assert
        assert result1 is not None
        assert result2 is not None
        assert result1 is tool1
        assert result2 is tool2
        assert result1.name == "tool1"
        assert result2.name == "tool2"