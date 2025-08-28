"""Integration tests for OdaToolManager register_function with real LLM.

Tests register Python functions as FunctionTool instances, and then test
complete integration with OdaAgent and real LLM.
"""

import asyncio
import os

import pytest
import pytest_asyncio
from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from one_dragon_agent.core.agent.config.oda_agent_config import (
    create_default_agent_config,
)
from one_dragon_agent.core.agent.oda_agent import OdaAgent
from one_dragon_agent.core.context.oda_context_config import OdaContextConfig
from one_dragon_agent.core.model.in_memory_oda_model_config_storage import (
    InMemoryOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager
from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager

# Fixed weather data for testing purposes
WEATHER_DATA = {
    "beijing": "sunny, 25°C",
    "shanghai": "cloudy, 22°C",
    "guangzhou": "rainy, 28°C",
    "shenzhen": "partly cloudy, 30°C",
    "hangzhou": "sunny, 24°C",
}


def get_weather(city: str) -> str:
    """
    Get weather information for a specified city

    Args:
        city: name of the city to get weather for

    Returns:
        str: weather information for the city
    """
    # Convert to lowercase for case-insensitive matching
    city_key = city.lower()

    # Get weather data or return default for unknown cities
    weather = WEATHER_DATA.get(city_key, "sunny, 20°C")

    return f"Weather in {city}: {weather}"


async def async_get_weather(city: str) -> str:
    """
    Async version of get_weather function for testing async function registration

    Args:
        city: name of the city to get weather for

    Returns:
        str: weather information for the city
    """
    # Convert to lowercase for case-insensitive matching
    city_key = city.lower()

    # Get weather data or return default for unknown cities
    weather = WEATHER_DATA.get(city_key, "sunny, 20°C")

    return f"Weather in {city}: {weather}"


class TestOdaToolManagerRegisterFunctionIntegration:
    """Test OdaToolManager register_function integration with real LLM.
    
    This test class registers Python functions as FunctionTool instances using
    OdaToolManager, and then tests complete integration with OdaAgent and real LLM.
    """

    @pytest.fixture(scope="class")
    def required_env_vars(self):
        """Check if required environment variables are set.
        
        Returns:
            dict: Configuration dictionary containing base_url, api_key, and model
        """
        base_url = os.getenv("ODA_DEFAULT_LLM_BASE_URL")
        api_key = os.getenv("ODA_DEFAULT_LLM_API_KEY")
        if not base_url or not api_key:
            pytest.skip("ODA_DEFAULT_LLM_BASE_URL and ODA_DEFAULT_LLM_API_KEY environment variables are required")
        return {
            "base_url": base_url,
            "api_key": api_key,
            "model": os.getenv("ODA_DEFAULT_LLM_MODEL"),
        }

    @pytest_asyncio.fixture(scope="class")
    async def test_setup(self, required_env_vars):
        """Create complete test setup with OdaToolManager and OdaAgent.

        Args:
            required_env_vars: Environment configuration for LLM

        Returns:
            dict: Complete test setup including OdaAgent and OdaToolManager
        """
        # Create OdaToolManager
        tool_manager = OdaToolManager()

        # Register the get_weather function as a FunctionTool
        app_name = "test_function_tool_app"
        await tool_manager.register_function(
            func=get_weather,
            app_name=app_name,
            tool_id="get_weather_tool"
        )
        
        # Register the async_get_weather function as a FunctionTool
        await tool_manager.register_function(
            func=async_get_weather,
            app_name=app_name,
            tool_id="async_get_weather_tool"
        )

        # Create OdaContext configuration
        context_config = OdaContextConfig(
            default_llm_base_url=required_env_vars["base_url"],
            default_llm_api_key=required_env_vars["api_key"],
            default_llm_model=required_env_vars["model"],
        )

        # Create model config manager
        model_config_service = InMemoryOdaModelConfigStorage()
        model_config_manager = OdaModelConfigManager(
            config_service=model_config_service,
            context_config=context_config
        )

        yield {
            "tool_manager": tool_manager,
            "app_name": app_name,
            "tool_id": "get_weather_tool",
            "async_tool_id": "async_get_weather_tool",
            "model_config_manager": model_config_manager
        }

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_register_function_tool_creation(self, test_setup):
        """Test FunctionTool creation with register_function.
        
        This test validates that OdaToolManager can successfully create
        a FunctionTool from a Python function.
        """
        tool_manager = test_setup["tool_manager"]
        app_name = test_setup["app_name"]
        tool_id = test_setup["tool_id"]

        # Get the tool instance
        tool = await tool_manager.get_tool(app_name, tool_id)

        # Validate tool was created
        assert tool is not None, "FunctionTool should be created"
        assert hasattr(tool, "func"), "Tool should have func attribute"

        # Test the function directly
        if asyncio.iscoroutinefunction(tool.func):
            result = await tool.func("Beijing")
        else:
            result = tool.func("Beijing")
        assert result == "Weather in Beijing: sunny, 25°C", f"Function should return expected result, got: {result}"

        print("Successfully created FunctionTool with register_function")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_register_async_function_tool_creation(self, test_setup):
        """Test FunctionTool creation with register_function for async functions.
        
        This test validates that OdaToolManager can successfully create
        a FunctionTool from an async Python function.
        """
        tool_manager = test_setup["tool_manager"]
        app_name = test_setup["app_name"]
        async_tool_id = test_setup["async_tool_id"]

        # Get the tool instance
        tool = await tool_manager.get_tool(app_name, async_tool_id)

        # Validate tool was created
        assert tool is not None, "FunctionTool should be created"
        assert hasattr(tool, "func"), "Tool should have func attribute"

        # Test the function directly
        if asyncio.iscoroutinefunction(tool.func):
            result = await tool.func("Beijing")
        else:
            result = tool.func("Beijing")
        assert result == "Weather in Beijing: sunny, 25°C", f"Function should return expected result, got: {result}"

        print("Successfully created async FunctionTool with register_function")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_oda_agent_with_sync_function_tool(self, test_setup):
        """Test OdaAgent integration with synchronous FunctionTool from register_function.
        
        This test validates that OdaAgent can successfully use synchronous tools
        created from Python functions through OdaToolManager register_function.
        """
        tool_manager = test_setup["tool_manager"]
        app_name = test_setup["app_name"]
        tool_id = test_setup["tool_id"]

        # Get the FunctionTool
        function_tool = await tool_manager.get_tool(app_name, tool_id)

        # Create LlmAgent with FunctionTool
        model_config = test_setup["model_config_manager"].get_default_config()
        glm_model = LiteLlm(
            model=f'hosted_vllm/{model_config.model}',
            api_base=model_config.base_url,
            api_key=model_config.api_key,
        )

        # Create LlmAgent with FunctionTool
        agent_config = create_default_agent_config(app_name)
        llm_agent_with_tools = LlmAgent(
            name=f"{agent_config.agent_name}_with_sync_function_tool",
            model=glm_model,
            instruction=agent_config.instruction,
            tools=[function_tool]  # Add only the sync FunctionTool here
        )

        # Create Runner with tool-enhanced agent
        session_service = InMemorySessionService()
        runner_with_tools = Runner(
            agent=llm_agent_with_tools,
            app_name=app_name,
            session_service=session_service,
        )

        # Create session
        user_id = "test_sync_function_user"
        session_id = "test_sync_function_session"
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

        # Create OdaAgent with tools
        oda_agent_with_tools = OdaAgent(
            runner=runner_with_tools,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            max_retries=1
        )

        # Test: Use FunctionTool through OdaAgent
        event_count = 0
        final_response_found = False
        response_content = None

        test_message = "Please use the get_weather tool to get weather for Beijing"

        async for event in oda_agent_with_tools.run_async(test_message):
            event_count += 1
            assert isinstance(event, Event), f"Event should be Event instance, got {type(event)}"

            if event.is_final_response():
                final_response_found = True
                if event.content and event.content.parts:
                    assert len(event.content.parts) > 0, "Final response should have content parts"
                    response_content = event.content.parts[0].text
                    print(f"Sync FunctionTool response: {response_content}")

                    # Response should contain weather information for Beijing
                    # The LLM might format the response differently, so we check for key elements
                    assert "Beijing" in response_content, \
                        f"Response should contain Beijing, got: {response_content}"
                    # Should also contain the fixed weather data
                    assert "sunny" in response_content.lower() and "25" in response_content, \
                        f"Response should contain weather data (sunny, 25), got: {response_content}"

        # Validate execution
        assert event_count > 0, "Should have received at least one event"
        assert final_response_found, "Should have found a final response event"
        assert response_content is not None, "Should have received response content"

        print("Successfully tested OdaAgent with synchronous FunctionTool from register_function")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_oda_agent_with_async_function_tool(self, test_setup):
        """Test OdaAgent integration with asynchronous FunctionTool from register_function.
        
        This test validates that OdaAgent can successfully use asynchronous tools
        created from Python functions through OdaToolManager register_function.
        """
        tool_manager = test_setup["tool_manager"]
        app_name = test_setup["app_name"]
        async_tool_id = test_setup["async_tool_id"]

        # Get the FunctionTool
        async_function_tool = await tool_manager.get_tool(app_name, async_tool_id)

        # Create LlmAgent with FunctionTool
        model_config = test_setup["model_config_manager"].get_default_config()
        glm_model = LiteLlm(
            model=f'hosted_vllm/{model_config.model}',
            api_base=model_config.base_url,
            api_key=model_config.api_key,
        )

        # Create LlmAgent with FunctionTool
        agent_config = create_default_agent_config(app_name)
        llm_agent_with_tools = LlmAgent(
            name=f"{agent_config.agent_name}_with_async_function_tool",
            model=glm_model,
            instruction=agent_config.instruction,
            tools=[async_function_tool]  # Add only the async FunctionTool here
        )

        # Create Runner with tool-enhanced agent
        session_service = InMemorySessionService()
        runner_with_tools = Runner(
            agent=llm_agent_with_tools,
            app_name=app_name,
            session_service=session_service,
        )

        # Create session
        user_id = "test_async_function_user"
        session_id = "test_async_function_session"
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

        # Create OdaAgent with tools
        oda_agent_with_tools = OdaAgent(
            runner=runner_with_tools,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            max_retries=1
        )

        # Test: Use FunctionTool through OdaAgent
        event_count = 0
        final_response_found = False
        response_content = None

        test_message = "Please use the async_get_weather tool to get weather for Beijing"

        async for event in oda_agent_with_tools.run_async(test_message):
            event_count += 1
            assert isinstance(event, Event), f"Event should be Event instance, got {type(event)}"

            if event.is_final_response():
                final_response_found = True
                if event.content and event.content.parts:
                    assert len(event.content.parts) > 0, "Final response should have content parts"
                    response_content = event.content.parts[0].text
                    print(f"Async FunctionTool response: {response_content}")

                    # Response should contain weather information for Beijing
                    # The LLM might format the response differently, so we check for key elements
                    assert "Beijing" in response_content, \
                        f"Response should contain Beijing, got: {response_content}"
                    # Should also contain the fixed weather data
                    assert "sunny" in response_content.lower() and "25" in response_content, \
                        f"Response should contain weather data (sunny, 25), got: {response_content}"

        # Validate execution
        assert event_count > 0, "Should have received at least one event"
        assert final_response_found, "Should have found a final response event"
        assert response_content is not None, "Should have received response content"

        print("Successfully tested OdaAgent with asynchronous FunctionTool from register_function")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_function_tool_listing_and_accessibility(self, test_setup):
        """Test that FunctionTool is properly listed and accessible.
        
        This test validates that FunctionTool created by register_function is properly
        exposed and can be listed and accessed through ADK framework.
        """
        tool_manager = test_setup["tool_manager"]
        app_name = test_setup["app_name"]
        tool_id = test_setup["tool_id"]
        async_tool_id = test_setup["async_tool_id"]
        
        # Expected number of tools
        EXPECTED_TOOL_COUNT = 2

        # List all tools
        all_tools = await tool_manager.list_tools()
        assert isinstance(all_tools, dict), "Tools should be returned as dict"
        assert len(all_tools) == EXPECTED_TOOL_COUNT, f"Should have exactly {EXPECTED_TOOL_COUNT} tools, got {len(all_tools)}"

        # Get tool by app name
        app_tools = await tool_manager.list_tools(app_name)
        assert isinstance(app_tools, dict), "App tools should be returned as dict"
        assert len(app_tools) == EXPECTED_TOOL_COUNT, f"Should have exactly {EXPECTED_TOOL_COUNT} tools for app, got {len(app_tools)}"

        # Validate FunctionTools
        global_id = tool_manager.get_global_identifier(app_name, tool_id)
        async_global_id = tool_manager.get_global_identifier(app_name, async_tool_id)
        
        assert global_id in all_tools, f"Global identifier {global_id} should be in tools list"
        assert async_global_id in all_tools, f"Global identifier {async_global_id} should be in tools list"
        
        function_tool = all_tools[global_id]
        async_function_tool = all_tools[async_global_id]
        
        assert hasattr(function_tool, "func"), "Tool should have func attribute"
        assert hasattr(async_function_tool, "func"), "Async tool should have func attribute"
        
        assert function_tool.func == get_weather, "Tool func should match original function"
        assert async_function_tool.func == async_get_weather, "Async tool func should match original async function"

        print("Successfully validated FunctionTool listing and accessibility")