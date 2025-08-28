# OdaModelConfigManager

`OdaModelConfigManager` 负责大模型配置的创建、存储、检索和管理。

## 构造函数

```python
class OdaModelConfigManager:
    def __init__(self, config_service: BaseOdaModelConfigStorage, context_config: OdaContextConfig) -> None:
        """初始化模型配置管理器
        
        初始化配置管理器，并从注入的 OdaContextConfig 创建默认配置实例
        （如果所有必需的默认 LLM 设置都存在）。默认配置缓存在内存中以便高效访问。
        
        Args:
            config_service: 配置服务实例，可以是任何继承自 BaseOdaModelConfigStorage 的实现
            context_config: 包含从环境变量加载的默认 LLM 设置的上下文配置对象
        """
```

## 方法

### create_config()

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

### get_config()

```python
async def get_config(self, model_id: str) -> OdaModelConfig | None:
    """获取大模型配置
    
    支持获取持久化配置和默认配置。当请求默认配置 ID 时，
    返回内存中的默认配置实例（不进行持久化查询）。
    
    Args:
        model_id: 大模型唯一标识符，支持特殊默认配置 ID "__default_llm_config"
        
    Returns:
        OdaModelConfig | None: 配置对象，如果不存在则返回 None
        
    Note:
        默认配置 ID "__default_llm_config" 为保留 ID，用于标识基于环境变量的默认配置
    """
```

### get_default_config()

```python
def get_default_config(self) -> OdaModelConfig | None:
    """获取默认大模型配置
    
    直接返回初始化时缓存的默认配置实例，不涉及持久化操作。
    默认配置在管理器初始化时从注入的 OdaContextConfig 中一次性读取，
    该配置由 OdaContext 统一从环境变量 ODA_DEFAULT_LLM_BASE_URL、
    ODA_DEFAULT_LLM_API_KEY、ODA_DEFAULT_LLM_MODEL 中读取并验证，
    使用固定的特殊 ID "__default_llm_config"。
    
    Returns:
        OdaModelConfig | None: 默认配置对象，如果 OdaContextConfig 中未设置默认配置则返回 None
        
    Note:
        该方法直接返回缓存实例，性能高效，适合频繁调用获取默认配置
    """
```

### update_config()

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

### delete_config()

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

### list_configs()

```python
async def list_configs(self) -> list[OdaModelConfig]:
    """获取所有大模型配置
    
    返回系统中所有可用的大模型配置，包括：
    - 持久化配置：通过 create_config 创建的自定义配置
    - 内置默认配置：基于 OdaContextConfig 生成的默认配置
    
    Returns:
        list[OdaModelConfig]: 包含所有配置对象的列表，默认配置总是出现在列表末尾
        
    Note:
        该方法提供完整的配置视图，便于上层应用了解所有可用的模型配置
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

## 属性

### config_service

```python
config_service: BaseOdaModelConfigStorage
```
配置服务实例，用于持久化操作

### _default_config

```python
_default_config: OdaModelConfig | None
```
缓存的默认配置实例

## 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig, OdaModelConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取模型配置管理器
    model_config_manager = context.model_config_manager
    
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
    
    # 更新模型配置
    config.model = "gemini-2.0-pro"
    await model_config_manager.update_config(config)
    
    # 删除模型配置
    await model_config_manager.delete_config("gemini-config")
    
finally:
    await context.stop()
```

## 默认配置

系统支持通过环境变量配置默认的LLM服务，当设置了以下三个环境变量时，系统会自动创建一个默认的LLM配置：

- `ODA_DEFAULT_LLM_BASE_URL`: 默认LLM服务的基础URL
- `ODA_DEFAULT_LLM_API_KEY`: 访问默认LLM服务的API密钥
- `ODA_DEFAULT_LLM_MODEL`: 默认使用的LLM模型名称

默认配置将使用固定的ID `__default_llm_config`，并在OdaModelConfigManager初始化时自动创建。这个配置可以被应用程序直接使用，无需额外的配置管理操作。

## 注意事项

- 默认配置只能通过环境变量设置，不能通过 `create_config()` 创建
- 默认配置不能通过 `update_config()` 更新，需要修改环境变量并重启系统
- 默认配置不能通过 `delete_config()` 删除，因为它是系统级配置
- `get_default_config()` 直接返回缓存实例，性能高效，适合频繁调用
- OdaModelConfigManager 由 OdaContext 持有，不应直接实例化
- 所有方法都是异步的，需要使用 await 调用（除了 get_default_config）