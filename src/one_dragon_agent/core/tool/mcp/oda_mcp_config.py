from typing import Any


class OdaMcpConfig:
    """MCP configuration template that defines standard configuration parameters for MCP tools,
    based on ADK's MCP Toolset parameters design.

    This class encapsulates all necessary parameters and configuration information for MCP tools,
    supporting different connection types and authentication mechanisms.
    """

    def __init__(
        self,
        # Basic fields
        app_name: str,
        mcp_id: str,
        name: str,
        description: str,
        
        # MCP connection configuration fields
        server_type: str,  # "sse" or "stdio" or "http"
        command: str | None = None,  # Used when server type is "stdio"
        args: list[str] | None = None,  # Used when server type is "stdio"
        url: str | None = None,  # Used when server type is "sse" or "http"
        env: dict[str, str] | None = None,  # Used when server type is "stdio"
        headers: dict[str, str] | None = None,  # Used when server type is "sse" or "http"
        tool_filter: list[str] | None = None,  # Optional tool filter list
        
        # MCP connection parameter fields
        timeout: int = 30,
        retry_count: int = 3,
    ):
        """Initializes an OdaMcpConfig instance.
        
        Args:
            app_name: Application name for tool isolation.
            mcp_id: Unique identifier for the MCP tool, must be unique within the app_name scope.
            name: Display name for the MCP tool.
            description: Description for the MCP tool.
            
            server_type: Server type, supports "sse", "stdio" or "http".
            command: Command to start the MCP server when server type is "stdio" (e.g., npx).
            args: Arguments list to start the MCP server when server type is "stdio" 
                (e.g., ["-y", "@modelcontextprotocol/server-filesystem"]).
            url: MCP server URL when server type is "sse" or "http" (e.g., http://localhost:8090/sse).
            env: Environment variables to start the MCP server when server type is "stdio" 
                (e.g., {"TARGET_FOLDER": "/path/to/folder"}).
            headers: HTTP headers when server type is "sse" or "http"
                (e.g., {"Authorization": "Bearer your-token"}).
            tool_filter: Optional tool filter list to specify only loading specific tools 
                (e.g., ['read_file', 'list_directory']).
            
            timeout: Connection timeout in seconds (e.g., 30).
            retry_count: Number of connection retries (e.g., 3).
            
        Raises:
            ValueError: If configuration parameters are invalid.
        """
        # Basic fields
        self.app_name = app_name
        self.mcp_id = mcp_id
        self.name = name
        self.description = description
        
        # MCP connection configuration fields
        self.server_type = server_type
        self.command = command
        self.args = args or []
        self.url = url
        self.env = env or {}
        self.headers = headers or {}
        self.tool_filter = tool_filter or []
        
        # MCP connection parameter fields
        self.timeout = timeout
        self.retry_count = retry_count
        
        # Validate configuration parameters
        self._validate_config()
        
    def _validate_config(self) -> None:
        """Validates MCP configuration parameters.
        
        Raises:
            ValueError: If configuration parameters are invalid.
        """
        if not self.app_name:
            raise ValueError("app_name cannot be empty")
            
        if not self.mcp_id:
            raise ValueError("mcp_id cannot be empty")
            
        if not self.name:
            raise ValueError("name cannot be empty")
            
        if not self.description:
            raise ValueError("description cannot be empty")
            
        if self.server_type not in ["sse", "stdio", "http"]:
            raise ValueError("server_type must be 'sse', 'stdio' or 'http'")
            
        if self.server_type in ["sse", "http"] and not self.url:
            raise ValueError("url cannot be empty when server_type is 'sse' or 'http'")
            
        if self.server_type == "stdio" and not self.command:
            raise ValueError("command cannot be empty when server_type is 'stdio'")
            
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than 0")
            
        if self.retry_count < 0:
            raise ValueError("retry_count cannot be less than 0")
            
    def to_dict(self) -> dict[str, Any]:
        """Converts the configuration to dictionary format for serialization.
        
        Returns:
            A dictionary containing all configuration information.
        """
        return {
            "app_name": self.app_name,
            "mcp_id": self.mcp_id,
            "name": self.name,
            "description": self.description,
            "server_type": self.server_type,
            "command": self.command,
            "args": self.args,
            "url": self.url,
            "env": self.env,
            "headers": self.headers,
            "tool_filter": self.tool_filter,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
        }
        
    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> 'OdaMcpConfig':
        """Creates an OdaMcpConfig instance from a dictionary.
        
        Args:
            config_dict: A dictionary containing configuration information.
            
        Returns:
            An OdaMcpConfig instance.
        """
        return cls(**config_dict)
        
    def get_global_id(self) -> str:
        """Generates a globally unique identifier.
        
        Returns:
            A globally unique identifier in the format "app_name:mcp_id".
        """
        return f"{self.app_name}:{self.mcp_id}"
        
    def __repr__(self) -> str:
        """Returns the string representation of the object.
        
        Returns:
            String representation of the object.
        """
        return f"OdaMcpConfig(app_name='{self.app_name}', mcp_id='{self.mcp_id}', name='{self.name}')"
        
    def __eq__(self, other) -> bool:
        """Compares two OdaMcpConfig instances for equality.
        
        Args:
            other: Another OdaMcpConfig instance.
            
        Returns:
            True if the two instances are equal, False otherwise.
        """
        if not isinstance(other, OdaMcpConfig):
            return False
            
        return self.to_dict() == other.to_dict()