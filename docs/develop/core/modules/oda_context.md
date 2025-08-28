# OdaContext 模块设计文档

## 1. 概述

`OdaContext` 是 OneDragon-Agent 的全局资源管理器和应用入口。作为系统的核心容器，它负责在应用启动时创建和管理所有ADK原生服务、管理器组件及共享资源，为上层应用提供统一的资源访问接口。

`OdaContext` 采用单例模式，在系统生命周期内保持唯一实例，确保资源的统一管理和服务的可靠交付。

## 2. 架构总览

`OdaContext` 作为系统的顶层容器，实现了ADK原生组件与业务层的解耦。它通过依赖注入的方式管理各组件的生命周期，确保系统启动时所有必要资源得到正确初始化。

`OdaContext` 本身不参与具体业务逻辑执行，专注于资源的创建、持有、依赖注入和生命周期管理，为整个系统提供稳定可靠的基础设施支持。

## 3. 核心概念

*   **`OdaContext`**: 系统的全局资源管理器，负责ADK原生服务和OneDragon管理器组件的统一管理。
*   **`OdaContextConfig`**: 系统的配置类，定义 `OdaContext` 初始化所需的各种配置参数，详细配置选项请参考 **[OdaContextConfig 配置文档](oda_context_config.md)**。
*   **`OdaAgentManager`**: 由 `OdaContext` 持有的智能体实例管理器，负责创建和管理 `OdaAgent` 实例，需要 `MemoryService` 等ADK原生服务来创建Runner实例，通过 `OdaMcpManager` 获取MCPToolset实例，依赖 `OdaAgentConfigManager` 获取智能体配置。
*   **`OdaSessionManager`**: 由 `OdaContext` 持有的会话管理器，负责创建和管理 `OdaSession` 实例，依赖 `OdaAgentManager` 获取智能体实例。
*   **`OdaAgentConfigManager`**: 由 `OdaContext` 持有的智能体配置管理器，负责 `OdaAgentConfig` 配置的CRUD操作和管理，依赖 `BaseOdaAgentConfigStorage`、`OdaModelConfigManager`、`OdaMcpManager`。支持内置默认智能体配置的自动加载和保护。
*   **`OdaToolManager`**: 由 `OdaContext` 持有的工具管理器，负责管理内置工具的创建、存储和执行，为智能体提供工具能力支持。
*   **`OdaMcpManager`**: 由 `OdaContext` 持有的MCP配置和工具管理器，负责MCP配置的CRUD操作和MCPToolset的创建管理，为智能体提供外部MCP工具集成能力。
*   **`SessionService` (ADK原生)**: 由 `OdaContext` 持有的会话服务，提供会话数据的存储和管理能力。
*   **`ArtifactService` (ADK原生)**: 由 `OdaContext` 持有的工件服务，提供工件数据的存储和管理能力。
*   **`MemoryService` (ADK原生)**: 由 `OdaContext` 持有的记忆服务，提供长期记忆的存储和检索能力。
*   **`OdaSession`**: 代表一个独立的用户对话会话，由 `OdaSessionManager` 创建和管理。
*   **`OdaAgent`**: OneDragon自定义的智能体封装类，由 `OdaAgentManager` 创建，持有ADK原生的 `Runner` 实例。

## 4. 职责与资源管理

### 4.1 由 `OdaContext` 创建和持有

`OdaContext` 在系统启动时初始化所有全局共享的ADK原生服务和管理器组件。

*   **ADK原生服务**:
    *   **`SessionService`**: 作为会话数据的存储和管理基础设施，提供给 `OdaAgentManager` 和 `OdaSessionManager` 使用。
    *   **`ArtifactService`**: 作为工件数据的存储和管理基础设施，提供给 `OdaAgentManager` 使用。
    *   **`MemoryService`**: 作为长期记忆管理的ADK原生服务，提供给 `OdaAgentManager` 使用。

*   **OneDragon管理器组件**:
    *   **`OdaAgentManager`**: 作为智能体实例的全局管理器，负责创建和管理 `OdaAgent` 实例，需要 `MemoryService` 等ADK原生服务来创建Runner实例，通过 `OdaMcpManager` 获取MCPToolset实例。
    *   **`OdaSessionManager`**: 作为会话实例的全局管理器，提供会话的 CRUD 操作接口，依赖 `OdaAgentManager` 获取智能体实例。
    *   **`OdaAgentConfigManager`**: 作为智能体配置的全局管理器，负责 `OdaAgentConfig` 配置的CRUD操作和管理，依赖 `BaseOdaAgentConfigStorage`、`OdaModelConfigManager`、`OdaMcpManager`。
    *   **`OdaToolManager`**: 作为工具管理的全局管理器，负责内置工具的创建、存储和执行，为智能体提供工具能力支持。

*   **核心功能**:
    *   **系统初始化流程**: 负责系统启动时各服务组件和管理组件的初始化，包括创建 `MemoryService` 实例。
    *   **资源分配流程**: 负责根据系统需求分配和管理各类资源。
    *   **生命周期管理流程**: 负责系统整体的启动、运行和关闭的生命周期管理。
    *   **依赖注入流程**: 负责各组件间的依赖关系管理和注入，为各管理器提供所需的依赖，包括将 `MemoryService`、`ArtifactService`、`OdaToolManager`、`OdaMcpManager`、`OdaAgentConfigManager` 注入到 `OdaAgentManager`，将 `OdaAgentManager` 注入到 `OdaSessionManager`。
    *   **全局配置管理**: 负理系统级别的配置信息和整体生命周期。

### 4.2 核心接口定义

`OdaContext` 提供简洁的核心接口，作为系统的统一入口：

```python
class OdaContext:
    def __init__(self, config: OdaContextConfig):
        """初始化OdaContext，创建所有ADK原生服务和管理器组件"""
    
    def start(self):
        """启动系统，初始化所有服务和管理器"""
    
    def stop(self):
        """停止系统，释放所有资源"""
```

### 4.3 资源获取流程

`OdaContext` 作为应用层的统一资源入口，提供标准化的资源获取接口：

1. **服务获取**: 上层应用通过 `get_*` 方法获取所需的ADK原生服务
2. **管理器获取**: 上层应用通过 `get_*_manager` 方法获取OneDragon管理器组件
3. **配置管理器获取**: 上层应用通过 `get_agent_config_manager()` 方法获取智能体配置管理器
4. **工具获取**: 上层应用通过 `get_tool_manager()` 和 `get_mcp_manager()` 方法获取工具和MCP管理器
5. **生命周期控制**: 通过 `start()` 和 `stop()` 方法控制系统生命周期

### 4.4 资源隔离机制

`OdaContext` 实现清晰的资源隔离策略：

*   **全局资源**: ADK原生服务由 `OdaContext` 统一创建和管理，全局共享
*   **会话资源**: 会话相关的资源由 `OdaSession` 独立管理，会话间完全隔离
*   **智能体资源**: 智能体相关资源由 `OdaAgent` 管理，支持会话级别的隔离
*   **工具资源**: 内置工具由 `OdaToolManager` 统一管理，支持应用级别的隔离
*   **MCP资源**: MCP配置和工具由 `OdaMcpManager` 统一管理，支持应用级别的隔离

## 5. 核心处理流程

### 5.1 系统初始化流程

`OdaContext` 的初始化是整个系统生命周期的起点，采用分阶段创建策略，确保所有组件正确初始化和依赖注入。

#### 5.1.1 初始化阶段划分

**第一阶段：ADK原生服务创建**
- 创建 `SessionService`：提供会话数据存储和管理能力
- 创建 `ArtifactService`：提供工件数据存储和管理能力  
- 创建 `MemoryService`：提供长期记忆存储和检索能力

**第二阶段：持久化相关服务创建**
- 创建 `BaseOdaAgentConfigStorage`：智能体配置的持久化存储服务，提供配置的CRUD操作
- 创建 `BaseOdaMcpStorage`：MCP配置的持久化存储服务，提供MCP配置的CRUD操作

**第三阶段：按依赖顺序创建管理器（包含依赖注入）**
- 创建 `OdaToolManager`：内置工具的全局管理器，无需依赖持久化存储服务，通过代码方式注册工具
- 创建 `OdaMcpManager`：MCP配置和工具的全局管理器，在构造函数中注入 `BaseOdaMcpStorage`
- 创建 `OdaAgentConfigManager`：智能体配置管理器，在构造函数中注入 `BaseOdaAgentConfigStorage`、`OdaModelConfigManager`、`OdaMcpManager`，支持内置默认配置
- 创建 `OdaAgentManager`：智能体实例管理器，在构造函数中注入 `MemoryService`、`ArtifactService`、`OdaToolManager`、`OdaMcpManager`、`OdaAgentConfigManager`
- 创建 `OdaSessionManager`：会话实例的全局管理器，在构造函数中注入 `SessionService`、`OdaAgentManager`

### 5.2 应用层使用流程

应用层通过 `OdaContext` 进行简单的会话管理和消息发送，无需关注底层智能体创建等复杂逻辑。

**核心流程**：
1. **会话管理**：应用层从 `OdaContext` 获取 `OdaSessionManager` 实例，创建和管理会话
2. **消息发送**：应用层向 `OdaSession` 发送消息，指定目标智能体名称，获取处理结果

**设计原则**：
- **简化接口**：应用层只需关注会话获取和消息发送，无需了解智能体创建机制
- **内部自治**：`OdaSession` 内部自主管理智能体实例的创建、缓存和复用
- **透明处理**：智能体创建、工具集成等复杂逻辑对应用层完全透明

详细的会话管理和智能体创建流程请参考 **[核心架构设计文档](../architecture/core_architecture.md)**。
