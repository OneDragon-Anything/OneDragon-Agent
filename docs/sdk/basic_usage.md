# 基础使用

本章将介绍 OneDragon-Agent SDK 的基本操作和常见用法，帮助您快速掌握 SDK 的核心功能。

## 初始化系统

使用 OneDragon-Agent SDK 的第一步是初始化系统。这包括创建配置对象、初始化 OdaContext 并启动系统。

### 基本初始化

```python
import asyncio
from one_dragon_agent import OdaContext, OdaContextConfig

async def main():
    # 创建配置对象
    config = OdaContextConfig()
    
    # 初始化 OdaContext
    context = OdaContext(config)
    
    # 启动系统
    await context.start()
    
    try:
        # 在这里使用 SDK
        pass
    finally:
        # 停止系统并清理资源
        await context.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 使用环境变量配置

如果您已经设置了环境变量（如 `ODA_DEFAULT_LLM_BASE_URL`、`ODA_DEFAULT_LLM_API_KEY`、`ODA_DEFAULT_LLM_MODEL`），系统会自动使用这些配置。

## 会话管理

会话是 OneDragon-Agent 中的核心概念，每个会话代表一个独立的用户对话环境。

### 创建会话

```python
# 获取会话管理器
session_manager = context.get_session_manager()

# 创建新会话
session = await session_manager.create_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"  # 可选，如果不提供会自动生成
)

print(f"会话创建成功: {session}")
```

### 获取现有会话

```python
# 获取指定会话
session = await session_manager.get_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)

if session:
    print("会话存在")
else:
    print("会话不存在")
```

### 列出用户的所有会话

```python
# 列出指定用户的所有会话
sessions = await session_manager.list_sessions(
    app_name="my_app",
    user_id="user_123"
)

print(f"用户 {user_id} 有 {len(sessions)} 个会话")
for session in sessions:
    print(f"- 会话ID: {session}")
```

### 删除会话

```python
# 删除指定会话
await session_manager.delete_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)

print("会话已删除")
```

## 消息处理

消息处理是 SDK 的核心功能，通过会话对象可以发送消息并获取智能体的响应。

### 基本消息处理

```python
# 发送消息并获取响应
response = await session.process_message(
    message="你好，请介绍一下自己",
    agent_name="default"  # 使用默认智能体
)

print(f"智能体响应: {response}")
```

### 指定智能体

如果您有多个智能体，可以通过指定 `agent_name` 来选择使用哪个智能体：

```python
# 使用特定智能体处理消息
response = await session.process_message(
    message="帮我查询一下北京的天气",
    agent_name="weather_agent"  # 使用天气查询智能体
)

print(f"天气查询结果: {response}")
```

### 不指定智能体

如果不指定 `agent_name`，系统会使用会话的默认智能体：

```python
# 不指定智能体，使用默认智能体
response = await session.process_message(
    message="今天天气怎么样？"
)

print(f"响应: {response}")
```

## 多轮对话

OneDragon-Agent 支持多轮对话，会话会自动维护对话历史。

### 多轮对话示例

```python
# 第一轮对话
response1 = await session.process_message(
    message="我叫张三",
    agent_name="default"
)
print(f"第一轮: {response1}")

# 第二轮对话（智能体会记住用户的名字）
response2 = await session.process_message(
    message="我叫什么名字？",
    agent_name="default"
)
print(f"第二轮: {response2}")

# 输出: 你叫张三
```

## 会话状态管理

会话对象提供了一些方法来管理和查询会话状态。

### 检查会话状态

```python
# 检查会话是否活跃
if session.is_active():
    print("会话处于活跃状态")
else:
    print("会话已关闭")
```

### 获取会话信息

```python
# 获取会话的基本信息
info = session.get_session_info()
print(f"会话信息: {info}")
```

### 清理会话资源

```python
# 清理会话资源（包括智能体实例等）
await session.cleanup()
print("会话资源已清理")
```

## 错误处理

在使用 SDK 时，正确处理错误是非常重要的。

### 基本错误处理

```python
try:
    response = await session.process_message(
        message="你好",
        agent_name="default"
    )
    print(f"响应: {response}")
except Exception as e:
    print(f"处理消息时发生错误: {e}")
```

### 处理特定错误

```python
from one_dragon_agent.exceptions import SessionNotFoundError, AgentNotFoundError

try:
    response = await session.process_message(
        message="你好",
        agent_name="nonexistent_agent"
    )
    print(f"响应: {response}")
except AgentNotFoundError as e:
    print(f"智能体不存在: {e}")
except SessionNotFoundError as e:
    print(f"会话不存在: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 完整示例

以下是一个完整的示例，展示了会话管理、消息处理和错误处理的综合用法：

```python
import asyncio
from one_dragon_agent import OdaContext, OdaContextConfig
from one_dragon_agent.exceptions import SessionNotFoundError, AgentNotFoundError

async def main():
    # 初始化系统
    config = OdaContextConfig()
    context = OdaContext(config)
    await context.start()
    
    try:
        # 获取会话管理器
        session_manager = context.get_session_manager()
        
        # 创建会话
        session = await session_manager.create_session(
            app_name="chat_app",
            user_id="user_123",
            session_id="chat_session_001"
        )
        
        print(f"会话创建成功: {session}")
        
        # 第一轮对话
        try:
            response1 = await session.process_message(
                message="你好，我叫李四",
                agent_name="default"
            )
            print(f"智能体: {response1}")
        except Exception as e:
            print(f"第一轮对话错误: {e}")
        
        # 第二轮对话
        try:
            response2 = await session.process_message(
                message="记住我的名字了吗？",
                agent_name="default"
            )
            print(f"智能体: {response2}")
        except Exception as e:
            print(f"第二轮对话错误: {e}")
        
        # 尝试使用不存在的智能体
        try:
            response3 = await session.process_message(
                message="测试错误处理",
                agent_name="nonexistent_agent"
            )
            print(f"智能体: {response3}")
        except AgentNotFoundError as e:
            print(f"捕获到预期错误: {e}")
        
        # 列出用户的所有会话
        sessions = await session_manager.list_sessions(
            app_name="chat_app",
            user_id="user_123"
        )
        print(f"用户 user_123 有 {len(sessions)} 个会话")
        
    finally:
        # 停止系统
        await context.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 最佳实践

在使用 OneDragon-Agent SDK 时，以下是一些最佳实践建议：

### 1. 资源管理

始终确保在程序结束时正确清理资源：

```python
try:
    # 使用 SDK
    pass
finally:
    await context.stop()
```

### 2. 错误处理

为所有可能失败的操作添加适当的错误处理：

```python
try:
    response = await session.process_message(message, agent_name)
except AgentNotFoundError:
    # 处理智能体不存在的情况
    pass
except Exception as e:
    # 处理其他错误
    pass
```

### 3. 会话管理

合理管理会话生命周期，及时清理不需要的会话：

```python
# 使用完成后删除会话
await session_manager.delete_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)
```

### 4. 异步编程

充分利用 Python 的异步特性，避免阻塞操作：

```python
# 可以同时处理多个会话
async def process_multiple_sessions():
    tasks = []
    for i in range(3):
        task = asyncio.create_task(process_single_session(i))
        tasks.append(task)
    
    await asyncio.gather(*tasks)

async def process_single_session(session_id):
    # 处理单个会话的逻辑
    pass
```

---

*通过掌握这些基础用法，您已经可以使用 OneDragon-Agent SDK 构建基本的智能体应用了。接下来，您可以了解更多关于配置管理的内容。*