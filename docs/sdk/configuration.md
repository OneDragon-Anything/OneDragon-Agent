# 配置管理

本章将详细介绍 OneDragon-Agent SDK 的配置管理功能，包括系统配置、智能体配置、模型配置和 MCP 配置等。

## 系统配置

系统配置通过 `OdaContextConfig` 类和环境变量进行管理，控制 SDK 的基本行为。

### OdaContextConfig

`OdaContextConfig` 是系统的主要配置类，用于初始化 `OdaContext`。

```python
from one_dragon_agent import OdaContextConfig

# 创建默认配置
config = OdaContextConfig()

# 使用配置初始化 OdaContext
context = OdaContext(config)
```

### 环境变量配置

OneDragon-Agent 支持通过环境变量进行系统级配置：

| 环境变量名称 | 描述 | 默认值 |
|-------------|------|--------|
| ODA_STORAGE | 持久化方式 (memory, mysql) | memory |
| ODA_DEFAULT_LLM_BASE_URL | 默认的 LLM 服务地址 | 无 |
| ODA_DEFAULT_LLM_API_KEY | 默认的 LLM 服务 API KEY | 无 |
| ODA_DEFAULT_LLM_MODEL | 默认的 LLM 服务模型 | 无 |

#### 配置示例

在 Linux/macOS 系统中：

```bash
export ODA_STORAGE=mysql
export ODA_DEFAULT_LLM_BASE_URL="https://api.example.com"
export ODA_DEFAULT_LLM_API_KEY="your-api-key"
export ODA_DEFAULT_LLM_MODEL="gemini-2.0-flash"
```

在 Windows 系统中：

```cmd
set ODA_STORAGE=mysql
set ODA_DEFAULT_LLM_BASE_URL="https://api.example.com"
set ODA_DEFAULT_LLM_API_KEY="your-api-key"
set ODA_DEFAULT_LLM_MODEL="gemini-2.0-flash"
```

#### 默认 LLM 配置

当设置了 `ODA_DEFAULT_LLM_BASE_URL`、`ODA_DEFAULT_LLM_API_KEY` 和 `ODA_DEFAULT_LLM_MODEL` 三个环境变量时，系统会自动创建一个默认的 LLM 配置，使用固定的 ID `__default_llm_config`。这个配置可以被应用程序直接使用，无需额外的配置管理操作。

## 模型配置管理

模型配置管理通过 `OdaModelConfigManager` 类实现，负责管理大模型服务的配置。

### OdaModelConfig 配置项

`OdaModelConfig` 是大模型配置的数据类，包含以下可配置项：

| 配置项 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `app_name` | `str` | 是 | 用于标识所属的应用程序 | `"weather_app"` |
| `model_id` | `str` | 是 | 大模型唯一标识符 | `"gemini-2.0-flash-config"` |
| `base_url` | `str` | 是 | 大模型 API 基础 URL | `"https://api.example.com"` |
| `api_key` | `str` | 是 | 访问大模型 API 的密钥 | `"sk-..."` |
| `model` | `str` | 是 | 实际使用的模型名称 | `"gemini-2.0-flash"` |

### 创建模型配置

```python
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig

# 创建模型配置
model_config = OdaModelConfig(
    app_name="my_app",
    model_id="gemini-config",
    base_url="https://api.example.com",
    api_key="your-api-key",
    model="gemini-2.0-flash"
)

# 获取模型配置管理器
model_config_manager = context.get_model_config_manager()

# 创建配置
await model_config_manager.create_config(model_config)
```

### 获取模型配置

```python
# 获取指定模型配置
model_config = await model_config_manager.get_config("gemini-config")

if model_config:
    print(f"模型配置: {model_config}")
else:
    print("模型配置不存在")
```

### 获取默认模型配置

```python
# 获取默认模型配置（基于环境变量自动创建）
default_config = model_config_manager.get_default_config()

if default_config:
    print(f"默认模型配置: {default_config}")
else:
    print("默认模型配置未设置")
```

### 列出所有模型配置

```python
# 列出所有模型配置
configs = await model_config_manager.list_configs()

print(f"共有 {len(configs)} 个模型配置:")
for config in configs:
    print(f"- {config.model_id}: {config.model}")
```

### 更新模型配置

```python
# 获取现有配置
config = await model_config_manager.get_config("gemini-config")

# 更新配置
config.model = "gemini-2.0-pro"
config.api_key = "new-api-key"

# 保存更新
await model_config_manager.update_config(config)
```

### 删除模型配置

```python
# 删除模型配置
await model_config_manager.delete_config("gemini-config")

print("模型配置已删除")
```

## 智能体配置管理

智能体配置管理通过 `OdaAgentConfigManager` 类实现，负责管理智能体的配置。

### OdaAgentConfig 配置项

`OdaAgentConfig` 是智能体配置的数据类，包含以下可配置项：

| 配置项 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `app_name` | `str` | 是 | 用于标识所属的应用程序 | `"weather_app"` |
| `agent_name` | `str` | 是 | 智能体名称，同时作为唯一标识 | `"weather_agent"` |
| `agent_type` | `str` | 是 | ADK 中的智能体类型 | `"llm_agent"` |
| `description` | `str` | 是 | 智能体功能描述 | `"天气查询智能体"` |
| `instruction` | `str` | 是 | 智能体的系统提示词 | `"你是一个天气查询助手，帮助用户获取天气信息"` |
| `model_config` | `str` | 是 | 使用的大模型 ID | `"gemini-2.0-flash"` |
| `tool_list` | `list[str]` | 否 | 可使用工具的 ID 列表 | `["get_weather", "get_temperature"]` |
| `mcp_list` | `list[str]` | 否 | 可使用 MCP 的 ID 列表 | `["filesystem_mcp", "notion_mcp"]` |
| `sub_agent_list` | `list[str]` | 否 | 可使用子智能体的名称/ID 列表 | `["payment_agent"]` |

### 创建智能体配置

```python
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig

# 创建智能体配置
agent_config = OdaAgentConfig(
    app_name="my_app",
    agent_name="weather_agent",
    agent_type="llm_agent",
    description="天气查询智能体",
    instruction="你是一个天气查询助手，帮助用户获取天气信息",
    model_config="gemini-config",  # 引用上面创建的模型配置
    tool_list=["get_weather", "get_temperature"]
)

# 获取智能体配置管理器
agent_config_manager = context.get_agent_config_manager()

# 创建配置
await agent_config_manager.create_config(agent_config)
```

### 获取智能体配置

```python
# 获取指定智能体配置
agent_config = await agent_config_manager.get_config("weather_agent")

if agent_config:
    print(f"智能体配置: {agent_config}")
else:
    print("智能体配置不存在")
```

### 列出所有智能体配置

```python
# 列出所有智能体配置
configs = await agent_config_manager.list_configs()

print(f"共有 {len(configs)} 个智能体配置:")
for config in configs:
    print(f"- {config.agent_name}: {config.description}")
```

### 更新智能体配置

```python
# 获取现有配置
config = await agent_config_manager.get_config("weather_agent")

# 更新配置
config.instruction = "你是一个专业的天气查询助手，提供准确的天气信息和穿衣建议"
config.tool_list.append("get_weather_forecast")

# 保存更新
await agent_config_manager.update_config(config)
```

### 删除智能体配置

```python
# 删除智能体配置
await agent_config_manager.delete_config("weather_agent")

print("智能体配置已删除")
```

### 默认智能体配置

系统内置了一个名为 "default" 的默认智能体配置，该配置自动加载且不可修改，为系统提供开箱即用的基础智能体功能。

```python
# 获取默认智能体配置（会自动创建）
default_config = await agent_config_manager.get_config("default")

if default_config:
    print(f"默认智能体配置: {default_config}")
else:
    print("默认智能体配置不可用")
```

## MCP 配置管理

MCP (Model Context Protocol) 配置管理通过 `OdaMcpManager` 类实现，负责管理 MCP 服务器的配置。

### OdaMcpConfig 配置项

`OdaMcpConfig` 是 MCP 配置的数据类，包含以下可配置项：

| 配置项 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `mcp_id` | `str` | 是 | MCP 配置的唯一标识符 | `"filesystem_mcp"` |
| `app_name` | `str` | 是 | 应用名称，用于隔离不同应用的 MCP 配置 | `"weather_app"` |
| `name` | `str` | 是 | MCP 配置的显示名称 | `"文件系统 MCP"` |
| `description` | `str` | 是 | MCP 配置的描述信息 | `"提供文件系统操作能力"` |
| `server_type` | `str` | 是 | 服务器类型：`'stdio'`、`'sse'` 或 `'http'` | `"stdio"` |
| `command` | `str` | 否 | 启动 MCP 服务器的命令（stdio 类型） | `"npx"` |
| `args` | `list[str]` | 否 | 启动 MCP 服务器的参数（stdio 类型） | `["-y", "@modelcontextprotocol/server-filesystem"]` |
| `url` | `str` | 否 | MCP 服务器的 URL（sse 或 http 类型） | `"http://localhost:8090/sse"` |
| `headers` | `dict[str, str]` | 否 | HTTP 请求头（sse 或 http 类型） | `{"Authorization": "Bearer token"}` |
| `env` | `dict[str, str]` | 否 | 环境变量 | `{"API_KEY": "secret"}` |
| `tool_filter` | `list[str]` | 否 | 工具过滤器，只加载指定的工具 | `["read_file", "list_directory"]` |
| `timeout` | `int` | 否 | 连接超时时间（秒） | `30` |
| `retry_count` | `int` | 否 | 重试次数 | `3` |

### 创建 MCP 配置

#### Stdio 类型 MCP 配置

```python
from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig

# 创建 Stdio 类型的 MCP 配置
mcp_config = OdaMcpConfig(
    mcp_id="filesystem_stdio",
    app_name="my_app",
    name="文件系统 MCP (Stdio)",
    description="通过 stdio 连接的文件系统 MCP 服务器",
    server_type="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"],
    tool_filter=["read_file", "list_directory"]
)

# 获取 MCP 管理器
mcp_manager = context.get_mcp_manager()

# 注册 MCP 配置
await mcp_manager.register_custom_config(mcp_config)
```

#### SSE 类型 MCP 配置

```python
# 创建 SSE 类型的 MCP 配置
mcp_config = OdaMcpConfig(
    mcp_id="web_api_sse",
    app_name="my_app",
    name="Web API MCP (SSE)",
    description="通过 SSE 连接的 Web API MCP 服务器",
    server_type="sse",
    url="http://localhost:8090/sse",
    headers={"Authorization": "Bearer your-token"},
    tool_filter=["fetch_data", "submit_form"]
)

# 注册 MCP 配置
await mcp_manager.register_custom_config(mcp_config)
```

#### HTTP 类型 MCP 配置

```python
# 创建 HTTP 类型的 MCP 配置
mcp_config = OdaMcpConfig(
    mcp_id="web_api_http",
    app_name="my_app",
    name="Web API MCP (HTTP)",
    description="通过 HTTP 连接的 Web API MCP 服务器",
    server_type="http",
    url="http://localhost:8080/mcp",
    headers={"Authorization": "Bearer your-token", "Content-Type": "application/json"},
    tool_filter=["get_data", "post_data", "delete_resource"]
)

# 注册 MCP 配置
await mcp_manager.register_custom_config(mcp_config)
```

### 获取 MCP 配置

```python
# 获取指定 MCP 配置
mcp_config = await mcp_manager.get_mcp_config(
    app_name="my_app",
    tool_id="filesystem_stdio"
)

if mcp_config:
    print(f"MCP 配置: {mcp_config}")
else:
    print("MCP 配置不存在")
```

### 列出所有 MCP 配置

```python
# 列出所有 MCP 配置
mcp_configs = await mcp_manager.list_mcp_configs(app_name="my_app")

print(f"应用 my_app 有 {len(mcp_configs)} 个 MCP 配置:")
for mcp_id, config in mcp_configs.items():
    print(f"- {mcp_id}: {config.name}")
```

### 更新 MCP 配置

```python
# 更新 MCP 配置
await mcp_manager.update_custom_config(
    app_name="my_app",
    tool_id="filesystem_stdio",
    config=updated_config
)

print("MCP 配置已更新")
```

### 删除 MCP 配置

```python
# 删除 MCP 配置
await mcp_manager.unregister_custom_config(
    app_name="my_app",
    tool_id="filesystem_stdio"
)

print("MCP 配置已删除")
```

## 配置验证

OneDragon-Agent SDK 提供了配置验证功能，确保配置的正确性和完整性。

### 模型配置验证

```python
# 验证模型配置是否有效
is_valid = await model_config_manager.validate_model_config(
    app_name="my_app",
    model_config="gemini-config"
)

if is_valid:
    print("模型配置有效")
else:
    print("模型配置无效")
```

### 智能体配置验证

智能体配置在创建和更新时会自动验证以下内容：

- 模型配置是否存在
- MCP 配置是否存在且启用
- 工具配置是否存在

```python
try:
    await agent_config_manager.create_config(agent_config)
    print("智能体配置创建成功")
except ValueError as e:
    print(f"智能体配置验证失败: {e}")
```

### MCP 配置验证

MCP 配置在创建和更新时会自动验证以下内容：

- 服务器类型是否有效
- 参数完整性（stdio 类型需要 command，sse/http 类型需要 url）
- 配置格式是否正确

```python
try:
    await mcp_manager.register_custom_config(mcp_config)
    print("MCP 配置注册成功")
except ValueError as e:
    print(f"MCP 配置验证失败: {e}")
```

## 配置示例

以下是一个完整的配置示例，展示了如何配置模型、智能体和 MCP：

```python
import asyncio
from one_dragon_agent import OdaContext, OdaContextConfig
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig
from one_dragon_agent.core.agent.config.oda_agent_config import OdaAgentConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig

async def setup_configuration():
    # 初始化系统
    config = OdaContextConfig()
    context = OdaContext(config)
    await context.start()
    
    try:
        # 获取各种管理器
        model_config_manager = context.get_model_config_manager()
        agent_config_manager = context.get_agent_config_manager()
        mcp_manager = context.get_mcp_manager()
        
        # 1. 创建模型配置
        gemini_config = OdaModelConfig(
            app_name="my_app",
            model_id="gemini-config",
            base_url="https://api.example.com",
            api_key="your-api-key",
            model="gemini-2.0-flash"
        )
        await model_config_manager.create_config(gemini_config)
        
        # 2. 创建 MCP 配置
        filesystem_mcp = OdaMcpConfig(
            mcp_id="filesystem_stdio",
            app_name="my_app",
            name="文件系统 MCP",
            description="提供文件系统操作能力",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"],
            tool_filter=["read_file", "write_file", "list_directory"]
        )
        await mcp_manager.register_custom_config(filesystem_mcp)
        
        # 3. 创建智能体配置
        file_agent_config = OdaAgentConfig(
            app_name="my_app",
            agent_name="file_agent",
            agent_type="llm_agent",
            description="文件操作智能体",
            instruction="你是一个文件操作助手，可以帮助用户读取、写入和管理文件",
            model_config="gemini-config",
            mcp_list=["filesystem_stdio"]
        )
        await agent_config_manager.create_config(file_agent_config)
        
        print("配置设置完成")
        
    finally:
        await context.stop()

if __name__ == "__main__":
    asyncio.run(setup_configuration())
```

## 配置最佳实践

### 1. 使用环境变量管理敏感信息

对于 API 密钥等敏感信息，建议使用环境变量而不是硬编码在配置中：

```python
import os

# 从环境变量获取 API 密钥
api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise ValueError("LLM_API_KEY 环境变量未设置")

model_config = OdaModelConfig(
    app_name="my_app",
    model_id="gemini-config",
    base_url="https://api.example.com",
    api_key=api_key,
    model="gemini-2.0-flash"
)
```

### 2. 使用配置文件

对于复杂的配置，建议使用配置文件（如 JSON、YAML）而不是硬编码：

```python
import json
from pathlib import Path

def load_config_from_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# 加载配置文件
config_data = load_config_from_file("config.json")

# 创建模型配置
model_config = OdaModelConfig(
    app_name=config_data["app_name"],
    model_id=config_data["model"]["id"],
    base_url=config_data["model"]["base_url"],
    api_key=config_data["model"]["api_key"],
    model=config_data["model"]["name"]
)
```

### 3. 配置验证

在应用启动时验证所有配置，避免运行时错误：

```python
async def validate_all_configurations(context):
    # 验证模型配置
    model_config_manager = context.get_model_config_manager()
    model_configs = await model_config_manager.list_configs()
    
    for config in model_configs:
        is_valid = await model_config_manager.validate_model_config(
            app_name=config.app_name,
            model_config=config.model_id
        )
        if not is_valid:
            raise ValueError(f"模型配置 {config.model_id} 无效")
    
    # 验证智能体配置
    agent_config_manager = context.get_agent_config_manager()
    agent_configs = await agent_config_manager.list_configs()
    
    for config in agent_configs:
        # 智能体配置在获取时会自动验证
        await agent_config_manager.get_config(config.agent_name)
    
    print("所有配置验证通过")
```

### 4. 配置版本管理

对于生产环境，建议使用配置版本管理，确保配置变更的可追溯性：

```python
# 在配置中添加版本信息
model_config = OdaModelConfig(
    app_name="my_app",
    model_id="gemini-config-v1.0",
    base_url="https://api.example.com",
    api_key="your-api-key",
    model="gemini-2.0-flash"
)
```

---

*通过掌握这些配置管理功能，您可以灵活地配置和管理 OneDragon-Agent SDK 的各种组件，构建功能强大的智能体应用。*