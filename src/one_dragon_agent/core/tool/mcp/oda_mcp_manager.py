
from google.adk.tools.mcp_tool.mcp_session_manager import (
    SseConnectionParams,
    StdioConnectionParams,
    StreamableHTTPConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

from one_dragon_agent.core.system import log

from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_config_storage import BaseOdaMcpStorage

logger = log.get_logger(__name__)


class OdaMcpManager:
    """MCP configuration manager that handles the complete lifecycle of MCP tool configurations.
    
    This manager is held by OdaToolManager and is responsible for managing both built-in 
    and custom MCP configurations. Built-in configurations are registered at startup and 
    managed in memory without persistence. Custom configurations are registered dynamically 
    at runtime and require persistence.
    """
    
    def __init__(self, custom_config_storage: BaseOdaMcpStorage):
        """Initializes the OdaMcpManager.
        
        Creates separate storage for built-in configurations and initializes the 
        custom configuration storage service.
        
        Args:
            custom_config_storage: Custom configuration storage service instance
        """
        # Built-in config memory storage
        self._build_in_configs: dict[str, OdaMcpConfig] = {}
        
        # Custom config storage service
        self._custom_config_storage: BaseOdaMcpStorage = custom_config_storage
        
    async def register_build_in_config(self, config: OdaMcpConfig) -> None:
        """Registers a built-in MCP configuration (stored in separate memory, no persistence needed).
        
        Args:
            config: MCP configuration object.
            
        Raises:
            ValueError: If configuration parameters are invalid or conflicting.
        """
        # 验证配置参数
        self._validate_config(config)
        
        # 生成全局唯一标识符
        global_id = config.get_global_id()
        
        # 检查配置唯一性
        if global_id in self._build_in_configs:
            raise ValueError(f"Built-in config with ID '{global_id}' already exists")
            
        # 保存到独立内存存储
        self._build_in_configs[global_id] = config
        logger.info(f"Registered built-in MCP config: {global_id}")
        
    async def register_custom_config(self, config: OdaMcpConfig) -> None:
        """Registers a custom MCP configuration (requires persistence).
        
        Args:
            config: MCP configuration object.
            
        Raises:
            ValueError: If configuration parameters are invalid or conflicting.
        """
        # 验证配置参数
        self._validate_config(config)
        
        # 生成全局唯一标识符
        global_id = config.get_global_id()
        
        # 保存到持久化存储
        await self._custom_config_storage.create_config(config)
        logger.info(f"Registered custom MCP config: {global_id}")
        
    async def unregister_build_in_config(self, app_name: str, mcp_id: str) -> None:
        """Unregisters a built-in MCP configuration.
        
        Args:
            app_name: Application name.
            mcp_id: MCP identifier.
            
        Raises:
            PermissionError: Built-in configurations are typically not allowed to be deleted.
        """
        global_id = self._generate_global_id(app_name, mcp_id)
        
        # 内置配置通常不允许删除
        if global_id in self._build_in_configs:
            raise PermissionError("Built-in configurations cannot be unregistered")
            
        logger.warning(f"Attempted to unregister non-existent built-in config: {global_id}")
        
    async def unregister_custom_config(self, app_name: str, mcp_id: str) -> None:
        """Unregisters a custom MCP configuration.
        
        Args:
            app_name: Application name.
            mcp_id: MCP identifier.
        """
        global_id = self._generate_global_id(app_name, mcp_id)
        
        # 从持久化存储删除
        await self._custom_config_storage.delete_config(global_id)
        logger.info(f"Unregistered custom MCP config: {global_id}")
        
    async def get_mcp_config(self, app_name: str, mcp_id: str) -> OdaMcpConfig | None:
        """Gets an MCP configuration (supports querying both built-in and custom configurations).
        
        Args:
            app_name: Application name.
            mcp_id: MCP identifier.
            
        Returns:
            MCP configuration object or None.
        """
        global_id = self._generate_global_id(app_name, mcp_id)
        
        # 优先从内置配置中查找
        if global_id in self._build_in_configs:
            return self._build_in_configs[global_id]
            
        # 然后从自定义配置中查找
        return await self._custom_config_storage.get_config(global_id)
        
    async def list_mcp_configs(self, app_name: str) -> dict[str, OdaMcpConfig]:
        """Lists all MCP configurations (including both built-in and custom configurations).
        
        Args:
            app_name: Application name filter.
            
        Returns:
            Configuration dictionary with global identifiers as keys (app_name:mcp_id).
        """
        configs: dict[str, OdaMcpConfig] = {}
        
        # 获取内置配置
        for global_id, config in self._build_in_configs.items():
            if config.app_name == app_name:
                configs[global_id] = config
                
        # 获取自定义配置
        all_custom_configs = await self._custom_config_storage.list_configs()
        for config in all_custom_configs:
            if config.app_name == app_name:
                global_id = config.get_global_id()
                configs[global_id] = config
        
        return configs
        
    async def update_custom_config(self, app_name: str, mcp_id: str, config: OdaMcpConfig) -> None:
        """Updates a custom MCP configuration (built-in configurations cannot be updated).
        
        Args:
            app_name: Application name.
            mcp_id: MCP identifier.
            config: New MCP configuration object.
            
        Raises:
            ValueError: If configuration parameters are invalid or MCP configuration does not exist.
            PermissionError: If trying to update a built-in configuration.
        """
        global_id = self._generate_global_id(app_name, mcp_id)
        
        # 验证配置参数
        self._validate_config(config)
        
        # 检查配置类型 - 如果是内置配置则拒绝更新
        if global_id in self._build_in_configs:
            raise PermissionError("Cannot update built-in configurations")
            
        # 检查配置是否存在
        existing_config = await self._custom_config_storage.get_config(global_id)
        if existing_config is None:
            raise ValueError(f"Custom config with ID '{global_id}' does not exist")
            
        # 更新配置参数
        await self._custom_config_storage.update_config(config)
        logger.info(f"Updated custom MCP config: {global_id}")
        
    def _generate_global_id(self, app_name: str, mcp_id: str) -> str:
        """Generates a globally unique identifier.
        
        Args:
            app_name: Application name.
            mcp_id: MCP identifier.
            
        Returns:
            Globally unique identifier in the format "app_name:mcp_id".
        """
        return f"{app_name}:{mcp_id}"
    
    async def create_mcp_toolset(self, app_name: str, mcp_id: str) -> MCPToolset:
        """Creates an MCPToolset instance that can be used directly as a toolset.
        
        Args:
            app_name: Application name.
            mcp_id: MCP identifier.
            
        Returns:
            MCPToolset instance that can be used directly in LlmAgent.
            
        Raises:
            ValueError: If MCP configuration is not found or invalid.
            RuntimeError: If MCPToolset creation fails.
        """
        # Get MCP configuration
        mcp_config = await self.get_mcp_config(app_name, mcp_id)
        if mcp_config is None:
            raise ValueError(f"MCP config '{mcp_id}' not found for app '{app_name}'")
        
        logger.info(f"Creating MCPToolset instance for {app_name}:{mcp_id}")
        
        # Create connection parameters based on server type
        if mcp_config.server_type == "stdio":
            connection_params = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=mcp_config.command,
                    args=mcp_config.args,
                )
            )
        elif mcp_config.server_type == "sse":
            connection_params = SseConnectionParams(
                url=mcp_config.url,
                headers=mcp_config.headers
            )
        elif mcp_config.server_type == "http":
            connection_params = StreamableHTTPConnectionParams(
                url=mcp_config.url,
                headers=mcp_config.headers
            )
        else:
            raise ValueError(f"Unsupported server type: {mcp_config.server_type}")
        
        try:
            # Create MCPToolset directly according to ADK API
            tool_filter = None
            if hasattr(mcp_config, 'tool_filter') and mcp_config.tool_filter:
                tool_filter = mcp_config.tool_filter

            toolset = MCPToolset(
                connection_params=connection_params,
                tool_filter=tool_filter
            )

            logger.info(f"Created MCPToolset instance for {app_name}:{mcp_id}")
            return toolset
            
        except Exception as e:
            logger.error(f"Failed to create MCPToolset instance for {app_name}:{mcp_id}: {e}")
            raise RuntimeError(f"Failed to create MCPToolset instance: {e}") from None
    
            
    def _validate_config(self, config: OdaMcpConfig) -> None:
        """Validates MCP configuration parameters.
        
        Args:
            config: MCP configuration object.
            
        Raises:
            ValueError: If configuration parameters are invalid.
        """
        # 配置参数验证和标准化
        config._validate_config()