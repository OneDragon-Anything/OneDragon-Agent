from collections.abc import Callable

from google.adk.tools import BaseTool, FunctionTool

from one_dragon_agent.core.system import log

logger = log.get_logger(__name__)


class OdaToolManager:
    """Tool manager for OneDragon-Agent that handles all ADK tool instances.
    
    This manager is held by OdaContext and is responsible for managing all ADK tool instances
    in the system. It provides standardized tool operation interfaces for upper-level 
    applications, ensuring proper allocation and efficient use of tool resources.
    
    OdaToolManager only supports code registration method. All tools must be directly 
    registered as build-in tools through code at startup. Tools are created and managed 
    based on ADK-Python's native tool classes without additional wrapper layers.
    """
    
    def __init__(self):
        """Initializes the OdaToolManager.
        
        Creates the tool registry and index structures for efficient tool management.
        """
        # Tool index - Index structure based on app_name
        self._app_index: dict[str, dict[str, BaseTool]] = {}  # app_name -> {tool_id -> BaseTool instance}
        
    async def register_tool(self, tool: BaseTool, app_name: str, tool_id: str) -> None:
        """Registers an ADK tool instance via code.
        
        Args:
            tool: The ADK tool instance to register.
            app_name: Application name for tool isolation.
            tool_id: Unique identifier for the tool, must be unique within the app_name scope.
            
        Raises:
            ValueError: If tool identifier conflicts or parameters are invalid.
            TypeError: If tool is not a BaseTool instance.
        """
        # Validate if tool is a BaseTool instance
        if not isinstance(tool, BaseTool):
            raise TypeError("tool must be an instance of BaseTool")
            
        # Validate parameters
        if not app_name:
            raise ValueError("app_name cannot be empty")
            
        if not tool_id:
            raise ValueError("tool_id cannot be empty")
            
        # Check tool identifier uniqueness within app_name scope
        if app_name in self._app_index and tool_id in self._app_index[app_name]:
            raise ValueError(f"Tool with ID '{app_name}:{tool_id}' already exists")
            
        # Add to app index
        if app_name not in self._app_index:
            self._app_index[app_name] = {}
        self._app_index[app_name][tool_id] = tool
        
        logger.info(f"Registered tool: {app_name}:{tool_id}")
        
    async def register_function(
        self, 
        func: Callable, 
        app_name: str, 
        tool_id: str
    ) -> None:
        """Registers a Python function and automatically wraps it as a FunctionTool.
        
        Args:
            func: The Python function to register (supports both sync and async functions).
            app_name: Application name for tool isolation.
            tool_id: Unique identifier for the tool, must be unique within the app_name scope.

        Raises:
            ValueError: If tool identifier conflicts or parameters are invalid.
            TypeError: If func is not callable.
        """
        # Validate if func is callable
        if not callable(func):
            raise TypeError("func must be callable")
            
        # Validate parameters
        if not app_name:
            raise ValueError("app_name cannot be empty")
            
        if not tool_id:
            raise ValueError("tool_id cannot be empty")
            
        # Automatically wrap Python function as FunctionTool
        function_tool = FunctionTool(func=func)
        
        # Register tool
        await self.register_tool(function_tool, app_name, tool_id)
        
    async def list_tools(self, app_name: str | None = None) -> dict[str, BaseTool]:
        """Lists all ADK tool instances.
        
        Args:
            app_name: Optional application name filter.
            
        Returns:
            Tool dictionary with global identifiers as keys (app_name:tool_id) 
            and ADK tool instances as values.
        """
        if app_name is None:
            # 返回所有工具
            result: dict[str, BaseTool] = {}
            for app_name, tools in self._app_index.items():
                for tool_id, tool in tools.items():
                    global_id = self.get_global_identifier(app_name, tool_id)
                    result[global_id] = tool
            return result
            
        # 根据应用名称过滤
        if app_name not in self._app_index:
            return {}
            
        result: dict[str, BaseTool] = {}
        for tool_id, tool in self._app_index[app_name].items():
            global_id = self.get_global_identifier(app_name, tool_id)
            result[global_id] = tool
                
        return result
        
    def get_global_identifier(self, app_name: str, tool_id: str) -> str:
        """Generates a globally unique identifier for a tool.
        
        Args:
            app_name: Application name.
            tool_id: Tool identifier.
            
        Returns:
            Globally unique identifier in the format "app_name:tool_id".
        """
        return f"{app_name}:{tool_id}"
    
    async def get_tool(self, app_name: str, tool_id: str) -> BaseTool | None:
        """根据app_name和tool_id获取ADK工具实例
        
        Args:
            app_name: 应用名称
            tool_id: 工具标识符
            
        Returns:
            ADK工具实例，如果不存在则返回None
        """
        if app_name in self._app_index and tool_id in self._app_index[app_name]:
            return self._app_index[app_name][tool_id]
        return None