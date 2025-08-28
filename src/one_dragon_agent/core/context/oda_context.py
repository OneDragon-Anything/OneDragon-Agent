"""OdaContext - Global Resource Manager

Responsible for initializing and managing all core services and components
during system startup, as well as resource allocation and lifecycle management.
"""


from google.adk.artifacts import BaseArtifactService, InMemoryArtifactService
from google.adk.memory import BaseMemoryService, InMemoryMemoryService
from google.adk.sessions import BaseSessionService, InMemorySessionService

from one_dragon_agent.core.agent.config.in_memory_oda_agent_config_storage import (
    InMemoryOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config_manager import (
    OdaAgentConfigManager,
)
from one_dragon_agent.core.agent.oda_agent_manager import OdaAgentManager
from one_dragon_agent.core.model.in_memory_oda_model_config_storage import (
    InMemoryOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager
from one_dragon_agent.core.session.oda_session_manager import OdaSessionManager
from one_dragon_agent.core.system.log import get_logger
from one_dragon_agent.core.tool.mcp.oda_mcp_config_storage import InMemoryOdaMcpStorage
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager
from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager

from one_dragon_agent.core.context.oda_context_config import OdaContextConfig

logger = get_logger(__name__)


class OdaContext:
    """Global Resource Manager
    
    The system's global service container and resource manager, responsible for 
    initializing and managing all core services.
    
    Attributes:
        config: Global configuration for OdaContext
        session_service: Session data storage and management infrastructure
        artifact_service: Artifact data storage and management infrastructure
        memory_service: Long-term memory management service
        model_config_manager: Model configuration manager for LLM configuration
        tool_manager: Tool manager for built-in tool management
        mcp_manager: MCP configuration and tool manager for MCP tool integration
        agent_config_manager: Agent configuration manager for retrieving agent configurations
        agent_manager: Global agent instance manager
        session_manager: Global session instance manager
    """
    
    def __init__(self, config: OdaContextConfig | None = None) -> None:
        """Initialize OdaContext instance
        
        Args:
            config: Global configuration for OdaContext. If None, will be created from environment variables.
        """
        self.config: OdaContextConfig = config or OdaContextConfig.from_env()
        self.session_service: BaseSessionService | None = None
        self.artifact_service: BaseArtifactService | None = None
        self.memory_service: BaseMemoryService | None = None
        self.model_config_manager: OdaModelConfigManager | None = None
        self.tool_manager: OdaToolManager | None = None
        self.mcp_manager: OdaMcpManager | None = None
        self.agent_config_manager: OdaAgentConfigManager | None = None
        self.agent_manager: OdaAgentManager | None = None
        self.session_manager: OdaSessionManager | None = None
    
    async def start(self) -> None:
        """Start the system and initialize all services and managers
        
        This method is the main entry point for starting the OdaContext system.
        It initializes all ADK native services and OneDragon management components
        in the correct order according to their dependencies.
        """
        await self._initialize()
    
    async def _initialize(self) -> None:
        """System initialization process
        
        Responsible for initializing all service components and management 
        components during system startup, following the initialization sequence 
        defined in the design documentation.
        """
        # Phase 1: Initialize ADK core services based on storage type
        if self.config.storage == "memory":
            # Use in-memory ADK services
            self.session_service = InMemorySessionService()
            self.artifact_service = InMemoryArtifactService()
            self.memory_service = InMemoryMemoryService()
            
            # Use in-memory storage services for OneDragon components
            model_config_service = InMemoryOdaModelConfigStorage()
            agent_config_storage = InMemoryOdaAgentConfigStorage(
                model_config_manager=self.model_config_manager
            )
            mcp_storage = InMemoryOdaMcpStorage()
        else:
            # For non-memory storage types, raise an exception as they are not yet supported
            raise ValueError(f"Storage type '{self.config.storage}' is not yet supported. Only 'memory' storage is currently supported.")
        
        # Phase 3: Initialize OneDragon management components in dependency order
        # 1. Create OdaToolManager (no dependencies)
        self.tool_manager = OdaToolManager()
        
        # 2. Create OdaMcpManager (depends on BaseOdaMcpStorage)
        self.mcp_manager = OdaMcpManager(custom_config_storage=mcp_storage)
        logger.info("OdaMcpManager created")
        
        # 3. Create OdaModelConfigManager (depends on BaseOdaModelConfigService and OdaContextConfig)
        self.model_config_manager = OdaModelConfigManager(
            config_service=model_config_service,
            context_config=self.config
        )
        logger.info("OdaModelConfigManager created")
        
        # 4. Create OdaAgentConfigManager (depends on BaseOdaAgentConfigStorage, OdaModelConfigManager and OdaMcpManager)
        self.agent_config_manager = OdaAgentConfigManager(
            config_service=agent_config_storage,
            model_config_manager=self.model_config_manager,
            mcp_manager=self.mcp_manager
        )
        logger.info("OdaAgentConfigManager created")
        
        # 5. Create OdaAgentManager (depends on MemoryService, ArtifactService, OdaToolManager, 
        #    OdaMcpManager, OdaModelConfigManager, and OdaAgentConfigManager)
        self.agent_manager = OdaAgentManager(
            session_service=self.session_service,
            artifact_service=self.artifact_service,
            memory_service=self.memory_service,
            tool_manager=self.tool_manager,
            mcp_manager=self.mcp_manager,
            model_config_manager=self.model_config_manager,
            agent_config_manager=self.agent_config_manager
        )
        logger.info("OdaAgentManager created")
        
        # 6. Create OdaSessionManager (depends on SessionService and OdaAgentManager)
        self.session_manager = OdaSessionManager(
            session_service=self.session_service,
            agent_manager=self.agent_manager
        )
        logger.info("OdaSessionManager created")
    
    async def stop(self) -> None:
        """Stop the system and release all resources
        
        This method is the main entry point for stopping the OdaContext system.
        It cleans up all resources and shuts down all services and managers.
        """
        # Clean up session manager resources
        if self.session_manager:
            # Clear all sessions and their resources
            pass  # SessionManager doesn't have a explicit cleanup method yet
        
        # Clean up agent manager resources
        if self.agent_manager:
            # OdaAgentManager doesn't have a explicit cleanup method yet
            pass
        
        # Clean up other managers
        self.session_manager = None
        self.agent_manager = None
        self.agent_config_manager = None
        self.mcp_manager = None
        self.tool_manager = None
        self.model_config_manager = None
        
        # Clean up ADK services
        self.session_service = None
        self.artifact_service = None
        self.memory_service = None
