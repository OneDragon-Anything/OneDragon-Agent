# OdaAgentManager

`OdaAgentManager` 负责系统中所有智能体实例的完整生命周期管理，为上层应用提供标准化的智能体操作接口。

## 构造函数

```python
class OdaAgentManager:
    def __init__(
        self, 
        session_service: BaseSessionService,
        artifact_service: BaseArtifactService,
        memory_service: BaseMemoryService,
        tool_manager: OdaToolManager,
        mcp_manager: OdaMcpManager,
        model_config_manager: OdaModelConfigManager,
        agent_config_manager: OdaAgentConfigManager
    ) -> None:
        """使用 ADK 服务实例初始化 OdaAgentManager
        
        Args:
            session_service: ADK 原生会话服务实例
            artifact_service: ADK 原生工件服务实例
            memory_service: ADK 原生记忆服务实例
            tool_manager: 用于内置工具管理的工具管理器实例
            mcp_manager: 用于 MCP 工具管理的 MCP 管理器实例
            model_config_manager: 模型配置管理器实例
            agent_config_manager: 智能体配置管理器实例
        """
```

## 方法

### create_agent()

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

## 属性

### session_service

```python
session_service: BaseSessionService
```
ADK 原生会话服务，用于会话管理

### artifact_service

```python
artifact_service: BaseArtifactService
```
ADK 原生工件服务，用于工件存储

### memory_service

```python
memory_service: BaseMemoryService
```
ADK 原生记忆服务，用于长期记忆

### tool_manager

```python
tool_manager: OdaToolManager
```
工具管理器，用于内置工具管理

### mcp_manager

```python
mcp_manager: OdaMcpManager
```
MCP 配置和工具管理器，用于 MCP 工具集成

### model_config_manager

```python
model_config_manager: OdaModelConfigManager
```
模型配置管理器，用于 LLM 配置

### agent_config_manager

```python
agent_config_manager: OdaAgentConfigManager
```
智能体配置管理器，用于检索智能体配置

### _lock

```python
_lock: asyncio.Lock
```
用于线程安全操作的异步锁

## 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取智能体管理器
    agent_manager = context.agent_manager
    
    # 创建智能体
    agent = await agent_manager.create_agent(
        agent_name="weather_agent",
        app_name="my_app",
        user_id="user_123",
        session_id="session_001"
    )
    
    # 使用智能体处理消息
    async for event in agent.run_async("今天天气怎么样？"):
        print(f"事件: {event}")
    
finally:
    await context.stop()
```

## 工作流程

1. **获取智能体配置**：通过 `OdaAgentConfigManager` 获取指定名称的智能体配置
2. **验证配置有效性**：检查配置中的模型配置、MCP 配置等是否有效
3. **创建 ADK 原生组件**：
   - 创建 `LlmAgent` 实例
   - 创建 `Runner` 实例
   - 注入所需的服务（SessionService、ArtifactService、MemoryService）
4. **创建 OdaAgent 实例**：将 ADK 原生组件包装为 `OdaAgent` 实例
5. **绑定会话**：将智能体实例绑定到指定的会话标识

## 注意事项

- 每个会话的智能体实例是完全独立的，不会共享状态
- 智能体实例的生命周期由会话管理，会话清理时会自动清理关联的智能体实例
- 智能体配置必须预先通过 `OdaAgentConfigManager` 创建
- 如果智能体配置中引用了 MCP 配置，这些 MCP 配置必须存在且启用
- OdaAgentManager 由 OdaContext 持有，不应直接实例化
- 所有方法都是异步的，需要使用 await 调用