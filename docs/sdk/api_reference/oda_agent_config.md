# OdaAgentConfig

`OdaAgentConfig` 是智能体配置的数据类，包含智能体的所有配置信息。

## 构造函数

```python
class OdaAgentConfig:
    def __init__(
        self,
        app_name: str,
        agent_name: str,
        agent_type: str,
        description: str,
        instruction: str,
        model_config: str,
        tool_list: Optional[List[str]] = None,
        mcp_list: Optional[List[str]] = None,
        sub_agent_list: Optional[List[str]] = None
    ):
        """初始化智能体配置
        
        Args:
            app_name: 用于标识所属的应用程序
            agent_name: 智能体名称，同时作为唯一标识
            agent_type: ADK 中的智能体类型
            description: 智能体功能描述
            instruction: 智能体的系统提示词
            model_config: 使用的大模型 ID
            tool_list: 可使用工具的 ID 列表，可选
            mcp_list: 可使用 MCP 的 ID 列表，可选
            sub_agent_list: 可使用子智能体的名称/ID 列表，可选
        """
```

## 属性

### app_name

```python
@property
def app_name(self) -> str:
    """用于标识所属的应用程序
    
    Returns:
        str: 应用名称
    """
```

### agent_name

```python
@property
def agent_name(self) -> str:
    """智能体名称，同时作为唯一标识
    
    Returns:
        str: 智能体名称
    """
```

### agent_type

```python
@property
def agent_type(self) -> str:
    """ADK 中的智能体类型
    
    Returns:
        str: 智能体类型
    """
```

### description

```python
@property
def description(self) -> str:
    """智能体功能描述
    
    Returns:
        str: 功能描述
    """
```

### instruction

```python
@property
def instruction(self) -> str:
    """智能体的系统提示词
    
    Returns:
        str: 系统提示词
    """
```

### model_config

```python
@property
def model_config(self) -> str:
    """使用的大模型 ID
    
    Returns:
        str: 模型配置 ID
    """
```

### tool_list

```python
@property
def tool_list(self) -> List[str]:
    """可使用工具的 ID 列表
    
    Returns:
        List[str]: 工具 ID 列表
    """
```

### mcp_list

```python
@property
def mcp_list(self) -> List[str]:
    """可使用 MCP 的 ID 列表
    
    Returns:
        List[str]: MCP ID 列表
    """
```

### sub_agent_list

```python
@property
def sub_agent_list(self) -> List[str]:
    """可使用子智能体的名称/ID 列表
    
    Returns:
        List[str]: 子智能体名称/ID 列表
    """
```

## 使用示例

```python
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig

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

# 访问配置属性
print(f"应用名称: {agent_config.app_name}")
print(f"智能体名称: {agent_config.agent_name}")
print(f"智能体类型: {agent_config.agent_type}")
print(f"功能描述: {agent_config.description}")
print(f"系统提示词: {agent_config.instruction}")
print(f"模型配置: {agent_config.model_config}")
print(f"工具列表: {agent_config.tool_list}")
```

## 配置约束

- **唯一性约束**: `agent_name` 在同一 `app_name` 下必须唯一
- **引用完整性**: `tool_list`、`mcp_list` 和 `sub_agent_list` 中引用的工具、MCP 配置和子智能体必须存在
- **模型兼容性**: `model_config` 必须是系统中可用的模型 ID，通过 `OdaModelConfigManager` 验证
- **MCP 配置有效性**: `mcp_list` 中引用的 MCP 配置必须存在且启用，通过 `OdaMcpManager` 验证
- **应用隔离**: 不同 `app_name` 下的配置相互独立，可以存在相同的 `agent_name`

## 默认智能体配置

系统提供了内置的默认智能体配置功能，通过 `create_default_agent_config` 工厂函数创建：

```python
def create_default_agent_config(app_name: str) -> OdaAgentConfig:
    """创建默认智能体配置
    
    创建一个使用默认LLM配置的智能体配置实例。
    
    Args:
        app_name: 应用名称，用于标识所属的应用程序
        
    Returns:
        默认智能体配置对象
    """
```

### 默认智能体特性：

- **固定标识**：使用 `"default"` 作为 agent_name
- **默认模型**：自动使用默认LLM配置 `"__default_llm_config"`
- **开箱即用**：提供基础的通用智能体功能，无需额外配置
- **零依赖**：默认情况下不依赖任何工具、MCP或子智能体
- **适用场景**：作为会话的默认智能体，提供通用AI助手服务

### 与默认LLM配置的集成：

默认智能体配置与系统的默认LLM配置紧密集成：
- 自动引用 `"__default_llm_config"` 作为模型配置
- 依赖 `OdaModelConfigManager` 提供的默认配置功能
- 当环境变量设置了默认LLM参数时，默认智能体立即可用
- 无需手动配置模型参数，简化系统部署和初始化

## 与 OdaAgentConfigManager 的配合使用

```python
from one_dragon_agent import OdaContext, OdaContextConfig
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
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
    
    # 注册配置
    await agent_config_manager.create_config(agent_config)
    
    # 获取配置
    retrieved_config = await agent_config_manager.get_config("weather_agent")
    if retrieved_config:
        print(f"获取的配置: {retrieved_config}")
    
finally:
    await context.stop()
```

## 注意事项

- 创建和更新配置时会自动验证引用的模型配置和MCP配置是否存在
- 内置默认配置只能通过系统自动创建，不能通过 `create_config()` 创建
- 内置默认配置不能通过 `update_config()` 更新
- 内置默认配置不能通过 `delete_config()` 删除
- `is_built_in_config()` 方法可以检查配置是否为内置配置