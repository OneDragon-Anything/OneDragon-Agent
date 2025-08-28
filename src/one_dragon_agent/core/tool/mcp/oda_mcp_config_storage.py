from abc import ABC, abstractmethod

from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig


class BaseOdaMcpStorage(ABC):
    """Abstract base class for MCP configuration storage.
    
    This class defines the interface for storing and loading MCP configurations,
    supporting both in-memory and database storage modes.
    """
    
    @abstractmethod
    async def create_config(self, config: OdaMcpConfig) -> None:
        """Creates an MCP configuration.
        
        Args:
            config: MCP configuration object.
        """
    
    @abstractmethod
    async def get_config(self, mcp_id: str) -> OdaMcpConfig | None:
        """Gets an MCP configuration.
        
        Args:
            mcp_id: MCP identifier.
            
        Returns:
            MCP configuration object or None.
        """
    
    @abstractmethod
    async def update_config(self, config: OdaMcpConfig) -> None:
        """Updates an MCP configuration.
        
        Args:
            config: MCP configuration object.
        """
        
    @abstractmethod
    async def delete_config(self, mcp_id: str) -> None:
        """Deletes an MCP configuration.
        
        Args:
            mcp_id: MCP identifier.
        """
        
    @abstractmethod
    async def list_configs(self) -> list[OdaMcpConfig]:
        """Lists all configurations.
            
        Returns:
            List of all MCP configuration objects.
        """


class InMemoryOdaMcpStorage(BaseOdaMcpStorage):
    """In-memory storage service for MCP configurations.
    
    Used to store MCP configurations in memory for development and testing scenarios.
    """
    
    def __init__(self):
        """Initializes the in-memory storage."""
        self._configs: dict[str, OdaMcpConfig] = {}
        
    async def create_config(self, config: OdaMcpConfig) -> None:
        """Creates an MCP configuration in in-memory storage.
        
        Args:
            config: MCP configuration object.
        """
        key = config.get_global_id()
        self._configs[key] = config
    
    async def get_config(self, mcp_id: str) -> OdaMcpConfig | None:
        """Gets an MCP configuration from in-memory storage.
        
        Args:
            mcp_id: Global identifier in the format "app_name:mcp_id".
            
        Returns:
            MCP configuration object or None.
        """
        return self._configs.get(mcp_id)
    
    async def update_config(self, config: OdaMcpConfig) -> None:
        """Updates an MCP configuration in in-memory storage.
        
        Args:
            config: MCP configuration object.
        """
        key = config.get_global_id()
        self._configs[key] = config
            
    async def delete_config(self, mcp_id: str) -> None:
        """Deletes an MCP configuration from in-memory storage.
        
        Args:
            mcp_id: Global identifier in the format "app_name:mcp_id".
        """
        if mcp_id in self._configs:
            del self._configs[mcp_id]
            
    async def list_configs(self) -> list[OdaMcpConfig]:
        """Lists all configurations from in-memory storage.
            
        Returns:
            List of all MCP configuration objects.
        """
        return list(self._configs.values())