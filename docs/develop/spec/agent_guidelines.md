# 项目开发指南

你需要按照以下描述进行本项目的开发。

## 项目概述
- **Python 3.11 Agent框架**，采用事件驱动、插件化架构
- **包管理器**: `uv`
- **测试**: `pytest` 配合 `pytest-asyncio` 进行异步测试

## 参考命令

### 开发环境设置
```bash
uv sync --group dev # 安装依赖
uv pip install -e . # 安装 one_dragon_agent 包
uv run python ...  # 运行 python 相关命令
uv run --env-file .env python ...  # 使用环境变量文件进行运行
```

### 测试
```bash
uv run --env-file .env pytest tests/ # 运行所有测试
uv run --env-file .env pytest tests/one_dragon_agent/core/agent/ # 运行特定模块
```

### 代码质量
```bash
uv run ruff check src/ tests/     # 代码检查和格式化
uv run ruff format src/ tests/    # 代码格式化
```

## 项目简介

该项目基于 Google Agent Development Kit (ADK) 构建，采用 ADK 原生组件与 OneDragon 自定义封装层的分层架构。核心组件位于 `one_dragon_agent` 包中，通过封装 ADK 原生能力提供业务友好的接口。

### 核心组件

- **`OdaContext`**: 系统的全局资源管理器。作为顶层容器，负责创建和管理所有 ADK 原生服务和管理器组件，提供统一的资源访问接口和依赖注入机制。采用单例模式，确保系统资源的统一管理。

- **`OdaAgentManager`**: 智能体实例的全局管理器。负责创建和管理 `OdaAgent` 实例，通过 ADK 原生 `LlmAgent` 工厂模式实现智能体创建，需要 `SessionService`、`ArtifactService`、`MemoryService`、`OdaToolManager` 和 `OdaMcpManager` 等服务支持。

- **`OdaSessionManager`**: 会话实例的全局管理器。负责会话实例的完整生命周期管理，通过 `SessionService` 提供 ADK 原生会话数据管理能力，支持多会话场景下的资源隔离和状态管理。

- **`OdaSession`**: 会话实例层。代表一个独立的、隔离的用户对话会话，作为 ADK 原生组件的业务包装器。内部持有 `OdaAgent` 池，支持多智能体场景下的无缝切换和协作。

- **`OdaAgent`**: 智能体封装层。OneDragon 自定义的智能体封装类，持有 ADK 原生 `Runner` 实例，提供与 ADK Runner 一致的接口，内置错误重试机制。通过事件流处理实现智能体执行和状态管理。

- **`OdaToolManager`**: 工具管理器。负责内置工具的创建、存储和执行，为智能体提供工具能力支持。

- **`OdaMcpManager`**: MCP 配置和工具管理器。负责 MCP 配置的 CRUD 操作和 MCPToolset 的创建管理，为智能体提供外部 MCP 工具集成能力。

### ADK 原生组件

项目直接使用 ADK 原生组件作为核心执行引擎，通过封装层提供业务接口：

- **`Runner` (ADK原生)**: 智能体执行器，负责协调 `LlmAgent` 的执行流程和异步事件流处理。
- **`LlmAgent` (ADK原生)**: 大语言模型智能体，处理具体的用户请求和大语言模型交互。
- **`SessionService` (ADK原生)**: 会话服务，负责会话数据的存储和管理。
- **`ArtifactService` (ADK原生)**: 工件服务，负责工件数据的存储和管理。
- **`MemoryService` (ADK原生)**: 记忆服务，负责长期记忆的存储和检索。

当你对 ADK 不了解时，使用 context7 查询 adk-python 相关文档了解。

### 执行流程

以下是系统处理一个用户命令的完整流程：

1. **系统初始化**: 应用启动时创建全局唯一的 `OdaContext` 实例，初始化所有 ADK 原生服务和管理器组件。
2. **创建会话请求**: 应用向 `OdaContext` 请求创建新会话。
3. **会话创建**: `OdaContext` 委托 `OdaSessionManager` 通过 `SessionService` 创建 ADK 原生会话，并创建 `OdaSession` 实例作为业务包装器。
4. **获取会话**: 应用获取 `OdaSession` 实例，包含会话 ID 和操作接口。
5. **消息发送**: 应用向 `OdaSession` 发送用户消息，指定目标智能体名称。
6. **智能体获取**: `OdaSession` 从内部 `OdaAgent` 池中获取指定智能体实例，如果不存在则请求 `OdaAgentManager` 创建。
7. **智能体创建**: `OdaAgentManager` 使用持有的服务创建 `OdaAgent` 实例，静态绑定 `LlmAgent` 到 `Runner`，注入所需的服务和工具。
8. **消息处理**: `OdaSession` 调用 `OdaAgent.process_message()` 处理消息，内部调用 `Runner.run_async()` 执行消息。
9. **事件流处理**: `Runner` 迭代 `LlmAgent.run_async()` 返回的异步事件流，处理每个 Event 并调用相应服务提交状态变更。
10. **结果返回**: `OdaAgent` 处理完整的事件流，提取最终响应结果并返回给 `OdaSession`，再返回给应用层。

### 异步流式处理架构

项目基于 ADK 的异步流式处理架构设计，采用 Python 异步生成器模式：

- **事件驱动**: Agent 通过生成器产生 Event 流，Runner 通过迭代处理这些 Event
- **流式处理**: Event 流被顺序迭代处理，支持实时响应和状态更新
- **内存高效**: 生成器模式按需产生 Event，避免一次性加载所有事件到内存
- **错误重试**: `OdaAgent` 在 Event 流处理层面检测异常并自动触发重试机制，用户消息只提交一次，重试时从当前会话状态恢复

有关每个模块的详细说明，请参阅 `docs/develop/modules/` 中的文档。

## 开发规范
- **文件编码**: 编写文件时始终使用 UTF-8 格式，以确保正确的字符编码支持。
- **保持测试同步**: 修改任何模块后，您必须更新 `tests/` 中的测试文件。确保修改后的代码已被覆盖且所有测试都通过。
- **保持文档同步**: 修改任何模块后，您必须更新 `docs/develop/modules/` 中对应的文档文件。确保文档准确反映更改。
- **Git 工作流**: 你的职责是根据用户请求编写和修改代码。不要执行任何 `git` 操作，如 `commit` 或 `push`。用户将处理所有版本控制操作。
- **使用 context7**: 当你写代码时遇到使用库的问题时，请使用 `context7` 搜索库的文档。

## Markdown 指南
- **Mermaid 图表**: 使用标准的流程图/状态图语法，避免循环结构和 "loop" 作为变量名
  - **节点文本引号**: 节点文本必须用双引号 (`"`) 包裹，以避免解析错误。例如，使用 `I["用户界面 (CLI)"]` 而不是 `I[用户界面 (CLI)]`。
- **语言编码**: 使用中文和utf-8编码进行文档编写。
- **文档代码**: 文档中禁止写具体的代码，只需要定义类和核心方法，有详细注释即可。

## Python代码规范
- **异步优先**: 所有操作均使用 async/await
- **docstring/注释**: 所有函数必须具有 Google 风格的文档注释，代码中也需要对必要逻辑加入注释说明。所有的注释都必须使用英文编写。
- **类型提示**: 所有类成员变量和函数签名必须包含类型提示(Type Hinting)。
- **内置泛型**: 使用内置泛型类型（`list`, `dict`）而不是从 `typing` 模块导入（`List`, `Dict`）。
  - **正确**: `my_list: list[str] = []`
  - **错误**: 
    ```python
    from typing import List
    my_list: List[str] = []
    ```
- **导入**: 在 `one_dragon_agent` 包内编写源码导入包时，需要遵循以下规范：
  - **使用绝对路径导入**: 禁止使用相对路径导入。
  - **类型注解导入**: 仅用于类型注解的导入应使用`TYPE_CHECKING`。
- **显式父类构造函数调用**:
    - **规则**: 在所有子类的 `__init__` 方法中，您**必须**直接调用父类构造函数（例如，`ParentClass.__init__(self, ...)`）。您**不得**使用 `super().__init__()`。
    - **原因**: 这是项目特定的强制性编码标准，以确保代码清晰度和明确性。
    - **示例**:
      ```python
      # 正确:
      class MySubclass(MyBaseClass):
          def __init__(self, name, value):
              # 直接调用父类的 __init__
              MyBaseClass.__init__(self, name)
              self.value = value
      ```
      ```python
      # 错误:
      class MySubclass(MyBaseClass):
          def __init__(self, name, value):
              # 初始化时不要使用 super()
              super().__init__(name)
              self.value = value
      ```
- **显式数据结构**: 你应该定义一个对象，而不是使用 dict。你必须适应类定义字段，不能使用 `getattr` 和 `setattr`。
- **不暴露任何模块**: 没有收到指示的情况下，不要在 `__init__.py` 中新增暴露任何模块。
- **编码规范**
  - **编码声明**: 所有 Python 文件必须在文件开头添加 UTF-8 编码声明：
    ```python
    # -*- coding: utf-8 -*-
    ```
  - **字符串处理**: 禁止在代码中直接使用 Unicode 字符（如表情符号、特殊符号等），特别是在 `print()` 语句和字符串字面量中。如需显示特殊字符，应使用转义序列或配置合适的终端/环境设置。
  - **输出格式化**: 在日志输出和打印语句中，禁止使用 Unicode 表情符号、特殊字符或非 ASCII 字符。使用简单的 ASCII 字符或转义序列。
- **日志模块**: 统一使用 `one_dragon_agent.core.system.log` 中的 `get_logger()` 获取日志对象。

## 测试代码规范

当你编写测试代码时，必须遵守以下规范：

- **无测试包**: 不得在测试目录中创建 python package。
- **测试类和Fixtures**: 测试文件必须使用测试类（以 `Test` 为前缀）来组织相关的测试方法。您必须使用 `pytest.fixture` 来管理测试依赖和状态（例如对象实例的创建和拆卸），以提高代码的可重用性和可维护性。
- **导入约定**: 由于项目使用 `src-layout`，测试文件中的导入路径不得包含 `src` 目录。
  - **正确**: `from one_dragon_agent.core.agent import Agent`
  - **错误**: `from src.one_dragon_agent.core.agent import Agent`
- **单方法测试文件**: 每个 Python 测试文件应专门针对单个方法在各种场景下进行测试。
  - **示例**: 要测试 `src/one_dragon_agent/core/agent/agent.py`，请创建一个文件夹 `tests/one_dragon_agent/core/agent/agent/` 来存储所有测试文件。
  - **示例**: 要测试 `agent.py` 的 `execute_main_loop` 方法，请在 `agent` 文件夹中创建一个名为 `test_execute_main_loop.py` 的文件。该文件应包含专门针对 `execute_main_loop` 方法的所有测试用例。
- **异步测试装饰器**: 所有异步测试方法必须同时包含 `@pytest.mark.asyncio` 和 `@pytest.mark.timeout` 装饰器。
- **临时文件**: 使用当前工作目录下的 `.temp` 目录来存储临时文件。
- **保证逻辑正确**: 除非源代码逻辑有错误，否则不能因为测试不通过而修改源代码。
- **诚实原则**: 当测试用例失败且您不知道原因或如何修复时，应停下来询问下一步该怎么做。
