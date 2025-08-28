# OdaToolManager

`OdaToolManager` 是 OneDragon-Agent 的工具管理层，由 `OdaContext` 持有，负责系统中所有 ADK 工具实例的管理。作为工具管理的核心组件，它为上层应用提供标准化的工具操作接口，确保工具资源的合理分配和高效使用。

`OdaToolManager` 只支持代码注册方式，所有工具都必须在启动时通过代码直接注册为 build-in 工具。工具的创建和管理基于 ADK-Python 的原生工具类，不提供额外的封装层。

## 构造函数

```python
class OdaToolManager:
    def __init__(self):
        """初始化 OdaToolManager
        
        创建工具注册表和索引结构，以便高效管理工具。
        """
```

## 方法

### register_tool()

```python
async def register_tool(self, tool: BaseTool, app_name: str, tool_id: str) -> None:
    """代码方式注册ADK工具实例
    
    Args:
        tool: 要注册的ADK工具实例
        app_name: 应用名称，用于工具隔离
        tool_id: 工具的唯一标识符，在app_name范围内必须唯一
        
    Raises:
        ValueError: 如果工具标识符冲突或参数无效
        TypeError: 如果tool不是BaseTool实例
    """
```

### register_function()

```python
async def register_function(self, func: Callable, app_name: str, tool_id: str) -> None:
    """注册Python函数并自动包装为FunctionTool
    
    Args:
        func: 要注册的Python函数（支持同步和异步函数）
        app_name: 应用名称，用于工具隔离
        tool_id: 工具的唯一标识符，在app_name范围内必须唯一
        
    Raises:
        ValueError: 如果工具标识符冲突或参数无效
        TypeError: 如果func不可调用
    """
```

### list_tools()

```python
async def list_tools(self, app_name: Optional[str] = None) -> Dict[str, BaseTool]:
    """列出所有ADK工具实例
    
    Args:
        app_name: 可选的应用名称过滤器
        
    Returns:
        工具字典，key为全局标识符 (app_name:tool_id)，value为ADK工具实例
    """
```

### get_tool()

```python
async def get_tool(self, app_name: str, tool_id: str) -> Optional[BaseTool]:
    """根据app_name和tool_id获取ADK工具实例
    
    Args:
        app_name: 应用名称
        tool_id: 工具标识符
        
    Returns:
        Optional[BaseTool]: ADK工具实例，如果不存在则返回None
    """
```

### get_global_identifier()

```python
def get_global_identifier(self, app_name: str, tool_id: str) -> str:
    """生成工具的全局唯一标识符
    
    Args:
        app_name: 应用名称
        tool_id: 工具标识符
        
    Returns:
        全局唯一标识符，格式为 "app_name:tool_id"
    """
```

## 属性

### _app_index

```python
_app_index: Dict[str, Dict[str, BaseTool]]
```
基于 app_name 的工具索引结构

## 使用示例

### 注册 ADK 内置工具

```python
from google.adk.tools import BaseTool, FunctionTool
from one_dragon_agent import OdaContext, OdaContextConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取工具管理器
    tool_manager = context.tool_manager
    
    # 注册 Google 搜索工具
    google_search = FunctionTool(func=lambda query: {"result": f"搜索结果: {query}"})
    await tool_manager.register_tool(
        tool=google_search,
        app_name="my_app",
        tool_id="google_search"
    )
    
    # 注册代码执行工具
    code_exec = FunctionTool(func=lambda code: {"result": f"执行结果: {code}"})
    await tool_manager.register_tool(
        tool=code_exec,
        app_name="my_app",
        tool_id="code_execution"
    )
    
    print("工具注册完成")
    
finally:
    await context.stop()
```

### 注册 Python 函数

```python
import asyncio
from one_dragon_agent import OdaContext, OdaContextConfig

# 定义同步函数
def get_weather(city: str) -> dict:
    """获取指定城市的天气信息"""
    # 实际实现中这里会调用天气API
    return {
        "city": city,
        "temperature": "25°C",
        "condition": "晴朗"
    }

# 定义异步函数
async def fetch_data(url: str) -> dict:
    """异步获取URL数据"""
    # 实际实现中这里会进行HTTP请求
    await asyncio.sleep(1)  # 模拟网络延迟
    return {
        "url": url,
        "status": "success",
        "data": "示例数据"
    }

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取工具管理器
    tool_manager = context.tool_manager
    
    # 注册同步函数
    await tool_manager.register_function(
        func=get_weather,
        app_name="my_app",
        tool_id="get_weather"
    )
    
    # 注册异步函数
    await tool_manager.register_function(
        func=fetch_data,
        app_name="my_app",
        tool_id="fetch_data"
    )
    
    print("函数工具注册完成")
    
finally:
    await context.stop()
```

### 获取工具实例

```python
from one_dragon_agent import OdaContext, OdaContextConfig

# 初始化系统
config = OdaContextConfig()
context = OdaContext(config)
await context.start()

try:
    # 获取工具管理器
    tool_manager = context.tool_manager
    
    # 预先注册工具
    await tool_manager.register_function(
        func=get_weather,
        app_name="my_app",
        tool_id="get_weather"
    )
    
    # 获取工具实例
    weather_tool = await tool_manager.get_tool(
        app_name="my_app",
        tool_id="get_weather"
    )
    
    print(f"获取的工具实例: {weather_tool}")
    
    # 列出所有工具
    tools = await tool_manager.list_tools(app_name="my_app")
    print(f"应用 my_app 的工具列表:")
    for global_id, tool in tools.items():
        print(f"- {global_id}: {tool}")
    
finally:
    await context.stop()
```

## 支持的工具类型

### ADK 内置工具

`OdaToolManager` 支持注册所有 ADK-Python 提供的内置工具：

```python
# FunctionTool 工具
from google.adk.tools import FunctionTool

# 将 Python 函数包装为 FunctionTool
def my_function(param: str) -> dict:
    """自定义函数工具"""
    return {"result": param}

function_tool = FunctionTool(func=my_function)
```

### FunctionTool 工具

支持将 Python 函数自动包装为 FunctionTool：

```python
# 同步函数
def my_function(param: str) -> dict:
    """自定义函数工具"""
    return {"result": param}

# 异步函数
async def async_function(url: str) -> dict:
    """异步函数工具"""
    # 实现异步逻辑
    return {"data": "response"}

# OdaToolManager 会自动将这些函数包装为 ADK FunctionTool
```

## 资源管理职责分离

`OdaToolManager` 专注于工具的注册和工具工厂方法，不负责工具实例的缓存、生命周期管理和清理。工具实例的资源管理由 `OdaSession` 统一负责：

- **工具注册**: `OdaToolManager` 负责工具实例的注册和工厂方法
- **资源管理**: `OdaSession` 负责创建、管理和清理所需工具实例
- **职责清晰**: `OdaToolManager` 专注于工具信息管理，`OdaSession` 负责资源生命周期
- **避免冲突**: 防止多个管理器对同一资源的重复管理
- **一致性**: 确保每个会话的工具资源管理策略的一致性

## 注意事项

- `OdaToolManager` 只支持代码注册方式，所有工具都必须在启动时通过代码直接注册
- 工具的创建和管理基于 ADK-Python 的原生工具类，不提供额外的封装层
- 通过 `app_name` 字段确保不同应用的工具相互隔离，避免命名冲突
- 使用全局唯一标识符 (`app_name:tool_id`) 确保工具在整个应用生态中的唯一性
- 工具实例的资源管理由 `OdaSession` 统一负责，`OdaToolManager` 只负责工具信息管理
- OdaToolManager 由 OdaContext 持有，不应直接实例化
- 所有方法都是异步的，需要使用 await 调用（除了 get_global_identifier）