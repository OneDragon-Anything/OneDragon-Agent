# OdaContext

`OdaContext` 是系统的全局资源管理器，负责在应用启动时创建和管理所有 ADK 原生服务、管理器组件及共享资源。

## 构造函数

```python
class OdaContext:
    def __init__(self, config: Optional[OdaContextConfig] = None) -> None:
        """初始化 OdaContext 实例
        
        Args:
            config: OdaContext 的全局配置。如果为 None，将从环境变量创建。
        """
```

## 属性

### config

```python
@property
def config(self) -> OdaContextConfig:
    """OdaContext 的全局配置
    
    Returns:
        OdaContextConfig: 配置实例
    """
```

### session_service

```python
@property
def session_service(self) -> Optional[BaseSessionService]:
    """会话数据存储和管理基础设施
    
    Returns:
        Optional[BaseSessionService]: ADK 原生会话服务实例
    """
```

### artifact_service

```python
@property
def artifact_service(self) -> Optional[BaseArtifactService]:
    """工件数据存储和管理基础设施
    
    Returns:
        Optional[BaseArtifactService]: ADK 原生工件服务实例
    """
```

### memory_service

```python
@property
def memory_service(self) -> Optional[BaseMemoryService]:
    """长期记忆管理服务
    
    Returns:
        Optional[BaseMemoryService]: ADK 原生记忆服务实例
    """
```

### model_config_manager

```python
@property
def model_config_manager(self) -> Optional[OdaModelConfigManager]:
    """模型配置管理器，用于 LLM 配置
    
    Returns:
        Optional[OdaModelConfigManager]: 模型配置管理器实例
    """
```

### tool_manager

```python
@property
def tool_manager(self) -> Optional[OdaToolManager]:
    """工具管理器，用于内置工具管理
    
    Returns:
        Optional[OdaToolManager]: 工具管理器实例
    """
```

### mcp_manager

```python
@property
def mcp_manager(self) -> Optional[OdaMcpManager]:
    """MCP 配置和工具管理器，用于 MCP 工具集成
    
    Returns:
        Optional[OdaMcpManager]: MCP 管理器实例
    """
```

### agent_config_manager

```python
@property
def agent_config_manager(self) -> Optional[OdaAgentConfigManager]:
    """智能体配置管理器，用于检索智能体配置
    
    Returns:
        Optional[OdaAgentConfigManager]: 智能体配置管理器实例
    """
```

### agent_manager

```python
@property
def agent_manager(self) -> Optional[OdaAgentManager]:
    """全局智能体实例管理器
    
    Returns:
        Optional[OdaAgentManager]: 智能体管理器实例
    """
```

### session_manager

```python
@property
def session_manager(self) -> Optional[OdaSessionManager]:
    """全局会话实例管理器
    
    Returns:
        Optional[OdaSessionManager]: 会话管理器实例
    """
```

## 方法

### start()

```python
async def start(self) -> None:
    """启动系统并初始化所有服务和管理器
    
    此方法是启动 OdaContext 系统的主要入口点。
    它按照依赖关系的正确顺序初始化所有 ADK 原生服务和 OneDragon 管理组件。
    """
```

### stop()

```python
async def stop(self) -> None:
    """停止系统并释放所有资源
    
    此方法是停止 OdaContext 系统的主要入口点。
    它清理所有资源并关闭所有服务和管理器。
    """
```

## 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig

# 创建配置
config = OdaContextConfig()

# 初始化 OdaContext
context = OdaContext(config)
await context.start()

# 获取各种管理器
session_manager = context.session_manager
agent_manager = context.agent_manager
model_config_manager = context.model_config_manager
tool_manager = context.tool_manager
mcp_manager = context.mcp_manager
agent_config_manager = context.agent_config_manager

# 使用完成后停止
await context.stop()
```

## 注意事项

- OdaContext 不是单例模式，但通常在应用生命周期中只创建一个实例
- 在调用任何管理器之前，必须先调用 `start()` 方法初始化系统
- 在应用关闭时，应调用 `stop()` 方法释放所有资源
- 目前只支持 "memory" 存储类型，其他存储类型尚未实现
- 所有管理器在 `start()` 方法调用后才会被初始化