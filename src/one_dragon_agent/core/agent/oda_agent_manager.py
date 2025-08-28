"""OdaAgentManager - Agent Lifecycle Manager

Responsible for managing complete lifecycle of all agent instances in system,
including configuration management, instance creation, and resource management.
"""

import asyncio
from typing import TYPE_CHECKING

from google.adk.agents import LlmAgent
from google.adk.artifacts import BaseArtifactService
from google.adk.memory import BaseMemoryService
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService

from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager
from one_dragon_agent.core.system import log
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager
from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager

from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig
from one_dragon_agent.core.agent.config.oda_agent_config_manager import OdaAgentConfigManager
from one_dragon_agent.core.agent.oda_agent import OdaAgent

if TYPE_CHECKING:
    from google.adk.agents.llm_agent import ToolUnion

logger = log.get_logger(__name__)


class OdaAgentManager:
    """Agent Lifecycle Manager
    
    The core agent management component held by OdaContext, responsible for the 
    complete lifecycle management of all agent instances in the system.
    
    Attributes:
        session_service: ADK native session service for session management
        artifact_service: ADK native artifact service for artifact storage
        memory_service: ADK native memory service for long-term memory
        tool_manager: Tool manager for built-in tool management
        mcp_manager: MCP configuration and tool manager for MCP tool integration
        model_config_manager: Model configuration manager for LLM configuration
        agent_config_manager: Agent configuration manager for retrieving agent configurations
        _lock: Async lock for thread-safe operations
    """
    
    def __init__(
        self, 
        session_service: BaseSessionService,
        artifact_service: BaseArtifactService,
        memory_service: BaseMemoryService,
        tool_manager: OdaToolManager,
        mcp_manager: OdaMcpManager,
        model_config_manager: OdaModelConfigManager,
        agent_config_manager: OdaAgentConfigManager
    ) -> None:
        """Initialize OdaAgentManager with ADK service instances
        
        Args:
            session_service: ADK native session service instance
            artifact_service: ADK native artifact service instance
            memory_service: ADK native memory service instance
            tool_manager: Tool manager instance for built-in tools
            mcp_manager: MCP manager instance for MCP tools
            model_config_manager: Model configuration manager instance
            agent_config_manager: Agent configuration manager instance
        """
        self.session_service: BaseSessionService = session_service
        self.artifact_service: BaseArtifactService = artifact_service
        self.memory_service: BaseMemoryService = memory_service
        self.tool_manager: OdaToolManager = tool_manager
        self.mcp_manager: OdaMcpManager = mcp_manager
        self.model_config_manager: OdaModelConfigManager = model_config_manager
        self.agent_config_manager: OdaAgentConfigManager = agent_config_manager
        self._lock: asyncio.Lock = asyncio.Lock()
    
    
    async def create_agent(self, agent_name: str, app_name: str, user_id: str, session_id: str) -> OdaAgent:
        """Create agent instance
        
        Args:
            agent_name: Name of the agent to create
            app_name: Application name for session binding
            user_id: User identifier for session binding
            session_id: Session identifier for session binding
            
        Returns:
            OdaAgent: Created agent instance
        """
        async with self._lock:
            # Get agent configuration from OdaAgentConfigManager
            config = await self.agent_config_manager.get_config(agent_name)
            if config is None:
                raise ValueError(f"Agent config with name '{agent_name}' not found")
            
            # Validate configuration effectiveness
            await self._validate_config_effectiveness(config)
            
            # Create ADK native LlmAgent instance
            llm_agent = await self._create_llm_agent(config)
            
            # Create ADK native Runner instance
            runner = await self._create_runner(llm_agent, app_name)
            
            # Create OdaAgent wrapper instance
            oda_agent = OdaAgent(
                runner=runner,
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                max_retries=3
            )
            
            logger.info("Created agent instance: %s for session %s", agent_name, session_id)
            return oda_agent
    
    
    async def _validate_config_effectiveness(self, config: OdaAgentConfig) -> None:
        """Validate configuration effectiveness for agent creation
        
        Args:
            config: Agent configuration to validate
            
        Raises:
            ValueError: If configuration is not effective for agent creation
        """
        # Check if tool configurations exist
        for tool_id in config.tool_list:
            # Get tool instance to verify it exists
            tool_instance = await self.tool_manager.get_tool(config.app_name, tool_id)
            if tool_instance is None:
                raise ValueError(f"Tool '{tool_id}' not found for app '{config.app_name}'")
    
    async def _create_llm_agent(self, config: OdaAgentConfig) -> LlmAgent:
        """Create ADK native LlmAgent instance
        
        Args:
            config: Agent configuration
            
        Returns:
            LlmAgent: Created ADK native LlmAgent instance
        """
        # Get model configuration
        model_config = await self.model_config_manager.get_config(config.model_config)
        if model_config is None:
            raise ValueError(f"Model config '{config.model_config}' not found")
        
        # Prepare tool list
        tools: list[ToolUnion] = []
        
        # Add built-in tools
        for tool_id in config.tool_list:
            tool_instance = await self.tool_manager.get_tool(config.app_name, tool_id)
            if tool_instance is not None:
                tools.append(tool_instance)
            else:
                logger.warning(f"Tool '{tool_id}' not found for app '{config.app_name}', skipping")
        
        # Add MCP tools
        for mcp_id in config.mcp_list:
            mcp_config = await self.mcp_manager.get_mcp_config(config.app_name, mcp_id)
            if mcp_config:
                # Create MCP toolset
                try:
                    mcp_toolset = await self.mcp_manager.create_mcp_toolset(config.app_name, mcp_id)
                    tools.append(mcp_toolset)
                    
                    logger.info(f"Added MCP toolset from {mcp_id} for agent {config.agent_name}")
                except Exception as e:
                    logger.warning(f"Failed to create MCP toolset from {mcp_id}: {e}")
                    # Continue with available tools even if MCP tools fail
            else:
                logger.warning(f"MCP config {mcp_id} not found for app {config.app_name}")
        
        # Create LiteLlm model instance for ADK
        llm_model = LiteLlm(
            model=f'openai/{model_config.model}',
            api_base=model_config.base_url,
            api_key=model_config.api_key
        )
        
        # Create LlmAgent instance
        llm_agent = LlmAgent(
            name=config.agent_name,
            model=llm_model,
            instruction=config.instruction,
            tools=tools
        )
        
        return llm_agent
    
    async def _create_runner(self, llm_agent: LlmAgent, app_name: str) -> Runner:
        """Create ADK native Runner instance
        
        Args:
            llm_agent: ADK native LlmAgent instance
            app_name: Application name for session binding
            
        Returns:
            Runner: Created ADK native Runner instance
        """
        # Create Runner instance with LlmAgent
        runner = Runner(
            app_name=app_name,
            agent=llm_agent,
            session_service=self.session_service,
            artifact_service=self.artifact_service,
            memory_service=self.memory_service
        )
        
        return runner