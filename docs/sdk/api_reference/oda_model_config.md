# OdaModelConfig

`OdaModelConfig` 是大模型配置的数据类，包含大模型的所有配置信息。

## 构造函数

```python
@dataclass
class OdaModelConfig:
    def __init__(
        self,
        app_name: str,
        model_id: str,
        base_url: str,
        api_key: str,
        model: str
    ):
        """初始化大模型配置
        
        Args:
            app_name: 用于标识所属的应用程序
            model_id: 大模型唯一标识符
            base_url: 大模型 API 基础 URL
            api_key: 访问大模型 API 的密钥
            model: 实际使用的模型名称
        """
```

## 属性

### app_name

```python
app_name: str
```
用于标识所属的应用程序，与 adk-python 中的定义相同

### model_id

```python
model_id: str
```
大模型唯一标识符，在 app_name 范围内必须唯一

### base_url

```python
base_url: str
```
大模型 API 基础 URL

### api_key

```python
api_key: str
```
访问大模型 API 的密钥

### model

```python
model: str
```
实际使用的模型名称

## 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig

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
    
    # 注册配置
    await model_config_manager.create_config(model_config)
    
    # 获取配置
    retrieved_config = await model_config_manager.get_config("gemini-config")
    if retrieved_config:
        print(f"获取的配置: {retrieved_config}")
    
    # 访问配置属性
    print(f"应用名称: {model_config.app_name}")
    print(f"模型ID: {model_config.model_id}")
    print(f"API URL: {model_config.base_url}")
    print(f"模型名称: {model_config.model}")
    
finally:
    await context.stop()
```

## 配置约束

- **唯一性约束**: `model_id` 在同一 `app_name` 下必须唯一
- **引用完整性**: 配置中的 URL 和 API Key 必须有效可访问
- **模型兼容性**: `model` 必须是目标 API 服务支持的模型名称
- **应用隔离**: 不同 `app_name` 下的配置相互独立，可以存在相同的 `model_id`

## 注意事项

- OdaModelConfig 是一个 dataclass，提供了简洁的配置管理方式
- API 密钥是敏感信息，建议通过环境变量或安全配置管理
- 配置创建后会进行验证，确保参数的有效性
- 默认配置使用固定的 ID `__default_llm_config`，不建议在自定义配置中使用
- 不同应用之间的配置是隔离的，可以存在相同的 model_id