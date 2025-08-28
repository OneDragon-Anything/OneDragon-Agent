# OdaContextConfig

`OdaContextConfig` 是系统的配置类，定义了 OdaContext 初始化所需的各种配置参数。

## 构造函数

```python
@dataclass
class OdaContextConfig:
    def __init__(
        self,
        storage: str = "memory",
        default_llm_base_url: str | None = None,
        default_llm_api_key: str | None = None,
        default_llm_model: str | None = None
    ):
        """初始化系统配置
        
        Args:
            storage: 存储类型，默认为 "memory"
            default_llm_base_url: 默认的 LLM 服务地址，可选
            default_llm_api_key: 默认的 LLM 服务 API KEY，可选
            default_llm_model: 默认的 LLM 服务模型，可选
        """
```

## 类方法

### from_env

```python
@classmethod
def from_env(cls) -> 'OdaContextConfig':
    """从环境变量创建 OdaContextConfig 实例
    
    Returns:
        OdaContextConfig: 从环境变量创建的配置实例
    """
```

## 属性

### storage

```python
storage: str
```
存储类型，默认为 "memory"

### default_llm_base_url

```python
default_llm_base_url: str | None
```
默认的 LLM 服务地址，可能为 None

### default_llm_api_key

```python
default_llm_api_key: str | None
```
默认的 LLM 服务 API KEY，可能为 None

### default_llm_model

```python
default_llm_model: str | None
```
默认的 LLM 服务模型，可能为 None

## 使用示例

```python
from one_dragon_agent import OdaContextConfig

# 创建配置（从环境变量读取）
config = OdaContextConfig.from_env()

# 或者直接创建配置实例
config = OdaContextConfig(
    storage="memory",
    default_llm_base_url="https://api.example.com",
    default_llm_api_key="your-api-key",
    default_llm_model="gemini-2.0-flash"
)

# 访问配置属性
print(f"存储方式: {config.storage}")
print(f"默认 LLM 地址: {config.default_llm_base_url}")
print(f"默认 LLM 模型: {config.default_llm_model}")
```

## 环境变量配置

在 Linux/macOS 系统中：

```bash
export ODA_STORAGE=memory
export ODA_DEFAULT_LLM_BASE_URL="https://api.example.com"
export ODA_DEFAULT_LLM_API_KEY="your-api-key"
export ODA_DEFAULT_LLM_MODEL="gemini-2.0-flash"
```

在 Windows 系统中：

```cmd
set ODA_STORAGE=memory
set ODA_DEFAULT_LLM_BASE_URL="https://api.example.com"
set ODA_DEFAULT_LLM_API_KEY="your-api-key"
set ODA_DEFAULT_LLM_MODEL="gemini-2.0-flash"
```

## 注意事项

- OdaContextConfig 是一个 dataclass，提供了简洁的配置管理方式
- 可以通过 `from_env()` 类方法从环境变量创建配置实例
- 也可以直接通过构造函数创建配置实例
- 目前只支持 "memory" 存储类型，其他存储类型尚未实现
- 默认 LLM 配置是可选的，如果不提供，系统将使用默认配置