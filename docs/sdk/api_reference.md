# API 参考

本章提供 OneDragon-Agent SDK 的详细 API 参考，包括核心类、方法和参数说明。

## OdaContext

`OdaContext` 是系统的全局资源管理器，采用单例模式，负责在应用启动时创建和管理所有 ADK 原生服务、管理器组件及共享资源。

### 构造函数

```python
class OdaContext:
    def __init__(self, config: OdaContextConfig):
        """初始化 OdaContext，创建所有 ADK 原生服务和管理器组件
        
        Args:
            config: 系统配置对象
        """
```

### 方法

#### start()

```python
async def start(self) -> None:
    """启动系统，初始化所有服务和管理器"""
```

#### stop()

```python
async def stop(self) -> None:
    """停止系统，释放所有资源"""
```

#### get_session_manager()

```python
def get_session_manager(self) -> OdaSessionManager:
    """获取会话管理器
    
    Returns:
        OdaSessionManager: 会话管理器实例
    """
```

#### get_agent_manager()

```python
def get_agent_manager(self) -> OdaAgentManager:
    """获取智能体管理器
    
    Returns:
        OdaAgentManager: 智能体管理器实例
    """
```

#### get_model_config_manager()

```python
def get_model_config_manager(self) -> OdaModelConfigManager:
    """获取模型配置管理器
    
    Returns:
        OdaModelConfigManager: 模型配置管理器实例
    """
```

#### get_agent_config_manager()

```python
def get_agent_config_manager(self) -> OdaAgentConfigManager:
    """获取智能体配置管理器
    
    Returns:
        OdaAgentConfigManager: 智能体配置管理器实例
    """
```

#### get_mcp_manager()

```python
def get_mcp_manager(self) -> OdaMcpManager:
    """获取 MCP 管理器
    
    Returns:
        OdaMcpManager: MCP 管理器实例
    """
```

#### get_tool_manager()

```python
def get_tool_manager(self) -> OdaToolManager:
    """获取工具管理器
    
    Returns:
        OdaToolManager: 工具管理器实例
    """
```

### 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig

# 创建配置
config = OdaContextConfig()

# 初始化 OdaContext
context = OdaContext(config)
await context.start()

# 获取各种管理器
session_manager = context.get_session_manager()
agent_manager = context.get_agent_manager()

# 使用完成后停止
await context.stop()
```

## OdaContextConfig

`OdaContextConfig` 是系统的配置类，定义了 OdaContext 初始化所需的各种配置参数。

### 构造函数

```python
class OdaContextConfig:
    def __init__(self):
        """初始化系统配置
        
        配置参数从环境变量中读取：
        - ODA_STORAGE: 持久化方式 (memory, mysql)
        - ODA_DEFAULT_LLM_BASE_URL: 默认的 LLM 服务地址
        - ODA_DEFAULT_LLM_API_KEY: 默认的 LLM 服务 API KEY
        - ODA_DEFAULT_LLM_MODEL: 默认的 LLM 服务模型
        """
```

### 属性

#### storage

```python
@property
def storage(self) -> str:
    """持久化方式
    
    Returns:
        str: 持久化方式，默认为 "memory"
    """
```

#### default_llm_base_url

```python
@property
def default_llm_base_url(self) -> Optional[str]:
    """默认的 LLM 服务地址
    
    Returns:
        Optional[str]: 默认的 LLM 服务地址，可能为 None
    """
```

#### default_llm_api_key

```python
@property
def default_llm_api_key(self) -> Optional[str]:
    """默认的 LLM 服务 API KEY
    
    Returns:
        Optional[str]: 默认的 LLM 服务 API KEY，可能为 None
    """
```

#### default_llm_model

```python
@property
def default_llm_model(self) -> Optional[str]:
    """默认的 LLM 服务模型
    
    Returns:
        Optional[str]: 默认的 LLM 服务模型，可能为 None
    """
```

## OdaSessionManager

`OdaSessionManager` 负责系统中所有会话实例的完整生命周期管理，为上层应用提供标准化的会话操作接口。

### 方法

#### create_session()

```python
async def create_session(self, app_name: str, user_id: str, session_id: str = None) -> OdaSession:
    """创建新的会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        session_id: 可选的会话标识（如果为 None 则自动生成）
        
    Returns:
        OdaSession: 创建的会话实例
        
    Raises:
        ValueError: 当参数无效时抛出异常
    """
```

#### get_session()

```python
async def get_session(self, app_name: str, user_id: str, session_id: str) -> Optional[OdaSession]:
    """获取指定的会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        session_id: 会话标识
        
    Returns:
        Optional[OdaSession]: 会话实例或 None（如果未找到）
    """
```

#### list_sessions()

```python
async def list_sessions(self, app_name: str, user_id: str) -> List[OdaSession]:
    """列出用户的所有会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        
    Returns:
        List[OdaSession]: 会话实例列表
    """
```

#### delete_session()

```python
async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
    """删除指定的会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        session_id: 会话标识
        
    Raises:
        ValueError: 当会话不存在时抛出异常
    """
```

#### cleanup_inactive_sessions()

```python
async def cleanup_inactive_sessions(self, timeout_seconds: int) -> None:
    """清理超时的会话实例
    
    Args:
        timeout_seconds: 会话超时时间（秒）
    """
```

#### set_concurrent_limit()

```python
async def set_concurrent_limit(self, max_concurrent_sessions: int) -> None:
    """设置并发会话数量限制
    
    Args:
        max_concurrent_sessions: 允许的最大并发会话数
    """
```

### 使用示例

```python
# 获取会话管理器
session_manager = context.get_session_manager()

# 创建会话
session = await session_manager.create_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)

# 获取会话
session = await session_manager.get_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)

# 列出会话
sessions = await session_manager.list_sessions(
    app_name="my_app",
    user_id="user_123"
)

# 删除会话
await session_manager.delete_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)
```

## OdaSession

`OdaSession` 代表一个独立的用户对话会话，是 ADK 原生组件的业务包装器。

### 构造函数

```python
class OdaSession:
    def __init__(self, app_name: str, user_id: str, session_id: str, agent_manager: OdaAgentManager):
        """初始化 OdaSession，传入会话标识和智能体管理器
        
        Args:
            app_name: 应用名称
            user_id: 用户标识
            session_id: 会话标识
            agent_manager: 智能体管理器实例
        """
```

### 方法

#### process_message()

```python
async def process_message(self, message: str, agent_name: str = None) -> str:
    """处理用户消息，返回最终响应
    
    Args:
        message: 用户输入的消息
        agent_name: 指定的智能体名称，如果为 None 则使用默认智能体
        
    Returns:
        str: 智能体的最终响应结果
        
    Raises:
        AgentNotFoundError: 当智能体不存在时抛出异常
        Exception: 其他处理错误
    """
```

#### cleanup()

```python
async def cleanup(self) -> None:
    """清理会话资源"""
```

#### get_session_info()

```python
def get_session_info(self) -> dict:
    """获取会话信息
    
    Returns:
        dict: 会话信息字典
    """
```

#### is_active()

```python
def is_active(self) -> bool:
    """检查会话是否活跃
    
    Returns:
        bool: 会话是否活跃
    """
```

### 属性

#### app_name

```python
@property
def app_name(self) -> str:
    """应用名称
    
    Returns:
        str: 应用名称
    """
```

#### user_id

```python
@property
def user_id(self) -> str:
    """用户标识
    
    Returns:
        str: 用户标识
    """
```

#### session_id

```python
@property
def session_id(self) -> str:
    """会话标识
    
    Returns:
        str: 会话标识
    """
```

### 使用示例

```python
# 处理消息
response = await session.process_message(
    message="你好，请介绍一下自己",
    agent_name="default"
)

print(f"响应: {response}")

# 不指定智能体，使用默认智能体
response = await session.process_message(
    message="今天天气怎么样？"
)

print(f"响应: {response}")

# 获取会话信息
info = session.get_session_info()
print(f"会话信息: {info}")

# 检查会话状态
if session.is_active():
    print("会话处于活跃状态")
else:
    print("会话已关闭")

# 清理会话资源
await session.cleanup()
```

## OdaAgentManager

`OdaAgentManager` 负责系统中所有智能体实例的完整生命周期管理，为上层应用提供标准化的智能体操作接口。

### 方法

#### create_agent()

```python
async def create_agent(self, agent_name: str, app_name: str, user_id: str, session_id: str) -> OdaAgent:
    """创建智能体实例
    
    Args:
        agent_name: 智能体名称
        app_name: 应用名称
        user_id: 用户标识
        session_id: 会话标识
        
    Returns:
        OdaAgent: 创建的智能体实例
        
    Raises:
        ValueError: 当配置无效或智能体不存在时抛出异常
    """
```

### 使用示例

```python
# 获取智能体管理器
agent_manager = context.get_agent_manager()

# 创建智能体
agent = await agent_manager.create_agent(
    agent_name="weather_agent",
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)
```

## OdaAgent

`OdaAgent` 是 OneDragon 自定义的智能体封装类，持有 ADK 原生 `Runner` 实例，为 `OdaSession` 提供简化的业务接口。

### 构造函数

```python
class OdaAgent:
    def __init__(self, runner: Runner, app_name: str, user_id: str, session_id: str, max_retries: int = 3):
        """初始化 OdaAgent，传入 Runner 实例和会话标识
        
        Args:
            runner: ADK Runner 实例
            app_name: 应用名称
            user_id: 用户标识
            session_id: 会话标识
            max_retries: 最大重试次数，默认为 3 次
        """
```

### 方法

#### run_async()

```python
async def run_async(self, new_message: str):
    """异步执行智能体，返回 Event 流生成器，内部实现错误重试机制
    
    内部实现错误重试机制：
    - 首次执行时使用原始用户消息，确保消息只提交一次到会话历史
    - 检测到执行异常时，按递增间隔自动重试（1s, 2s, 4s, 8s...）
    - 重试时不重复用户消息，从当前会话状态恢复
    - 产生符合 ADK 原生标准的事件通知重试状态
    - 达到最大重试次数后产生最终错误事件
    
    Args:
        new_message: 用户消息内容（字符串格式）
        
    Returns:
        AsyncGenerator: Event 流生成器
    """
```

#### run()

```python
def run(self, new_message: str):
    """同步执行智能体，返回 Event 流生成器，内部实现错误重试机制
    
    内部实现与 run_async 相同的错误重试机制
    
    Args:
        new_message: 用户消息内容（字符串格式）
        
    Returns:
        Generator: Event 流生成器
    """
```

#### get_agent_info()

```python
def get_agent_info(self) -> dict:
    """获取智能体信息
    
    Returns:
        dict: 智能体信息
    """
```

#### is_ready()

```python
def is_ready(self) -> bool:
    """检查智能体是否就绪
    
    Returns:
        bool: 智能体是否就绪
    """
```

#### cleanup()

```python
async def cleanup(self) -> None:
    """清理智能体资源"""
```

### 使用示例

```python
# 异步执行智能体
async for event in agent.run_async("你好，请介绍一下自己"):
    print(f"事件: {event}")

# 同步执行智能体
for event in agent.run("你好，请介绍一下自己"):
    print(f"事件: {event}")

# 获取智能体信息
info = agent.get_agent_info()
print(f"智能体信息: {info}")

# 检查智能体状态
if agent.is_ready():
    print("智能体已就绪")
else:
    print("智能体未就绪")

# 清理智能体资源
await agent.cleanup()
```

## OdaModelConfigManager

`OdaModelConfigManager` 负责大模型配置的创建、存储、检索和管理。

### 方法

#### create_config()

```python
async def create_config(self, config: OdaModelConfig) -> None:
    """创建大模型配置
    
    创建持久化的大模型配置，配置将被存储到底层服务中。
    默认配置不允许通过此方法创建，因为它基于环境变量自动生成。
    
    Args:
        config: 要创建的配置对象
        
    Raises:
        ValueError: 当尝试创建默认配置时抛出异常
    """
```

#### get_config()

```python
async def get_config(self, model_id: str) -> Optional[OdaModelConfig]:
    """获取大模型配置
    
    支持获取持久化配置和默认配置。当请求默认配置 ID 时，
    返回内存中的默认配置实例（不进行持久化查询）。
    
    Args:
        model_id: 大模型唯一标识符，支持特殊默认配置 ID "__default_llm_config"
        
    Returns:
        Optional[OdaModelConfig]: 配置对象，如果不存在则返回 None
        
    Note:
        默认配置 ID "__default_llm_config" 为保留 ID，用于标识基于环境变量的默认配置
    """
```

#### get_default_config()

```python
def get_default_config(self) -> Optional[OdaModelConfig]:
    """获取默认大模型配置
    
    直接返回初始化时缓存的默认配置实例，不涉及持久化操作。
    默认配置在管理器初始化时从注入的 OdaContextConfig 中一次性读取，
    该配置由 OdaContext 统一从环境变量 ODA_DEFAULT_LLM_BASE_URL、
    ODA_DEFAULT_LLM_API_KEY、ODA_DEFAULT_LLM_MODEL 中读取并验证，
    使用固定的特殊 ID "__default_llm_config"。
    
    Returns:
        Optional[OdaModelConfig]: 默认配置对象，如果 OdaContextConfig 中未设置默认配置则返回 None
        
    Note:
        该方法直接返回缓存实例，性能高效，适合频繁调用获取默认配置
    """
```

#### update_config()

```python
async def update_config(self, config: OdaModelConfig) -> None:
    """更新大模型配置
    
    更新持久化的大模型配置。默认配置不允许通过此方法更新，
    因为默认配置基于 OdaContextConfig，需要通过修改环境变量并重启系统来更新。
    
    Args:
        config: 要更新的配置对象
        
    Raises:
        ValueError: 当尝试更新默认配置时抛出异常
    """
```

#### delete_config()

```python
async def delete_config(self, model_id: str) -> None:
    """删除大模型配置
    
    删除持久化的大模型配置。默认配置不允许删除，
    因为它是基于 OdaContextConfig 的系统级配置。
    
    Args:
        model_id: 要删除的大模型唯一标识符
        
    Raises:
        ValueError: 当尝试删除默认配置时抛出异常
    """
```

#### list_configs()

```python
async def list_configs(self) -> List[OdaModelConfig]:
    """获取所有大模型配置
    
    返回系统中所有可用的大模型配置，包括：
    - 持久化配置：通过 create_config 创建的自定义配置
    - 内置默认配置：基于 OdaContextConfig 生成的默认配置
    
    Returns:
        List[OdaModelConfig]: 包含所有配置对象的列表，默认配置总是出现在列表末尾
        
    Note:
        该方法提供完整的配置视图，便于上层应用了解所有可用的模型配置
    """
```

#### validate_model_config()

```python
async def validate_model_config(self, app_name: str, model_config: str) -> bool:
    """验证模型配置是否有效
    
    Args:
        app_name: 应用名称
        model_config: 模型配置 ID
        
    Returns:
        bool: 如果模型配置有效返回 True，否则返回 False
    """
```

### 使用示例

```python
# 获取模型配置管理器
model_config_manager = context.get_model_config_manager()

# 创建模型配置
model_config = OdaModelConfig(
    app_name="my_app",
    model_id="gemini-config",
    base_url="https://api.example.com",
    api_key="your-api-key",
    model="gemini-2.0-flash"
)
await model_config_manager.create_config(model_config)

# 获取模型配置
config = await model_config_manager.get_config("gemini-config")
if config:
    print(f"模型配置: {config}")

# 获取默认模型配置
default_config = model_config_manager.get_default_config()
if default_config:
    print(f"默认模型配置: {default_config}")

# 列出所有模型配置
configs = await model_config_manager.list_configs()
print(f"共有 {len(configs)} 个模型配置")

# 验证模型配置
is_valid = await model_config_manager.validate_model_config(
    app_name="my_app",
    model_config="gemini-config"
)
print(f"模型配置有效: {is_valid}")
```

## OdaAgentConfigManager

`OdaAgentConfigManager` 负责智能体配置的创建、存储、检索和管理。

### 方法

#### create_config()

```python
async def create_config(self, config: OdaAgentConfig) -> None:
    """创建智能体配置
    
    创建持久化的智能体配置，配置将被存储到底层服务中。
    在创建之前会验证所有引用的模型和 MCP 配置是否有效。
    
    Args:
        config: 要创建的配置对象
        
    Raises:
        ValueError: 当配置无效或引用了不存在的配置时抛出异常
    """
```

#### get_config()

```python
async def get_config(self, agent_name: str) -> Optional[OdaAgentConfig]:
    """获取智能体配置
    
    Args:
        agent_name: 智能体名称，唯一标识符
        
    Returns:
        Optional[OdaAgentConfig]: 配置对象，如果不存在则返回 None
    """
```

#### update_config()

```python
async def update_config(self, config: OdaAgentConfig) -> None:
    """更新智能体配置
    
    更新持久化的智能体配置。在更新之前会验证所有引用的模型和 MCP 配置是否有效。
    
    Args:
        config: 要更新的配置对象
        
    Raises:
        ValueError: 当配置无效或引用了不存在的配置时抛出异常
    """
```

#### delete_config()

```python
async def delete_config(self, agent_name: str) -> None:
    """删除智能体配置
    
    Args:
        agent_name: 要删除的智能体名称
    """
```

#### list_configs()

```python
async def list_configs(self) -> List[OdaAgentConfig]:
    """获取所有智能体配置
    
    Returns:
        List[OdaAgentConfig]: 所有配置对象的列表
    """
```

#### validate_model_config()

```python
async def validate_model_config(self, app_name: str, model_config: str) -> bool:
    """验证模型配置是否有效
    
    Args:
        app_name: 应用名称
        model_config: 模型配置 ID
        
    Returns:
        bool: 如果模型配置有效返回 True，否则返回 False
    """
```

#### validate_mcp_config()

```python
async def validate_mcp_config(self, app_name: str, mcp_list: List[str]) -> bool:
    """验证 MCP 配置是否有效
    
    Args:
        app_name: 应用名称
        mcp_list: MCP 配置 ID 列表
        
    Returns:
        bool: 如果所有 MCP 配置都有效返回 True，否则返回 False
    """
```

#### is_built_in_config()

```python
def is_built_in_config(self, agent_name: str) -> bool:
    """检查是否为内置配置
    
    Args:
        agent_name: 智能体名称
        
    Returns:
        bool: 如果为内置配置返回 True，否则返回 False
    """
```

### 使用示例

```python
# 获取智能体配置管理器
agent_config_manager = context.get_agent_config_manager()

# 创建智能体配置
agent_config = OdaAgentConfig(
    app_name="my_app",
    agent_name="weather_agent",
    agent_type="llm_agent",
    description="天气查询智能体",
    instruction="你是一个天气查询助手，帮助用户获取天气信息",
    model_config="gemini-config",
    tool_list=["get_weather", "get_temperature"]
)
await agent_config_manager.create_config(agent_config)

# 获取智能体配置
config = await agent_config_manager.get_config("weather_agent")
if config:
    print(f"智能体配置: {config}")

# 列出所有智能体配置
configs = await agent_config_manager.list_configs()
print(f"共有 {len(configs)} 个智能体配置")

# 验证模型配置
is_valid = await agent_config_manager.validate_model_config(
    app_name="my_app",
    model_config="gemini-config"
)
print(f"模型配置有效: {is_valid}")

# 验证 MCP 配置
is_valid = await agent_config_manager.validate_mcp_config(
    app_name="my_app",
    mcp_list=["filesystem_mcp"]
)
print(f"MCP 配置有效: {is_valid}")

# 检查是否为内置配置
is_builtin = agent_config_manager.is_built_in_config("default")
print(f"是否为内置配置: {is_builtin}")
```

## OdaMcpManager

`OdaMcpManager` 负责 MCP 配置的创建、存储、检索和管理。

### 方法

#### register_build_in_config()

```python
async def register_build_in_config(self, config: OdaMcpConfig) -> None:
    """注册内置 MCP 配置（存储在独立内存中，无需持久化）
    
    Args:
        config: MCP 配置对象
        
    Raises:
        ValueError: 如果配置参数无效或冲突
    """
```

#### register_custom_config()

```python
async def register_custom_config(self, config: OdaMcpConfig) -> None:
    """注册自定义 MCP 配置（需要持久化）
    
    Args:
        config: MCP 配置对象
        
    Raises:
        ValueError: 如果配置参数无效或冲突
    """
```

#### unregister_build_in_config()

```python
async def unregister_build_in_config(self, app_name: str, tool_id: str) -> None:
    """注销内置 MCP 配置
    
    Args:
        app_name: 应用名称
        tool_id: 工具标识符
        
    Raises:
        PermissionError: 内置配置通常不允许删除
    """
```

#### unregister_custom_config()

```python
async def unregister_custom_config(self, app_name: str, tool_id: str) -> None:
    """注销自定义 MCP 配置
    
    Args:
        app_name: 应用名称
        tool_id: 工具标识符
    """
```

#### get_mcp_config()

```python
async def get_mcp_config(self, app_name: str, tool_id: str) -> Optional[OdaMcpConfig]:
    """获取 MCP 配置（支持查询内置和自定义配置）
    
    Args:
        app_name: 应用名称
        tool_id: 工具标识符
        
    Returns:
        Optional[OdaMcpConfig]: MCP 配置对象或 None
    """
```

#### list_mcp_configs()

```python
async def list_mcp_configs(self, app_name: str) -> Dict[str, OdaMcpConfig]:
    """列出所有 MCP 配置（包括内置和自定义配置）
    
    Args:
        app_name: 应用名称过滤器
        
    Returns:
        Dict[str, OdaMcpConfig]: 配置字典，以全局标识符为键 (app_name:tool_id)
    """
```

#### update_custom_config()

```python
async def update_custom_config(self, app_name: str, tool_id: str, config: OdaMcpConfig) -> None:
    """更新自定义 MCP 配置（内置配置无法更新）
    
    Args:
        app_name: 应用名称
        tool_id: 工具标识符
        config: 新的 MCP 配置对象
        
    Raises:
        ValueError: 如果配置参数无效或 MCP 配置不存在
        PermissionError: 如果尝试更新内置配置
    """
```

### 使用示例

```python
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
config = await mcp_manager.get_mcp_config(
    app_name="my_app",
    tool_id="filesystem_stdio"
)
if config:
    print(f"MCP 配置: {config}")

# 列出所有 MCP 配置
configs = await mcp_manager.list_mcp_configs(app_name="my_app")
print(f"应用 my_app 有 {len(configs)} 个 MCP 配置")

# 更新 MCP 配置
mcp_config.tool_filter.append("write_file")
await mcp_manager.update_custom_config(
    app_name="my_app",
    tool_id="filesystem_stdio",
    config=mcp_config
)

# 删除 MCP 配置
await mcp_manager.unregister_custom_config(
    app_name="my_app",
    tool_id="filesystem_stdio"
)
```

## 异常类

OneDragon-Agent SDK 定义了以下异常类：

### SessionNotFoundError

```python
class SessionNotFoundError(Exception):
    """会话不存在异常"""
    pass
```

### AgentNotFoundError

```python
class AgentNotFoundError(Exception):
    """智能体不存在异常"""
    pass
```

### ConfigurationError

```python
class ConfigurationError(Exception):
    """配置错误异常"""
    pass
```

### McpConfigurationError

```python
class McpConfigurationError(Exception):
    """MCP 配置错误异常"""
    pass
```

---

*通过本 API 参考，您可以详细了解 OneDragon-Agent SDK 的所有接口和用法。*