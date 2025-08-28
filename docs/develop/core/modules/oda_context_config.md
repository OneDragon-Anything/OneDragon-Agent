# OneDragon-Agent 配置

OneDragon-Agent 启动所需的配置 OdaContextConfig，均从环境变量中读取，以下是可用的环境变量

|环境变量名称|描述|默认值|
|---|---|---|
|ODA_STORAGE|持久化方式 memory, mysql|memory|
|ODA_DEFAULT_LLM_BASE_URL|默认的LLM服务地址|无|
|ODA_DEFAULT_LLM_API_KEY|默认的LLM服务API KEY|无|
|ODA_DEFAULT_LLM_MODEL|默认的LLM服务模型|无|

## 默认LLM配置

系统支持通过环境变量配置默认的LLM服务，当设置了以下三个环境变量时，系统会自动创建一个默认的LLM配置：

- `ODA_DEFAULT_LLM_BASE_URL`: 默认LLM服务的基础URL
- `ODA_DEFAULT_LLM_API_KEY`: 访问默认LLM服务的API密钥
- `ODA_DEFAULT_LLM_MODEL`: 默认使用的LLM模型名称

默认配置将使用固定的ID `__default_llm_config`，并在OdaModelConfigManager初始化时自动创建。这个配置可以被应用程序直接使用，无需额外的配置管理操作。
