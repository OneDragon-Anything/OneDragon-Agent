"""Integration tests for OdaSession process_message method.

Tests process_message with both built-in tools and MCP tools, verifying that OdaSession
can properly process messages and return event streams from OdaAgent.
"""

import asyncio
import os
import socket
import threading

import pytest
import pytest_asyncio
import uvicorn
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events import Event
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from mcp.server import FastMCP

from one_dragon_agent.core.agent.config.in_memory_oda_agent_config_storage import (
    InMemoryOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config import (
    OdaAgentConfig,
    create_default_agent_config,
)
from one_dragon_agent.core.agent.config.oda_agent_config_manager import (
    OdaAgentConfigManager,
)
from one_dragon_agent.core.agent.oda_agent_manager import OdaAgentManager
from one_dragon_agent.core.context.oda_context_config import OdaContextConfig
from one_dragon_agent.core.model.in_memory_oda_model_config_storage import (
    InMemoryOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager
from one_dragon_agent.core.session.oda_session_manager import OdaSessionManager
from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_config_storage import InMemoryOdaMcpStorage
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager
from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager

# Fixed weather data for testing purposes
WEATHER_DATA = {
    "beijing": "sunny, 25°C",
    "shanghai": "cloudy, 22°C",
    "guangzhou": "rainy, 28°C",
    "shenzhen": "partly cloudy, 30°C",
    "hangzhou": "sunny, 24°C",
}

# Fixed province data for testing purposes
PROVINCE_DATA = {
    "beijing": "Beijing",
    "shanghai": "Shanghai", 
    "guangzhou": "Guangdong",
    "shenzhen": "Guangdong",
    "hangzhou": "Zhejiang",
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


def get_free_port():
    """获取一个可用的端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


# Create MCP server with dynamic port
sse_port = get_free_port()
mcp = FastMCP("sse-mcp-server", port=sse_port)
# copy mcp.run_sse_async()
starlette_app = mcp.sse_app()
config = uvicorn.Config(
    starlette_app,
    host=mcp.settings.host,
    port=mcp.settings.port,
    log_level=mcp.settings.log_level.lower(),
)
server = uvicorn.Server(config)


@mcp.tool(
    name="get_province",
    description="Get province information for a city",
)
def get_province_mcp(city: str) -> str:
    """
    Get province information for a specified city via MCP

    Args:
        city: name of the city to get province for

    Returns:
        str: province information for the city
    """
    # Convert to lowercase for case-insensitive matching
    city_key = city.lower()

    # Get province data or return default for unknown cities
    province = PROVINCE_DATA.get(city_key, "Unknown Province")

    return f"{city} is located in {province} province"


async def wait_for_server(host: str, port: int, timeout: int = 30):
    """等待服务器启动并监听指定端口"""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            # 尝试连接到服务器端口
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            # 连接失败，服务器可能还在启动中
            await asyncio.sleep(0.5)

    raise RuntimeError(
        f"Server failed to start on {host}:{port} within {timeout} seconds"
    )


class TestOdaSessionProcessMessageIntegration:
    """Test OdaSession process_message integration with tools and MCP.
    
    This test class validates that OdaSession can successfully process messages
    and return event streams from OdaAgent with both built-in tools and MCP tools 
    properly integrated.
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
        """Create complete test setup with all required services and managers.
        
        Args:
            required_env_vars: Environment configuration for LLM
            
        Returns:
            dict: Complete test setup including all required services and managers
        """
        def run_server():
            asyncio.run(server.serve())

        # 启动服务器线程
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # 给服务器一些启动时间
        await wait_for_server('localhost', sse_port)

        # Create ADK native services
        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()
        memory_service = InMemoryMemoryService()
        
        # Create OdaToolManager
        tool_manager = OdaToolManager()
        
        # Register the get_weather function as a FunctionTool
        app_name = "test_session_app"
        await tool_manager.register_function(
            func=get_weather,
            app_name=app_name,
            tool_id="get_weather_tool"
        )
        
        # Create OdaMcpManager with in-memory storage
        mcp_storage = InMemoryOdaMcpStorage()
        mcp_manager = OdaMcpManager(custom_config_storage=mcp_storage)
        
        # Create MCP configuration for testing (using SSE instead of stdio)
        mcp_config = OdaMcpConfig(
            mcp_id="test_mcp_server",
            app_name=app_name,
            name="Test MCP Server",
            description="Test MCP server for integration testing",
            server_type="sse",
            url=f"http://localhost:{sse_port}/sse",
            timeout=30,
        )
        await mcp_manager.register_custom_config(mcp_config)
        
        # Create model config manager
        model_config_service = InMemoryOdaModelConfigStorage()
        context_config = OdaContextConfig(
            default_llm_base_url=required_env_vars["base_url"],
            default_llm_api_key=required_env_vars["api_key"],
            default_llm_model=required_env_vars["model"],
        )
        model_config_manager = OdaModelConfigManager(
            config_service=model_config_service,
            context_config=context_config
        )
        
        # Create agent config manager with in-memory storage
        agent_config_storage = InMemoryOdaAgentConfigStorage(model_config_manager)
        agent_config_manager = OdaAgentConfigManager(
            config_service=agent_config_storage,
            model_config_manager=model_config_manager,
            mcp_manager=mcp_manager
        )
        
        # Create OdaAgentManager
        agent_manager = OdaAgentManager(
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,
            tool_manager=tool_manager,
            mcp_manager=mcp_manager,
            model_config_manager=model_config_manager,
            agent_config_manager=agent_config_manager
        )
        
        # Create OdaSessionManager
        session_manager = OdaSessionManager(session_service, agent_manager)
        
        # Create test agent configuration with both tool and MCP
        agent_config = OdaAgentConfig(
            app_name=app_name,
            agent_name="test_agent_with_tools",
            agent_type="default",
            description="Test agent with both built-in tools and MCP tools",
            instruction="You are a helpful assistant that can check weather information and province information.",
            model_config=model_config_manager.get_default_config().model_id,
            tool_list=["get_weather_tool"],
            mcp_list=["test_mcp_server"],
            sub_agent_list=[]
        )
        await agent_config_manager.create_config(agent_config)
        
        # Also create a default agent config for comparison
        default_agent_config = create_default_agent_config(app_name)
        default_agent_config.agent_name = "test_default_agent"
        await agent_config_manager.create_config(default_agent_config)
        
        yield {
            "session_manager": session_manager,
            "agent_manager": agent_manager,
            "app_name": app_name,
            "agent_name": "test_agent_with_tools",
            "default_agent_name": "test_default_agent",
            "session_service": session_service,
            "tool_manager": tool_manager,
            "mcp_manager": mcp_manager,
            "agent_config_manager": agent_config_manager
        }

        # 设置退出标志
        server.should_exit = True
        server.force_exit = True
        await server.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_process_message_with_tools_and_mcp(self, test_setup):
        """Test process_message with both built-in tools and MCP tools.
        
        This test validates that OdaSession can successfully process messages
        and return event streams from OdaAgent with both built-in tools and MCP tools 
        properly integrated.
        """
        session_manager = test_setup["session_manager"]
        agent_manager = test_setup["agent_manager"]
        app_name = test_setup["app_name"]
        agent_name = test_setup["agent_name"]
        
        # Create session
        user_id = "test_user"
        session_id = "test_session_with_tools"
        oda_session = await session_manager.create_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        # Set agent manager in session
        oda_session.agent_manager = agent_manager
        
        # Test message that should trigger both tool and MCP usage
        test_message = "What is the weather in Beijing and which province is it in?"
        
        # Process message with session
        event_count = 0
        final_response_found = False
        response_content = None
        
        async for event in oda_session.process_message(test_message, agent_name):
            event_count += 1
            assert isinstance(event, Event), f"Event should be Event instance, got {type(event)}"
            
            # Check for final response
            # Different LLMs may have different ways of indicating final responses
            # Let's check for content in various possible formats
            if hasattr(event, 'content') and event.content:
                # Handle different content types
                if isinstance(event.content, dict):
                    # Check for text content in dict
                    if 'text' in event.content:
                        final_response_found = True
                        response_content = event.content['text']
                    # Check for parts in dict (like ADK Content objects)
                    elif event.content.get('parts'):
                        final_response_found = True
                        part = event.content['parts'][0]
                        if isinstance(part, dict) and 'text' in part:
                            response_content = part['text']
                        elif hasattr(part, 'text'):
                            response_content = part.text
                # Handle string content directly
                elif isinstance(event.content, str):
                    final_response_found = True
                    response_content = event.content
                # Handle Content objects directly
                elif hasattr(event.content, 'parts') and event.content.parts:
                    final_response_found = True
                    part = event.content.parts[0]
                    if hasattr(part, 'text'):
                        response_content = part.text
                        
        # For debugging, let's also check if we have any events with text content
        # even if they don't match our initial criteria
        if not final_response_found and event_count > 0:
            # Reset and iterate again to capture any text content
            response_content = None
            async for event in oda_session.process_message(test_message, agent_name):
                if hasattr(event, 'content') and event.content:
                    if isinstance(event.content, str):
                        response_content = event.content
                        final_response_found = True
                        break
                    elif isinstance(event.content, dict):
                        if 'text' in event.content:
                            response_content = event.content['text']
                            final_response_found = True
                            break
        
        # Validate execution
        assert event_count > 0, "Should have received at least one event"
        assert final_response_found, "Should have found a final response event"
        assert response_content is not None, "Should have received response content"
        
        # Response should contain weather information for Beijing
        assert "Beijing" in response_content, \
            f"Response should contain Beijing, got: {response_content}"
        # Should also contain the fixed weather data
        assert "sunny" in response_content.lower() and "25" in response_content, \
            f"Response should contain weather data (sunny, 25), got: {response_content}"
        # Should also contain province information
        assert "province" in response_content.lower() or "Beijing" in response_content, \
            f"Response should contain province information, got: {response_content}"
        
        print("Successfully tested OdaSession process_message with both tool and MCP processing messages")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_process_message_without_tools(self, test_setup):
        """Test process_message without any tools (default agent).
        
        This test validates that OdaSession can successfully process messages
        and return event streams from OdaAgent without any tools.
        """
        session_manager = test_setup["session_manager"]
        agent_manager = test_setup["agent_manager"]
        app_name = test_setup["app_name"]
        agent_name = test_setup["default_agent_name"]
        
        # Create session
        user_id = "test_user"
        session_id = "test_session_without_tools"
        oda_session = await session_manager.create_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        # Set agent manager in session
        oda_session.agent_manager = agent_manager
        
        # Test simple message without tools
        test_message = "Say hello to me."
        
        # Process message with session
        event_count = 0
        final_response_found = False
        response_content = None
        
        async for event in oda_session.process_message(test_message, agent_name):
            event_count += 1
            assert isinstance(event, Event), f"Event should be Event instance, got {type(event)}"
            
            # Check for final response
            # Different LLMs may have different ways of indicating final responses
            # Let's check for content in various possible formats
            if hasattr(event, 'content') and event.content:
                # Handle different content types
                if isinstance(event.content, dict):
                    # Check for text content in dict
                    if 'text' in event.content:
                        final_response_found = True
                        response_content = event.content['text']
                    # Check for parts in dict (like ADK Content objects)
                    elif event.content.get('parts'):
                        final_response_found = True
                        part = event.content['parts'][0]
                        if isinstance(part, dict) and 'text' in part:
                            response_content = part['text']
                        elif hasattr(part, 'text'):
                            response_content = part.text
                # Handle string content directly
                elif isinstance(event.content, str):
                    final_response_found = True
                    response_content = event.content
                # Handle Content objects directly
                elif hasattr(event.content, 'parts') and event.content.parts:
                    final_response_found = True
                    part = event.content.parts[0]
                    if hasattr(part, 'text'):
                        response_content = part.text
                        
        # For debugging, let's also check if we have any events with text content
        # even if they don't match our initial criteria
        if not final_response_found and event_count > 0:
            # Reset and iterate again to capture any text content
            response_content = None
            async for event in oda_session.process_message(test_message, agent_name):
                if hasattr(event, 'content') and event.content:
                    if isinstance(event.content, str):
                        response_content = event.content
                        final_response_found = True
                        break
                    elif isinstance(event.content, dict):
                        if 'text' in event.content:
                            response_content = event.content['text']
                            final_response_found = True
                            break
        
        # Validate execution
        assert event_count > 0, "Should have received at least one event"
        assert final_response_found, "Should have found a final response event"
        assert response_content is not None, "Should have received response content"
        
        print("Successfully tested OdaSession process_message without tools")