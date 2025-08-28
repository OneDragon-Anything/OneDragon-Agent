"""Test OdaToolManager list_tools method."""

from unittest.mock import Mock

import pytest
from google.adk.tools import BaseTool, FunctionTool

from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager


class TestOdaToolManagerListTools:
    """Test cases for OdaToolManager.list_tools method."""

    @pytest.fixture
    def tool_manager(self) -> OdaToolManager:
        """Create an OdaToolManager instance for testing."""
        return OdaToolManager()

    @pytest.fixture
    def mock_tool_factory(self):
        """Factory for creating mock tools with different names."""
        def _create_tool(name: str, description: str) -> BaseTool:
            tool = Mock(spec=BaseTool)
            tool.name = name
            tool.description = description
            return tool
        return _create_tool

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_empty_manager(self, tool_manager: OdaToolManager):
        """Test listing tools from empty manager."""
        # Act
        result = await tool_manager.list_tools()

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_all_tools(self, tool_manager: OdaToolManager, mock_tool_factory):
        """Test listing all tools from multiple apps."""
        # Arrange
        app1_tool1 = mock_tool_factory("tool1", "First tool")
        app1_tool2 = mock_tool_factory("tool2", "Second tool")
        app2_tool1 = mock_tool_factory("tool1", "First tool in app2")
        app3_tool1 = mock_tool_factory("tool1", "First tool in app3")

        await tool_manager.register_tool(app1_tool1, "app1", "tool1")
        await tool_manager.register_tool(app1_tool2, "app1", "tool2")
        await tool_manager.register_tool(app2_tool1, "app2", "tool1")
        await tool_manager.register_tool(app3_tool1, "app3", "tool1")

        # Act
        result = await tool_manager.list_tools()

        # Assert
        assert len(result) == 4
        assert "app1:tool1" in result
        assert "app1:tool2" in result
        assert "app2:tool1" in result
        assert "app3:tool1" in result
        assert result["app1:tool1"] is app1_tool1
        assert result["app1:tool2"] is app1_tool2
        assert result["app2:tool1"] is app2_tool1
        assert result["app3:tool1"] is app3_tool1

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_filtered_by_app(self, tool_manager: OdaToolManager, mock_tool_factory):
        """Test listing tools filtered by specific app."""
        # Arrange
        app1_tool1 = mock_tool_factory("tool1", "First tool")
        app1_tool2 = mock_tool_factory("tool2", "Second tool")
        app2_tool1 = mock_tool_factory("tool1", "First tool in app2")

        await tool_manager.register_tool(app1_tool1, "app1", "tool1")
        await tool_manager.register_tool(app1_tool2, "app1", "tool2")
        await tool_manager.register_tool(app2_tool1, "app2", "tool1")

        # Act
        result = await tool_manager.list_tools("app1")

        # Assert
        assert len(result) == 2
        assert "app1:tool1" in result
        assert "app1:tool2" in result
        assert "app2:tool1" not in result
        assert result["app1:tool1"] is app1_tool1
        assert result["app1:tool2"] is app1_tool2

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_non_existing_app(self, tool_manager: OdaToolManager, mock_tool_factory):
        """Test listing tools from non-existing app."""
        # Arrange
        tool = mock_tool_factory("tool1", "Test tool")
        await tool_manager.register_tool(tool, "app1", "tool1")

        # Act
        result = await tool_manager.list_tools("non_existing_app")

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_with_functions(self, tool_manager: OdaToolManager):
        """Test listing tools that were registered via register_function."""
        # Arrange
        def test_function(param: str) -> dict:
            """Test function."""
            return {"result": param}

        await tool_manager.register_function(test_function, "app1", "func_tool")

        def another_function(param: int) -> int:
            """Another test function."""
            return param * 2

        await tool_manager.register_function(another_function, "app2", "calc_tool")

        # Act
        result = await tool_manager.list_tools()

        # Assert
        assert len(result) == 2
        assert "app1:func_tool" in result
        assert "app2:calc_tool" in result
        assert isinstance(result["app1:func_tool"], FunctionTool)
        assert isinstance(result["app2:calc_tool"], FunctionTool)
        assert result["app1:func_tool"].func is test_function
        assert result["app2:calc_tool"].func is another_function

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_mixed_registration(self, tool_manager: OdaToolManager, mock_tool_factory):
        """Test listing tools from both register_tool and register_function."""
        # Arrange
        # Register tool directly
        direct_tool = mock_tool_factory("direct_tool", "Directly registered tool")
        await tool_manager.register_tool(direct_tool, "app1", "direct")

        # Register function
        def func_tool(param: str) -> dict:
            """Function tool."""
            return {"result": param}

        await tool_manager.register_function(func_tool, "app1", "func")

        # Act
        result = await tool_manager.list_tools("app1")

        # Assert
        assert len(result) == 2
        assert "app1:direct" in result
        assert "app1:func" in result
        assert result["app1:direct"] is direct_tool
        assert isinstance(result["app1:func"], FunctionTool)
        assert result["app1:func"].func is func_tool

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_order_consistency(self, tool_manager: OdaToolManager, mock_tool_factory):
        """Test that listing tools returns consistent order."""
        # Arrange
        tools = []
        for i in range(5):
            tool = mock_tool_factory(f"tool{i}", f"Tool {i}")
            tools.append(tool)
            await tool_manager.register_tool(tool, "app1", f"tool{i}")

        # Act
        result1 = await tool_manager.list_tools("app1")
        result2 = await tool_manager.list_tools("app1")

        # Assert
        assert len(result1) == 5
        assert len(result2) == 5
        # Check that both results contain same keys
        assert set(result1.keys()) == set(result2.keys())
        # Check that both results contain same values
        for key in result1:
            assert result1[key] is result2[key]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_tools_empty_app_name(self, tool_manager: OdaToolManager, mock_tool_factory):
        """Test listing tools with empty app_name."""
        # Arrange
        tool = mock_tool_factory("tool1", "Test tool")
        await tool_manager.register_tool(tool, "app1", "tool1")

        # Act
        result = await tool_manager.list_tools("")

        # Assert - Empty app_name should return empty dict
        assert len(result) == 0