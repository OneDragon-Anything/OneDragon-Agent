# OdaSessionManager

`OdaSessionManager` 负责系统中所有会话实例的完整生命周期管理，为上层应用提供标准化的会话操作接口。

## 构造函数

```python
class OdaSessionManager:
    def __init__(self, session_service: BaseSessionService, agent_manager: OdaAgentManager) -> None:
        """使用 SessionService 和 AgentManager 实例初始化 OdaSessionManager
        
        Args:
            session_service: ADK 原生会话服务实例
            agent_manager: 用于创建 OdaAgent 实例的智能体管理器实例
        """
```

## 方法

### create_session()

```python
async def create_session(
    self, 
    app_name: str, 
    user_id: str, 
    session_id: Optional[str] = None
) -> OdaSession:
    """创建新的会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        session_id: 可选的会话标识（如果为 None 则自动生成）

    Returns:
        OdaSession: 创建的会话实例
    """
```

### get_session()

```python
async def get_session(
    self, 
    app_name: str, 
    user_id: str, 
    session_id: str
) -> Optional[OdaSession]:
    """获取指定的会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        session_id: 会话标识
        
    Returns:
        Optional[OdaSession]: 会话实例或 None（如果未找到）
    """
```

### list_sessions()

```python
async def list_sessions(
    self, 
    app_name: str, 
    user_id: str
) -> List[OdaSession]:
    """列出用户的所有会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        
    Returns:
        List[OdaSession]: 会话实例列表
    """
```

### delete_session()

```python
async def delete_session(
    self, 
    app_name: str, 
    user_id: str, 
    session_id: str
) -> None:
    """删除指定的会话实例
    
    Args:
        app_name: 应用名称
        user_id: 用户标识
        session_id: 会话标识
    """
```

### cleanup_inactive_sessions()

```python
async def cleanup_inactive_sessions(self, timeout_seconds: int) -> None:
    """清理不活动的会话实例
    
    Args:
        timeout_seconds: 会话超时时间（秒）
    """
```

### set_concurrent_limit()

```python
async def set_concurrent_limit(self, max_concurrent_sessions: int) -> None:
    """设置并发会话数量限制
    
    Args:
        max_concurrent_sessions: 允许的最大并发会话数
    """
```

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
    
    # 清理超时会话
    await session_manager.cleanup_inactive_sessions(timeout_seconds=3600)
    
    # 设置并发限制
    await session_manager.set_concurrent_limit(max_concurrent_sessions=100)
    
finally:
    await context.stop()
```

## 属性

### session_service

```python
session_service: BaseSessionService
```
ADK 原生会话服务，用于数据存储和管理

### agent_manager

```python
agent_manager: OdaAgentManager
```
智能体管理器，用于创建 OdaAgent 实例

### _session_pool

```python
_session_pool: dict[str, OdaSession]
```
活动 OdaSession 实例的内存缓存

### _lock

```python
_lock: asyncio.Lock
```
用于线程安全操作的异步锁

### _max_concurrent_sessions

```python
_max_concurrent_sessions: Optional[int]
```
允许的最大并发会话数

### _session_last_access

```python
_session_last_access: dict[str, float]
```
跟踪会话最后访问时间，用于会话清理

## 注意事项

- OdaSessionManager 由 OdaContext 持有，不应直接实例化
- 所有方法都是异步的，需要使用 await 调用
- 会话实例在内存中缓存，提高访问性能
- 支持并发会话数量限制，防止资源过度使用
- 自动清理超时会话，防止内存泄漏