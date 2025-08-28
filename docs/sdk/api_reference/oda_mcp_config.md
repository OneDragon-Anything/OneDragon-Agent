# OdaMcpConfig

`OdaMcpConfig` 是 MCP 配置的数据类，包含 MCP 服务器的所有配置信息。

## 构造函数

```python
class OdaMcpConfig:
    def __init__(
        self,
        mcp_id: str,
        app_name: str,
        name: str,
        description: str,
        server_type: str,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
        tool_filter: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        retry_count: Optional[int] = None
    ):
        """初始化 MCP 配置
        
        Args:
            mcp_id: MCP 配置的唯一标识符
            app_name: 应用名称，用于隔离不同应用的 MCP 配置
            name: MCP 配置的显示名称
            description: MCP 配置的描述信息
            server_type: 服务器类型：`'stdio'`、`'sse'` 或 `'http'`
            command: 启动 MCP 服务器的命令（stdio 类型），可选
            args: 启动 MCP 服务器的参数（stdio 类型），可选
            url: MCP 服务器的 URL（sse 或 http 类型），可选
            headers: HTTP 请求头（sse 或 http 类型），可选
            env: 环境变量，可选
            tool_filter: 工具过滤器，只加载指定的工具，可选
            timeout: 连接超时时间（秒），可选
            retry_count: 重试次数，可选
        """
```

## 属性

### mcp_id

```python
@property
def mcp_id(self) -> str:
    """MCP 配置的唯一标识符
    
    Returns:
        str: MCP ID
    """
```

### app_name

```python
@property
def app_name(self) -> str:
    """应用名称，用于隔离不同应用的 MCP 配置
    
    Returns:
        str: 应用名称
    """
```

### name

```python
@property
def name(self) -> str:
    """MCP 配置的显示名称
    
    Returns:
        str: 显示名称
    """
```

### description

```python
@property
def description(self) -> str:
    """MCP 配置的描述信息
    
    Returns:
        str: 描述信息
    """
```

### server_type

```python
@property
def server_type(self) -> str:
    """服务器类型：`'stdio'`、`'sse'` 或 `'http'`
    
    Returns:
        str: 服务器类型
    """
```

### command

```python
@property
def command(self) -> Optional[str]:
    """启动 MCP 服务器的命令（stdio 类型）
    
    Returns:
        Optional[str]: 命令或 None
    """
```

### args

```python
@property
def args(self) -> Optional[List[str]]:
    """启动 MCP 服务器的参数（stdio 类型）
    
    Returns:
        Optional[List[str]]: 参数列表或 None
    """
```

### url

```python
@property
def url(self) -> Optional[str]:
    """MCP 服务器的 URL（sse 或 http 类型）
    
    Returns:
        Optional[str]: URL 或 None
    """
```

### headers

```python
@property
def headers(self) -> Optional[Dict[str, str]]:
    """HTTP 请求头（sse 或 http 类型）
    
    Returns:
        Optional[Dict[str, str]]: 请求头字典或 None
    """
```

### env

```python
@property
def env(self) -> Optional[Dict[str, str]]:
    """环境变量
    
    Returns:
        Optional[Dict[str, str]]: 环境变量字典或 None
    """
```

### tool_filter

```python
@property
def tool_filter(self) -> Optional[List[str]]:
    """工具过滤器，只加载指定的工具
    
    Returns:
        Optional[List[str]]: 工具名称列表或 None
    """
```

### timeout

```python
@property
def timeout(self) -> Optional[int]:
    """连接超时时间（秒）
    
    Returns:
        Optional[int]: 超时时间或 None
    """
```

### retry_count

```python
@property
def retry_count(self) -> Optional[int]:
    """重试次数
    
    Returns:
        Optional[int]: 重试次数或 None
    """
```

## 使用示例

### Stdio 服务器配置

```python
from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig

# stdio 类型的 MCP 配置示例
stdio_config = OdaMcpConfig(
    mcp_id="filesystem_stdio",
    app_name="file_app",
    name="文件系统 MCP (Stdio)",
    description="通过 stdio 连接的文件系统 MCP 服务器",
    server_type="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"],
    tool_filter=["read_file", "list_directory"]
)

# 访问配置属性
print(f"MCP ID: {stdio_config.mcp_id}")
print(f"应用名称: {stdio_config.app_name}")
print(f"服务器类型: {stdio_config.server_type}")
print(f"启动命令: {stdio_config.command}")
print(f"启动参数: {stdio_config.args}")
print(f"工具过滤器: {stdio_config.tool_filter}")
```

### SSE 服务器配置

```python
# sse 类型的 MCP 配置示例
sse_config = OdaMcpConfig(
    mcp_id="web_api_sse",
    app_name="web_app",
    name="Web API MCP (SSE)",
    description="通过 SSE 连接的 Web API MCP 服务器",
    server_type="sse",
    url="http://localhost:8090/sse",
    headers={"Authorization": "Bearer your-token"},
    tool_filter=["fetch_data", "submit_form"]
)

# 访问配置属性
print(f"MCP ID: {sse_config.mcp_id}")
print(f"应用名称: {sse_config.app_name}")
print(f"服务器类型: {sse_config.server_type}")
print(f"服务器 URL: {sse_config.url}")
print(f"请求头: {sse_config.headers}")
print(f"工具过滤器: {sse_config.tool_filter}")
```

### HTTP 服务器配置

```python
# http 类型的 MCP 配置示例
http_config = OdaMcpConfig(
    mcp_id="web_api_http",
    app_name="web_app",
    name="Web API MCP (HTTP)",
    description="通过 HTTP 连接的 Web API MCP 服务器",
    server_type="http",
    url="http://localhost:8080/mcp",
    headers={"Authorization": "Bearer your-token", "Content-Type": "application/json"},
    tool_filter=["get_data", "post_data", "delete_resource"]
)

# 访问配置属性
print(f"MCP ID: {http_config.mcp_id}")
print(f"应用名称: {http_config.app_name}")
print(f"服务器类型: {http_config.server_type}")
print(f"服务器 URL: {http_config.url}")
print(f"请求头: {http_config.headers}")
print(f"工具过滤器: {http_config.tool_filter}")
```

## 配置约束

- **唯一性约束**: `mcp_id` 在同一 `app_name` 下必须唯一
- **服务器类型约束**: `server_type` 必须是 `'stdio'`、`'sse'` 或 `'http'`
- **参数完整性**: stdio 类型必须提供 `command`，sse 和 http 类型必须提供 `url`
- **应用隔离**: 不同 `app_name` 下的配置相互独立，可以存在相同的 `mcp_id`
- **配置验证**: 所有配置都必须通过有效性验证，确保连接参数正确

## 与 OdaMcpManager 的配合使用

```python
from one_dragon_agent import OdaContext, OdaContextConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取 MCP 管理器
    mcp_manager = context.get_mcp_manager()
    
    # 创建 MCP 配置
    mcp_config = OdaMcpConfig(
        mcp_id="filesystem_stdio",
        app_name="my_app",
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
    retrieved_config = await mcp_manager.get_mcp_config(
        app_name="my_app",
        tool_id="filesystem_stdio"
    )
    if retrieved_config:
        print(f"获取的配置: {retrieved_config}")
    
    # 列出所有 MCP 配置
    configs = await mcp_manager.list_mcp_configs(app_name="my_app")
    print(f"应用 my_app 有 {len(configs)} 个 MCP 配置")
    
finally:
    await context.stop()
```

## 注意事项

- 内置配置和自定义配置存储在不同的位置，内置配置存储在内存中，自定义配置需要持久化
- 内置配置通常不允许删除，尝试删除会抛出 `PermissionError`
- 自定义配置可以创建、更新和删除
- 更新配置时会验证配置参数的有效性
- `list_mcp_configs()` 返回的配置字典以全局标识符为键，格式为 `app_name:tool_id`
- 不同服务器类型需要提供不同的必需参数，请确保根据服务器类型提供正确的参数