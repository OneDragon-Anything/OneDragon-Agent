"""Test OdaToolManager register_function method."""


import pytest
from google.adk.tools import FunctionTool

from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager


class TestOdaToolManagerRegisterFunction:
    """Test cases for OdaToolManager.register_function method."""

    @pytest.fixture
    def tool_manager(self) -> OdaToolManager:
        """Create an OdaToolManager instance for testing."""
        return OdaToolManager()

    @pytest.fixture
    def sync_function(self):
        """Create a synchronous function for testing."""
        def sync_test_function(param: str) -> dict:
            """Test synchronous function."""
            return {"result": param}
        return sync_test_function

    @pytest.fixture
    def async_function(self):
        """Create an asynchronous function for testing."""
        async def async_test_function(param: str) -> dict:
            """Test asynchronous function."""
            return {"result": param}
        return async_test_function

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_sync_function_success(self, tool_manager: OdaToolManager, sync_function):
        """Test successful registration of synchronous function."""
        # Arrange
        app_name = "test_app"
        tool_id = "sync_tool"

        # Act
        await tool_manager.register_function(sync_function, app_name, tool_id)

        # Assert
        registered_tool = await tool_manager.get_tool(app_name, tool_id)
        assert registered_tool is not None
        assert isinstance(registered_tool, FunctionTool)
        assert registered_tool.func is sync_function
        assert registered_tool.name == "sync_test_function"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_async_function_success(self, tool_manager: OdaToolManager, async_function):
        """Test successful registration of asynchronous function."""
        # Arrange
        app_name = "test_app"
        tool_id = "async_tool"

        # Act
        await tool_manager.register_function(async_function, app_name, tool_id)

        # Assert
        registered_tool = await tool_manager.get_tool(app_name, tool_id)
        assert registered_tool is not None
        assert isinstance(registered_tool, FunctionTool)
        assert registered_tool.func is async_function
        assert registered_tool.name == "async_test_function"

    
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_function_non_callable(self, tool_manager: OdaToolManager):
        """Test function registration fails with non-callable object."""
        # Arrange
        app_name = "test_app"
        tool_id = "invalid_tool"
        not_callable = "not_a_function"

        # Act & Assert
        with pytest.raises(TypeError, match="func must be callable"):
            await tool_manager.register_function(not_callable, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_function_empty_app_name(self, tool_manager: OdaToolManager, sync_function):
        """Test function registration fails with empty app_name."""
        # Arrange
        app_name = ""
        tool_id = "test_tool"

        # Act & Assert
        with pytest.raises(ValueError, match="app_name cannot be empty"):
            await tool_manager.register_function(sync_function, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_function_empty_tool_id(self, tool_manager: OdaToolManager, sync_function):
        """Test function registration fails with empty tool_id."""
        # Arrange
        app_name = "test_app"
        tool_id = ""

        # Act & Assert
        with pytest.raises(ValueError, match="tool_id cannot be empty"):
            await tool_manager.register_function(sync_function, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_function_duplicate_id_same_app(self, tool_manager: OdaToolManager, sync_function):
        """Test function registration fails when tool_id already exists in same app."""
        # Arrange
        app_name = "test_app"
        tool_id = "duplicate_tool"

        # Register first function
        await tool_manager.register_function(sync_function, app_name, tool_id)

        # Act & Assert - Register second function with same id
        with pytest.raises(ValueError, match="Tool with ID 'test_app:duplicate_tool' already exists"):
            await tool_manager.register_function(sync_function, app_name, tool_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_function_docstring_as_description(self, tool_manager: OdaToolManager):
        """Test that function docstring is used as default description."""
        # Arrange
        def function_with_doc(param: str) -> dict:
            """This is the function docstring used as description."""
            return {"result": param}

        app_name = "test_app"
        tool_id = "doc_tool"

        # Act
        await tool_manager.register_function(function_with_doc, app_name, tool_id)

        # Assert
        registered_tool = await tool_manager.get_tool(app_name, tool_id)
        assert registered_tool is not None
        assert isinstance(registered_tool, FunctionTool)
        assert registered_tool.description == "This is the function docstring used as description."

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_function_without_docstring(self, tool_manager: OdaToolManager):
        """Test function registration without docstring."""
        # Arrange
        def function_without_doc(param: str) -> dict:
            return {"result": param}

        app_name = "test_app"
        tool_id = "no_doc_tool"

        # Act
        await tool_manager.register_function(function_without_doc, app_name, tool_id)

        # Assert
        registered_tool = await tool_manager.get_tool(app_name, tool_id)
        assert registered_tool is not None
        assert isinstance(registered_tool, FunctionTool)
        # ADK provides a default description when no docstring
        assert registered_tool.description is not None
        # The actual default description can vary, just check it's a string
        assert isinstance(registered_tool.description, str)