# LLM Service

大模型服务模块,提供统一的 LLM 调用接口,支持多种模型提供商。

## 目录结构

```
llm/
├── __init__.py           # 模块导出
├── base.py              # LLM 基类定义
├── config_loader.py     # 配置加载器
├── factory.py           # LLM 工厂类
├── dashscope_provider.py # DashScope 适配器
└── README.md            # 本文档
```

## 配置

### 1. 环境变量配置

在 `backend/.env` 文件中添加 API Key:

```bash
# DashScope (Aliyun) API Key
DASHSCOPE_API_KEY=your_api_key_here
```

### 2. 模型配置

在 `backend/config/llm.yaml` 中配置模型参数:

```yaml
# 默认使用的模型
default_model: "qwen-max"

# 模型配置
models:
  qwen-max:
    enabled: true
    provider: "dashscope"
    model_name: "qwen-max"
    temperature: 0.7
    max_tokens: 2000
    top_p: 0.9
```

## 使用示例

### 基本使用

```python
from src.services.llm import LLMFactory

# 创建工厂实例
factory = LLMFactory()

# 获取默认模型
provider = factory.get_provider()

# 发送消息
messages = [
    {"role": "system", "content": "你是一个历史学家"},
    {"role": "user", "content": "介绍一下1812年拿破仑战争"}
]

response = provider.chat(messages)
print(response)
```

### 流式响应

```python
from src.services.llm import LLMFactory

factory = LLMFactory()
provider = factory.get_provider()

messages = [
    {"role": "user", "content": "讲一个故事"}
]

# 启用流式响应
for chunk in provider.chat(messages, stream=True):
    print(chunk, end="", flush=True)
```

### 指定模型

```python
from src.services.llm import LLMFactory

factory = LLMFactory()

# 使用 qwen-plus 模型
provider = factory.get_provider("qwen-plus")

# 使用 deepseek-r1 模型（支持思考模式）
provider = factory.get_provider("deepseek-r1")
```

### 自定义参数

```python
response = provider.chat(
    messages,
    temperature=0.8,
    max_tokens=1000,
    top_p=0.95
)
```

## 架构设计

### 工厂模式

使用工厂模式创建 LLM 提供商实例,支持:
- 统一的接口调用
- 多种模型提供商
- 配置化管理
- 实例缓存

### 基类设计

`BaseLLMProvider` 定义了所有 LLM 提供商必须实现的接口:
- `initialize()`: 初始化服务
- `chat()`: 发送消息并获取响应
- `get_provider_name()`: 获取提供商名称
- `is_available()`: 检查服务是否可用

### 提供商适配器

目前支持的提供商:
- **DashScope**: 阿里云百炼平台,支持通义千问、DeepSeek 等模型

## 扩展新的提供商

1. 创建新的提供商类,继承 `BaseLLMProvider`
2. 实现所有抽象方法
3. 在 `LLMFactory._providers` 中注册
4. 在 `config/llm.yaml` 中添加配置

示例:

```python
from .base import BaseLLMProvider

class NewProvider(BaseLLMProvider):
    def initialize(self) -> bool:
        # 初始化逻辑
        pass

    def chat(self, messages, stream=False, **kwargs):
        # 调用逻辑
        pass

    def get_provider_name(self) -> str:
        return "new_provider"

# 注册到工厂
LLMFactory.register_provider("new_provider", NewProvider)
```

## 注意事项

1. **API Key 安全**: 不要将 API Key 提交到版本控制系统
2. **错误处理**: 所有 API 调用都应该有适当的错误处理
3. **速率限制**: 注意各个提供商的 API 调用限制
4. **成本控制**: 合理设置 `max_tokens` 参数控制成本
