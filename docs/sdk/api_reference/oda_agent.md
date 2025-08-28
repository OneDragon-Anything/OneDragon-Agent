# OdaAgent

`OdaAgent` 是 OneDragon 自定义的智能体封装类，持有 ADK 原生 `Runner` 实例，为 `OdaSession` 提供简化的业务接口。

## 构造函数

```python
class OdaAgent:
    def __init__(
        self, 
        runner: Runner,
        app_name: str, 
        user_id: str, 
        session_id: str, 
        max_retries: int = 3
    ) -> None:
        """初始化 OdaAgent，传入 Runner 实例和会话标识
        
        Args:
            runner: ADK Runner 实例
            app_name: 应用名称
            user_id: 用户标识
            session_id: 会话标识
            max_retries: 最大重试次数，默认为 3 次
        """
```

## 方法

### run_async()

```python
async def run_async(self, new_message: str) -> AsyncGenerator[Event, None]:
    """异步执行智能体，返回 Event 流生成器，内部实现错误重试机制
    
    提供与 ADK Runner 相同的接口，内置错误重试机制：
    - 首次执行使用原始用户消息，确保消息只提交一次
    - 检测到执行异常时，按递增间隔自动重试
    - 重试时不重复用户消息，从当前会话状态恢复
    - 生成 ADK 原生标准事件通知重试状态
    - 达到最大重试次数后产生最终错误事件
    
    Args:
        new_message: 用户消息内容
        
    Returns:
        AsyncGenerator[Event, None]: 事件流生成器
    """
```

### run()

```python
def run(self, new_message: str) -> Generator[Event, None, None]:
    """同步执行智能体，返回 Event 流生成器，内部实现错误重试机制
    
    提供与 ADK Runner 相同的接口，内置错误重试机制。
    实现同步重试逻辑和指数退避策略。
    
    Args:
        new_message: 用户消息内容
        
    Returns:
        Generator[Event, None, None]: 事件流生成器
    """
```

### cleanup()

```python
async def cleanup(self) -> None:
    """清理智能体资源"""
```

### get_agent_info()

```python
def get_agent_info(self) -> dict:
    """获取智能体信息
    
    Returns:
        dict: 智能体信息
    """
```

### is_ready()

```python
def is_ready(self) -> bool:
    """检查智能体是否就绪
    
    Returns:
        bool: 智能体是否就绪
    """
```

## 属性

### runner

```python
runner: Runner
```
ADK 原生 Runner 实例

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

### max_retries

```python
max_retries: int
```
最大重试次数

### _retry_count

```python
_retry_count: int
```
当前重试次数

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
    
    # 异步执行智能体
    async for event in session.process_message("你好，请介绍一下自己"):
        print(f"事件: {event}")
    
    # 获取智能体信息
    # 注意：智能体实例由会话内部管理，通常不需要直接访问
    
finally:
    await context.stop()
```

## 重试机制

`OdaAgent` 内置了错误重试机制，当检测到执行异常时会自动重试：

1. **重试触发条件**：在 Event 流处理层面检测到异常
2. **重试策略**：
   - 最大重试次数：默认 3 次（可通过构造函数参数配置）
   - 重试间隔：递增策略（1s, 2s, 4s, 8s...）
3. **重试行为**：
   - 首次执行时使用原始用户消息
   - 重试时不重复用户消息，从当前会话状态恢复
   - 产生符合 ADK 原生标准的事件通知重试状态
4. **最终处理**：
   - 达到最大重试次数后产生最终错误事件
   - 最终错误事件包含 `escalate: true` 标识

## 注意事项

- OdaAgent 是 ADK Runner 的轻量级包装器，提供会话隔离和错误重试机制
- 智能体实例由 OdaSession 内部管理，通常不需要直接创建或访问
- 所有方法都支持错误重试，提高系统稳定性
- 使用完毕后应调用 cleanup 方法清理资源