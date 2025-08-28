# OdaAgentConfigManager

`OdaAgentConfigManager` 负责智能体配置的创建、存储、检索和管理。

## 构造函数

```python
class OdaAgentConfigManager:
    def __init__(
        self,
        config_service: BaseOdaAgentConfigStorage,
        model_config_manager: OdaModelConfigManager,
        mcp_manager: OdaMcpManager,
    ) -> None:
        """初始化智能体配置管理器
        
        Args:
            config_service: 配置存储服务，可以是任何继承自 BaseOdaAgentConfigStorage 的实现
            model_config_manager: 模型配置管理器，用于验证模型配置
            mcp_manager: MCP 管理器，用于验证 MCP 配置
        """
```

## 方法

### create_config()

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

### get_config()

```python
async def get_config(self, agent_name: str) -> OdaAgentConfig | None:
    """获取智能体配置
    
    Args:
        agent_name: 智能体名称，唯一标识符
        
    Returns:
        OdaAgentConfig | None: 配置对象，如果不存在则返回 None
    """
```

### update_config()

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

### delete_config()

```python
async def delete_config(self, agent_name: str) -> None:
    """删除智能体配置
    
    Args:
        agent_name: 要删除的智能体名称
    """
```

### list_configs()

```python
async def list_configs(self) -> list[OdaAgentConfig]:
    """获取所有智能体配置
    
    Returns:
        list[OdaAgentConfig]: 所有持久化配置对象的列表（不包括内置默认配置）
    """
```

### validate_model_config()

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

### validate_mcp_config()

```python
async def validate_mcp_config(self, app_name: str, mcp_list: list[str]) -> bool:
    """验证 MCP 配置是否有效
    
    Args:
        app_name: 应用名称
        mcp_list: MCP 配置 ID 列表
        
    Returns:
        bool: 如果所有 MCP 配置都有效返回 True，否则返回 False
    """
```

### is_built_in_config()

```python
def is_built_in_config(self, agent_name: str) -> bool:
    """检查是否为内置配置
    
    Args:
        agent_name: 智能体名称
        
    Returns:
        bool: 如果为内置配置返回 True，否则返回 False
    """
```

## 属性

### config_service

```python
config_service: BaseOdaAgentConfigStorage
```
配置存储服务，用于持久化操作

### model_config_manager

```python
model_config_manager: OdaModelConfigManager
```
模型配置管理器，用于验证模型配置

### mcp_manager

```python
mcp_manager: OdaMcpManager
```
MCP 管理器，用于验证 MCP 配置

### _default_config

```python
_default_config: OdaAgentConfig | None
```
缓存的默认配置实例

## 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig, OdaAgentConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取智能体配置管理器
    agent_config_manager = context.agent_config_manager
    
    # 创建智能体配置
    agent_config = OdaAgentConfig(
        app_name="my_app",
        agent_name="weather_agent",
        agent_type="default",
        description="天气查询智能体",
        instruction="你是一个天气查询助手，帮助用户获取天气信息",
        model_config="gemini-config",
        tool_list=[],
        mcp_list=[],
        sub_agent_list=[]
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
    
    # 更新智能体配置
    config.instruction = "你是一个专业的天气查询助手，提供准确的天气信息和穿衣建议"
    await agent_config_manager.update_config(config)
    
    # 删除智能体配置
    await agent_config_manager.delete_config("weather_agent")
    
finally:
    await context.stop()
```

## 内置默认配置

系统内置了一个名为 "default" 的默认智能体配置，该配置自动加载且不可修改，为系统提供开箱即用的基础智能体功能。

### 默认智能体特性

- **固定标识**：使用 `"default"` 作为 agent_name
- **默认模型**：自动使用默认LLM配置 `"__default_llm_config"`
- **开箱即用**：提供基础的通用智能体功能，无需额外配置
- **零依赖**：默认情况下不依赖任何工具、MCP或子智能体
- **适用场景**：作为会话的默认智能体，提供通用AI助手服务

### 与默认LLM配置的集成

默认智能体配置与系统的默认LLM配置紧密集成：
- 自动引用 `"__default_llm_config"` 作为模型配置
- 依赖 `OdaModelConfigManager` 提供的默认配置功能
- 当环境变量设置了默认LLM参数时，默认智能体立即可用
- 无需手动配置模型参数，简化系统部署和初始化

## 注意事项

- 内置默认配置只能通过系统自动创建，不能通过 `create_config()` 创建
- 内置默认配置不能通过 `update_config()` 更新
- 内置默认配置不能通过 `delete_config()` 删除
- 创建和更新配置时会自动验证引用的模型配置和MCP配置是否存在
- `is_built_in_config()` 方法可以检查配置是否为内置配置
- OdaAgentConfigManager 由 OdaContext 持有，不应直接实例化
- 所有方法都是异步的，需要使用 await 调用