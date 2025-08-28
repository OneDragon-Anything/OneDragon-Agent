# 核心概念

本章将深入介绍 OneDragon-Agent SDK 的核心概念、架构设计和关键组件，帮助您更好地理解和使用 SDK。

## 架构概述

OneDragon-Agent 基于 Google Agent Development Kit (ADK) 构建，采用分层架构设计，通过必要的封装层提供业务友好的接口。

### 架构层次

```
应用层 (CLI/Web)
    ↓
OneDragon 封装层 (业务接口)
    ↓
ADK 原生组件 (核心执行引擎)
```

### 核心特点

- **ADK 原生**: 直接使用 ADK 核心组件，通过封装层提供业务接口
- **异步流式处理**: 完全基于 ADK 的异步生成器模式
- **多会话支持**: 天然支持多会话、多智能体场景
- **异步优先**: 所有操作都是异步的，性能优异

## 核心组件

### OdaContext (全局资源管理器)

`OdaContext` 是系统的全局服务容器和资源管理器，采用单例模式，在系统生命周期内保持唯一实例。

#### 主要职责

- **系统初始化**: 负责系统启动时各服务组件和管理组件的初始化
- **资源分配**: 负责根据系统需求分配和管理各类资源
- **生命周期管理**: 负责系统整体的启动、运行和关闭
- **依赖注入**: 负责各组件间的依赖关系管理和注入
- **全局配置管理**: 负理系统级别的配置信息和整体生命周期

#### 持有组件

- `SessionService`: 会话数据的存储和管理基础设施
- `ArtifactService`: 工件数据的存储和管理基础设施
- `MemoryService`: 长期记忆管理的 ADK 原生服务
- `OdaSessionManager`: 会话实例的全局管理器
- `OdaAgentManager`: 智能体配置的全局管理器
- `OdaMcpManager`: MCP 配置和工具的全局管理器

#### 使用示例

```python
from one_dragon_agent import OdaContext, OdaContextConfig

# 创建配置
config = OdaContextConfig()

# 初始化 OdaContext
context = OdaContext(config)
await context.start()

# 获取各种管理器
session_manager = context.get_session_manager()
agent_manager = context.get_agent_manager()
mcp_manager = context.get_mcp_manager()

# 使用完成后停止
await context.stop()
```

### OdaSessionManager (会话管理层)

`OdaSessionManager` 负责系统中所有会话实例的完整生命周期管理，为上层应用提供标准化的会话操作接口。

#### 主要职责

- **会话实例管理**: 负责 `OdaSession` 实例的创建、查找、更新和删除
- **生命周期控制**: 管理会话实例的生命周期，包括超时清理和资源释放
- **会话级别接口**: 提供会话级别的查询、统计和监控接口
- **协调操作**: 作为 `OdaContext` 和 `OdaSession` 之间的桥梁
- **资源管理**: 确保会话资源的合理分配和使用

#### 核心接口

```python
class OdaSessionManager:
    async def create_session(self, app_name: str, user_id: str, session_id: str = None) -> OdaSession:
        """创建新的会话实例"""
        
    async def get_session(self, app_name: str, user_id: str, session_id: str) -> Optional[OdaSession]:
        """获取指定的会话实例"""
        
    async def list_sessions(self, app_name: str, user_id: str) -> list[OdaSession]:
        """列出用户的所有会话实例"""
        
    async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        """删除指定的会话实例"""
```

### OdaSession (会话实例层)

`OdaSession` 代表一个独立的、隔离的用户对话会话，是 ADK 原生组件的业务包装器。

#### 主要职责

- **消息处理**: 提供用户消息发送、智能体选择、状态查询等核心业务功能
- **会话业务逻辑**: 负责会话的业务逻辑处理、状态管理和生命周期控制
- **多智能体支持**: 支持同一会话中多个智能体的无缝切换和协作
- **状态管理**: 管理会话的业务状态和用户上下文
- **生命周期管理**: 负责会话资源的分配、使用和清理

#### 核心接口

```python
class OdaSession:
    async def process_message(self, message: str, agent_name: str = None) -> str:
        """处理用户消息，返回最终响应"""
        
    async def cleanup(self) -> None:
        """清理会话资源"""
```

#### 使用示例

```python
# 创建会话
session = await session_manager.create_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_001"
)

# 处理消息
response = await session.process_message(
    message="你好，请介绍一下自己",
    agent_name="default"
)

print(f"响应: {response}")
```

### OdaAgentManager (智能体管理层)

`OdaAgentManager` 负责系统中所有智能体实例的完整生命周期管理，为上层应用提供标准化的智能体操作接口。

#### 主要职责

- **智能体实例创建**: 通过 ADK 原生 `LlmAgent` 工厂模式创建 `OdaAgent` 实例
- **会话绑定管理**: 创建后立即将 `OdaAgent` 实例绑定到具体的 `OdaSession`
- **服务依赖注入**: 在创建 `OdaAgent` 实例时直接使用持有的服务实例
- **工具实例创建**: 通过 `OdaToolManager` 创建智能体所需的工具实例
- **配置管理**: 通过 `OdaAgentConfigManager` 获取智能体配置

#### 核心接口

```python
class OdaAgentManager:
    async def create_agent(self, agent_name: str, app_name: str, user_id: str, session_id: str) -> OdaAgent:
        """创建智能体实例"""
```

### OdaAgent (智能体封装层)

`OdaAgent` 是 OneDragon 自定义的智能体封装类，持有 ADK 原生 `Runner` 实例，为 `OdaSession` 提供简化的业务接口。

#### 主要职责

- **Runner 管理**: 管理 ADK 原生 `Runner` 实例的生命周期
- **业务接口封装**: 提供简化的业务方法，内部调用 `Runner.run_async()` 并内置错误重试机制
- **执行逻辑处理**: 处理用户消息的完整执行流程，包括事件流处理和结果提取
- **错误重试管理**: 在 Runner 执行异常时自动进行重试，支持可配置的重试次数和递增间隔策略

#### 核心接口

```python
class OdaAgent:
    async def run_async(self, new_message: str):
        """异步执行智能体，返回Event流生成器，内部实现错误重试机制"""
        
    def run(self, new_message: str):
        """同步执行智能体，返回Event流生成器，内部实现错误重试机制"""
        
    def get_agent_info(self) -> dict:
        """获取智能体信息"""
        
    def is_ready(self) -> bool:
        """检查智能体是否就绪"""
        
    async def cleanup(self) -> None:
        """清理智能体资源"""
```

## 会话标识与智能体管理

### 会话标识三元组

ADK 使用**三元组**唯一标识每个会话：

- `app_name` - 应用名称（如：客服应用、数据分析应用）
- `user_id` - 用户标识（如：user_123）
- `session_id` - 会话标识（如：session_abc）

### 每个会话独立智能体

**智能体使用策略**：

- **会话隔离**：每个会话创建自己独立的 `OdaAgent` 实例
- **独立实例**：相同 `agent_name` 在不同会话中创建完全独立的智能体实例
- **状态隔离**：每个会话的智能体只访问本会话的对话历史，跨会话完全隔离

## ADK 异步流式处理架构

ADK 采用异步流式处理架构设计，基于 Python 的异步生成器模式。Agent 通过生成器产生 Event 流，Runner 通过迭代处理这些 Event，形成完整的异步处理链路。

### Event 类型

ADK 中 Event 是 Agent 和 Runner 之间的通信载体，主要类型包括：

1. **用户输入Event**: `Event(author='user', content=...)`
2. **智能体响应Event**: `Event(author='AgentName', content=...)`
3. **工具调用Event**: `Event(content={function_call: ...})`
4. **工具结果Event**: `Event(content={function_response: ...})`
5. **状态变更Event**: `Event(actions={state_delta: ...})`
6. **控制流Event**: `Event(actions={transfer_to_agent: ...})`
7. **错误重试Event**: `Event(error_code="RETRY_ATTEMPT", error_message="...")`
8. **最终错误Event**: `Event(error_code="MAX_RETRIES_EXCEEDED", error_message="...", actions={escalate: true})`

### 异步流式处理流程

1. `Runner.run_async()` 内部调用 `LlmAgent.run_async()` 并迭代其返回的事件流
2. `LlmAgent` 通过 `yield Event` 生成事件流
3. 每次迭代处理一个 Event，调用相应的服务提交状态变更
4. `Runner` 处理完后 `yield event` 给上层消费者
5. `OdaAgent` 在 Event 流处理层面检测到异常时触发错误重试机制
6. 重试事件通过标准的 `error_code` 和 `error_message` 传递错误信息
7. 达到最大重试次数后，产生包含 `escalate: true` 的最终错误事件
8. 最终 Event 流返回给应用层

## 设计原则

OneDragon-Agent 遵循以下设计原则：

- **简洁性**: 避免过度抽象，直接利用 ADK 原生能力
- **模块化**: 组件间职责清晰，便于维护和扩展
- **封装性**: 通过封装层隐藏 ADK 复杂性，提供简化接口
- **性能导向**: 优先考虑异步处理和资源利用效率
- **可扩展性**: 支持动态添加智能体和功能扩展

## 命名约定

为了确保代码的清晰性和一致性，项目遵循以下命名约定：

### `Oda` 前缀的使用

- **使用场景**: `Oda` 前缀（代表 One Dragon Agent）仅用于 OneDragon 自定义的核心包装类
- **示例**: `OdaContext`, `OdaSession`, `OdaSessionManager`, `OdaAgentManager`

### 省略 `Oda` 前缀

- **使用场景**: 对于 ADK 原生类和配置类，省略 `Oda` 前缀
- **目的**:
  - **清晰性**: 明确区分 ADK 原生组件和 OneDragon 自定义组件
  - **一致性**: 与 ADK 官方命名风格保持一致
  - **简洁性**: 避免冗余，使类名更简洁
- **示例**: `OdaAgentConfig`, `SessionConfig`, `SessionInfo`, `Runner`, `LlmAgent`

---

*通过理解这些核心概念，您将能够更好地使用 OneDragon-Agent SDK 构建强大的智能体应用。*