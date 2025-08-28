"""Integration tests for OdaMcpManager with stdio MCP server.

Tests create a real stdio MCP server, connect to it using McpToolSet,
and then test complete integration with OdaAgent and real LLM.
"""

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
from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_config_storage import InMemoryOdaMcpStorage
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager


class TestOdaMcpManagerStdioIntegration:
    """Test OdaMcpManager with stdio MCP server integration.
    
    This test class creates stdio MCP server configurations, uses McpToolSet to connect
    to them (which automatically starts stdio servers), and then tests complete
    integration with OdaAgent and real LLM.
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
            "model": os.getenv("ODA_DEFAULT_LLM_MODEL", "gemini-2.0-flash")
        }
    
    @pytest_asyncio.fixture(scope="class")
    async def test_setup(self, required_env_vars):
        """Create complete test setup with stdio MCP server and OdaAgent.
        
        Args:
            required_env_vars: Environment configuration for LLM
            
        Returns:
            dict: Complete test setup including OdaAgent and MCP configuration
        """
        # Create OdaMcpManager with in-memory storage
        storage = InMemoryOdaMcpStorage()
        mcp_manager = OdaMcpManager(custom_config_storage=storage)
        
        # Create MCP configuration for stdio server (auto-started by MCPToolSet)
        app_name = "test_stdio_app"
        mcp_config = OdaMcpConfig(
            mcp_id="stdio_weather_server",
            app_name=app_name,
            name="Stdio Weather MCP Server",
            description="Stdio MCP server with weather functionality",
            server_type="stdio",
            command="python",
            args=[os.path.join(os.path.dirname(__file__), "stdio_mcp_server.py")],
            timeout=30
        )
        
        await mcp_manager.register_custom_config(mcp_config)
        
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

        return {
            "mcp_manager": mcp_manager,
            "app_name": app_name,
            "mcp_id": "stdio_weather_server",
            "model_config_manager": model_config_manager
        }
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_stdio_mcp_toolset_creation(self, test_setup):
        """Test McpToolSet creation with stdio MCP server (auto-started).
        
        This test validates that OdaMcpManager can successfully create
        an MCPToolset that automatically starts a real stdio MCP server.
        """
        mcp_manager = test_setup["mcp_manager"]
        app_name = test_setup["app_name"]
        mcp_id = test_setup["mcp_id"]
        
        # Create MCPToolset (this will automatically start MCP server)
        toolset = await mcp_manager.create_mcp_toolset(app_name, mcp_id)
        
        # Validate toolset was created
        assert toolset is not None, "MCPToolset should be created"
        assert hasattr(toolset, "tool_filter"), "Toolset should have tool_filter"
        
        # Get tools from toolset
        tools = await toolset.get_tools()
        assert isinstance(tools, list), "Tools should be returned as list"
        assert len(tools) > 0, "Should have at least one tool available"
        
        # Find weather tool
        weather_tool = None
        for tool in tools:
            if tool.name == "get_weather":
                weather_tool = tool
                break

        assert weather_tool is not None, "Weather tool should be available"
        assert "Get weather information for a city" in weather_tool.description, \
            f"Tool description should match, got: {weather_tool.description}"
        
        print("Successfully created stdio MCPToolset with auto-started real MCP server")
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_oda_agent_with_stdio_mcp_tools(self, test_setup):
        """Test OdaAgent integration with stdio MCP tools from real server.
        
        This test validates that OdaAgent can successfully use tools
        from a real stdio MCP server through McpToolSet integration.
        """
        mcp_manager = test_setup["mcp_manager"]
        app_name = test_setup["app_name"]
        mcp_id = test_setup["mcp_id"]
        
        # Create MCPToolset
        toolset = await mcp_manager.create_mcp_toolset(app_name, mcp_id)
        
        # Create LlmAgent with MCP tools
        model_config = test_setup["model_config_manager"].get_default_config()
        llm = LiteLlm(
            model=f"openai/{model_config.model}",
            api_base=model_config.base_url,
            api_key=model_config.api_key,
        )

        # Create LlmAgent with MCP toolset
        agent_config = create_default_agent_config(app_name)
        llm_agent_with_tools = LlmAgent(
            name=f"{agent_config.agent_name}_with_stdio_tools",
            model=llm,
            instruction=agent_config.instruction,
            tools=[toolset]  # Add MCP toolset here
        )
        
        # Create Runner with tool-enhanced agent
        session_service = InMemorySessionService()
        runner_with_tools = Runner(
            agent=llm_agent_with_tools,
            app_name=app_name,
            session_service=session_service,
        )
        
        # Create session
        user_id = "test_stdio_user"
        session_id = "test_stdio_session"
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        
        # Create OdaAgent with tools
        oda_agent_with_tools = OdaAgent(
            runner=runner_with_tools,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            max_retries=1
        )
        
        # Test: Use MCP weather tool through OdaAgent
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
                    print(f"Stdio MCP tool response: {response_content}")
                    
                    # Response should contain weather information for Beijing
                    assert "Weather in Beijing" in response_content, \
                        f"Response should contain weather for Beijing, got: {response_content}"
                    # Should also contain the fixed weather data
                    assert "sunny, 25°C" in response_content, \
                        f"Response should contain fixed weather data, got: {response_content}"
        
        # Validate execution
        assert event_count > 0, "Should have received at least one event"
        assert final_response_found, "Should have found a final response event"
        assert response_content is not None, "Should have received response content"
        
        print("Successfully tested OdaAgent with stdio MCP tools from real server")
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_stdio_mcp_tool_listing_and_accessibility(self, test_setup):
        """Test that stdio MCP tools are properly listed and accessible.
        
        This test validates that stdio MCP server's tools are properly
        exposed and can be listed and accessed through ADK framework.
        """
        mcp_manager = test_setup["mcp_manager"]
        app_name = test_setup["app_name"]
        mcp_id = test_setup["mcp_id"]
        
        # Create MCPToolset
        toolset = await mcp_manager.create_mcp_toolset(app_name, mcp_id)
        
        # Get tools from toolset
        tools = await toolset.get_tools()
        
        # Validate tools are available
        assert isinstance(tools, list), "Tools should be returned as list"
        assert len(tools) == 1, f"Should have exactly 1 tool, got {len(tools)}"
        
        # Validate weather tool
        weather_tool = tools[0]
        assert weather_tool.name == "get_weather", f"Tool name should be 'get_weather', got: {weather_tool.name}"

        print("Successfully validated stdio MCP tool listing and accessibility")
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_stdio_mcp_server_reconnection(self, test_setup):
        """Test stdio MCP server reconnection and stability.
        
        This test validates that stdio MCP connection remains stable
        across multiple tool calls.
        """
        mcp_manager = test_setup["mcp_manager"]
        app_name = test_setup["app_name"]
        mcp_id = test_setup["mcp_id"]
        
        # Create MCPToolset
        toolset = await mcp_manager.create_mcp_toolset(app_name, mcp_id)
        
        # Create LlmAgent with MCP tools
        model_config = test_setup["model_config_manager"].get_default_config()
        llm = LiteLlm(
            model=f'hosted_vllm/{model_config.model}',
            api_base=model_config.base_url,
            api_key=model_config.api_key,
        )
        
        # Create LlmAgent with MCP toolset
        agent_config = create_default_agent_config(app_name)
        llm_agent_with_tools = LlmAgent(
            name=f"{agent_config.agent_name}_with_stdio_tools",
            model=llm,
            instruction=agent_config.instruction,
            tools=[toolset]
        )
        
        # Create Runner with tool-enhanced agent
        session_service = InMemorySessionService()
        runner_with_tools = Runner(
            agent=llm_agent_with_tools,
            app_name=app_name,
            session_service=session_service,
        )
        
        # Create session
        user_id = "test_stdio_reconnect_user"
        session_id = "test_stdio_reconnect_session"
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        
        # Create OdaAgent with tools
        oda_agent_with_tools = OdaAgent(
            runner=runner_with_tools,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            max_retries=1
        )
        
        # Perform multiple tool calls
        test_messages = [
            "Get weather for Beijing",
            "Get weather for Shanghai", 
            "Get weather for Guangzhou"
        ]
        
        responses = []
        
        expected_responses = [
            "sunny, 25°C",
            "cloudy, 22°C", 
            "rainy, 28°C"
        ]
        
        for i, message in enumerate(test_messages):
            event_count = 0
            final_response_found = False
            response_content = None
            
            async for event in oda_agent_with_tools.run_async(f"Please {message}"):
                event_count += 1
                
                if event.is_final_response():
                    final_response_found = True
                    if event.content and event.content.parts:
                        response_content = event.content.parts[0].text
                        responses.append(response_content)
            
            # Validate each request
            assert event_count > 0, f"Should have received events for message {i+1}"
            assert final_response_found, f"Should have final response for message {i+1}"
            assert response_content is not None, f"Should have response for message {i+1}"
            assert expected_responses[i] in response_content, f"Response {i+1} should contain expected weather data"
        
        # Validate all responses
        assert len(responses) == len(test_messages), "Should have response for each message"
        
        for i, (expected_response, response) in enumerate(zip(expected_responses, responses, strict=False)):
            assert expected_response in response, f"Response {i+1} should contain expected weather data"
        
        print("Successfully tested stdio MCP server reconnection and stability")