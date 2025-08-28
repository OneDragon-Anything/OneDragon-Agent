# OdaSession

`OdaSession` 代表一个独立的用户对话会话，是 ADK 原生组件的业务包装器。

## 构造函数

```python
class OdaSession:
    def __init__(
        self, 
        app_name: str, 
        user_id: str, 
        session_id: str, 
        agent_manager: OdaAgentManager
    ) -> None:
        """初始化 OdaSession，传入会话标识和智能体管理器
        
        Args:
            app_name: 应用名称
            user_id: 用户标识
            session_id: 会话标识
            agent_manager: 智能体管理器实例
        """
```

## 方法

### process_message()

```python
async def process_message(self, message: str, agent_name: Optional[str] = None):
    """处理用户消息并返回事件流生成器
    
    Args:
        message: 用户输入消息
        agent_name: 可选的智能体名称，使用默认智能体如果为 None
        
    Returns:
        AsyncGenerator[Event, None]: 来自智能体的事件流生成器
    """
```

### cleanup()

```python
async def cleanup(self) -> None:
    """清理会话资源"""
```

## 属性

### app_name

```python
app_name: str
```
应用名称

### user_id

```python
user_id: str
```
用户标识

### session_id

```python
session_id: str
```
会话标识

### agent_manager

```python
agent_manager: OdaAgentManager
```
智能体管理器实例

### _agent_pool

```python
_agent_pool: Dict[str, OdaAgent]
```
缓存的 OdaAgent 实例池

### _lock

```python
_lock: asyncio.Lock
```
用于线程安全操作的异步锁

### _session_state

```python
_session_state: dict
```
会话业务状态和上下文

## 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取会话管理器
    session_manager = context.session_manager
    
    # 创建会话
    session = await session_manager.create_session(
        app_name="my_app",
        user_id="user_123",
        session_id="session_001"
    )
    
    # 处理消息并迭代事件
    async for event in session.process_message(
        message="你好，请介绍一下自己",
        agent_name="default"
    ):
        print(f"事件: {event}")
    
    # 不指定智能体，使用默认智能体
    async for event in session.process_message(
        message="今天天气怎么样？"
    ):
        print(f"事件: {event}")
    
finally:
    # 清理会话资源
    await session.cleanup()
    await context.stop()
```

## 多轮对话示例

```python
# 第一轮对话
async for event in session.process_message(
    message="我叫张三",
    agent_name="default"
):
    if hasattr(event, 'content') and event.content:
        print(f"第一轮: {event.content}")

# 第二轮对话（智能体会记住用户的名字）
async for event in session.process_message(
    message="我叫什么名字？",
    agent_name="default"
):
    if hasattr(event, 'content') and event.content:
        print(f"第二轮: {event.content}")

# 输出: 你叫张三
```

## 注意事项

- process_message 方法返回的是一个异步生成器，需要使用 async for 迭代
- 每个会话维护自己的智能体实例池，提高性能
- 会话支持多轮对话，上下文会在同一会话中保持
- 使用完毕后应调用 cleanup 方法清理资源
- 会话内部使用锁机制确保线程安全