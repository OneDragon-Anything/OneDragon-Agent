# OdaMcpManager

`OdaMcpManager` 负责 MCP 配置的创建、存储、检索和管理。

## 构造函数

```python
class OdaMcpManager:
    def __init__(self, custom_config_storage: BaseOdaMcpStorage):
        """初始化 OdaMcpManager
        
        创建内置配置的单独存储和自定义配置存储服务。
        
        Args:
            custom_config_storage: 自定义配置存储服务实例
        """
```

## 方法

### register_build_in_config()

```python
async def register_build_in_config(self, config: OdaMcpConfig) -> None:
    """注册内置 MCP 配置（存储在独立内存中，无需持久化）
    
    Args:
        config: MCP 配置对象
        
    Raises:
        ValueError: 如果配置参数无效或冲突
    """
```

### register_custom_config()

```python
async def register_custom_config(self, config: OdaMcpConfig) -> None:
    """注册自定义 MCP 配置（需要持久化）
    
    Args:
        config: MCP 配置对象
        
    Raises:
        ValueError: 如果配置参数无效或冲突
    """
```

### unregister_build_in_config()

```python
async def unregister_build_in_config(self, app_name: str, mcp_id: str) -> None:
    """注销内置 MCP 配置
    
    Args:
        app_name: 应用名称
        mcp_id: MCP 标识符
        
    Raises:
        PermissionError: 内置配置通常不允许删除
    """
```

### unregister_custom_config()

```python
async def unregister_custom_config(self, app_name: str, mcp_id: str) -> None:
    """注销自定义 MCP 配置
    
    Args:
        app_name: 应用名称
        mcp_id: MCP 标识符
    """
```

### get_mcp_config()

```python
async def get_mcp_config(self, app_name: str, mcp_id: str) -> OdaMcpConfig | None:
    """获取 MCP 配置（支持查询内置和自定义配置）
    
    Args:
        app_name: 应用名称
        mcp_id: MCP 标识符
        
    Returns:
        OdaMcpConfig | None: MCP 配置对象或 None
    """
```

### list_mcp_configs()

```python
async def list_mcp_configs(self, app_name: str) -> dict[str, OdaMcpConfig]:
    """列出所有 MCP 配置（包括内置和自定义配置）
    
    Args:
        app_name: 应用名称过滤器
        
    Returns:
        dict[str, OdaMcpConfig]: 配置字典，以全局标识符为键 (app_name:mcp_id)
    """
```

### update_custom_config()

```python
async def update_custom_config(self, app_name: str, mcp_id: str, config: OdaMcpConfig) -> None:
    """更新自定义 MCP 配置（内置配置无法更新）
    
    Args:
        app_name: 应用名称
        mcp_id: MCP 标识符
        config: 新的 MCP 配置对象
        
    Raises:
        ValueError: 如果配置参数无效或 MCP 配置不存在
        PermissionError: 如果尝试更新内置配置
    """
```

### create_mcp_toolset()

```python
async def create_mcp_toolset(self, app_name: str, mcp_id: str) -> MCPToolset:
    """创建可直接用作工具集的 MCPToolset 实例
    
    Args:
        app_name: 应用名称
        mcp_id: MCP 标识符
        
    Returns:
        MCPToolset: 可直接在 LlmAgent 中使用的 MCPToolset 实例
        
    Raises:
        ValueError: 如果 MCP 配置未找到或无效
        RuntimeError: 如果 MCPToolset 创建失败
    """
```

## 属性

### _build_in_configs

```python
_build_in_configs: dict[str, OdaMcpConfig]
```
内置配置内存存储

### _custom_config_storage

```python
_custom_config_storage: BaseOdaMcpStorage
```
自定义配置存储服务

## 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取 MCP 管理器
    mcp_manager = context.mcp_manager
    
    # 创建 MCP 配置
    mcp_config = OdaMcpConfig(
        app_name="my_app",
        mcp_id="filesystem_stdio",
        name="文件系统 MCP",
        description="提供文件系统操作能力",
        server_type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"],
        tool_filter=["read_file", "list_directory"]
    )
    
    # 注册自定义 MCP 配置
    await mcp_manager.register_custom_config(mcp_config)
    
    # 获取 MCP 配置
    config = await mcp_manager.get_mcp_config(
        app_name="my_app",
        mcp_id="filesystem_stdio"
    )
    if config:
        print(f"MCP 配置: {config}")
    
    # 列出所有 MCP 配置
    configs = await mcp_manager.list_mcp_configs(app_name="my_app")
    print(f"应用 my_app 有 {len(configs)} 个 MCP 配置")
    
    # 创建 MCP 工具集
    toolset = await mcp_manager.create_mcp_toolset(
        app_name="my_app",
        mcp_id="filesystem_stdio"
    )
    print(f"创建的 MCP 工具集: {toolset}")
    
    # 更新 MCP 配置
    mcp_config.tool_filter.append("write_file")
    await mcp_manager.update_custom_config(
        app_name="my_app",
        mcp_id="filesystem_stdio",
        config=mcp_config
    )
    
    # 删除 MCP 配置
    await mcp_manager.unregister_custom_config(
        app_name="my_app",
        mcp_id="filesystem_stdio"
    )
    
finally:
    await context.stop()
```

## MCP 服务器类型支持

### Stdio 服务器

适用于本地进程通信，通过标准输入输出与 MCP 服务器交互：

```python
# stdio 类型的 MCP 配置示例
stdio_config = OdaMcpConfig(
    app_name="file_app",
    mcp_id="filesystem_stdio",
    name="文件系统 MCP (Stdio)",
    description="通过 stdio 连接的文件系统 MCP 服务器",
    server_type="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"],
    tool_filter=["read_file", "list_directory"]
)
```

### SSE 服务器

适用于 HTTP 服务器通信，通过 Server-Sent Events 与 MCP 服务器交互：

```python
# sse 类型的 MCP 配置示例
sse_config = OdaMcpConfig(
    app_name="web_app",
    mcp_id="web_api_sse",
    name="Web API MCP (SSE)",
    description="通过 SSE 连接的 Web API MCP 服务器",
    server_type="sse",
    url="http://localhost:8090/sse",
    headers={"Authorization": "Bearer your-token"},
    tool_filter=["fetch_data", "submit_form"]
)
```

### HTTP 服务器

适用于标准 HTTP 服务器通信，通过 REST API 与 MCP 服务器交互：

```python
# http 类型的 MCP 配置示例
http_config = OdaMcpConfig(
    app_name="web_app",
    mcp_id="web_api_http",
    name="Web API MCP (HTTP)",
    description="通过 HTTP 连接的 Web API MCP 服务器",
    server_type="http",
    url="http://localhost:8080/mcp",
    headers={"Authorization": "Bearer your-token", "Content-Type": "application/json"},
    tool_filter=["get_data", "post_data", "delete_resource"]
)
```

## 注意事项

- 内置配置和自定义配置存储在不同的位置，内置配置存储在内存中，自定义配置需要持久化
- 内置配置通常不允许删除，尝试删除会抛出 `PermissionError`
- 自定义配置可以创建、更新和删除
- 更新配置时会验证配置参数的有效性
- `list_mcp_configs()` 返回的配置字典以全局标识符为键，格式为 `app_name:mcp_id`
- OdaMcpManager 由 OdaToolManager 持有，不应直接实例化
- 所有方法都是异步的，需要使用 await 调用
- `create_mcp_toolset()` 方法可以创建可直接在 LlmAgent 中使用的 MCPToolset 实例