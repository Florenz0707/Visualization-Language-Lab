# TTS 架构说明

## 概述

TTS模块采用工厂模式设计，支持多种TTS模型的灵活切换和扩展。

## 目录结构

```
src/services/
├── tts/
│   ├── __init__.py          # 包初始化
│   ├── base.py              # 基础接口
│   ├── factory.py           # TTS工厂
│   ├── config_loader.py     # 配置加载器
│   └── kokoro_provider.py   # Kokoro提供者
├── tts_service.py           # 主服务接口
└── tts_legacy.py            # 旧版本备份

config/
└── tts.yaml                 # TTS配置文件

data/story/tts/
└── {model}/                 # 按模型分类的音频目录
    ├── 1.wav
    ├── 2.wav
    └── ...
```

## 核心组件

### 1. BaseTTSProvider (base.py)
抽象基类，定义TTS提供者接口：
- `initialize()`: 初始化模型
- `generate_audio()`: 生成音频
- `get_model_name()`: 获取模型名称

### 2. TTSFactory (factory.py)
工厂类，负责创建和管理提供者实例：
- `get_provider(model_name)`: 获取提供者
- `register_provider()`: 注册新提供者
- `get_available_models()`: 获取可用模型列表

### 3. TTSConfigLoader (config_loader.py)
配置加载器，读取和管理配置：
- `load()`: 加载配置文件
- `get_model_config()`: 获取模型配置
- `get_output_dir()`: 获取输出目录

## 使用方法

### 1. 生成音频（默认模型）
```bash
uv run scripts/generate_tts_audio.py
```

### 2. 生成音频（指定模型）
```bash
uv run scripts/generate_tts_audio.py --model kokoro
```

### 3. 强制重新生成
```bash
uv run scripts/generate_tts_audio.py --force
```

### 4. API调用（默认模型）
```
GET /api/story/tts/1
```

### 5. API调用（指定模型）
```
GET /api/story/tts/1?model=kokoro
```

## 添加新模型

### 步骤1: 创建提供者类
```python
# src/services/tts/new_provider.py
from .base import BaseTTSProvider

class NewTTSProvider(BaseTTSProvider):
    def initialize(self):
        # 初始化逻辑
        pass

    def generate_audio(self, text, output_path, **kwargs):
        # 生成逻辑
        pass

    def get_model_name(self):
        return "new_model"
```

### 步骤2: 注册提供者
```python
# src/services/tts/factory.py
from .new_provider import NewTTSProvider

class TTSFactory:
    _providers = {
        "kokoro": KokoroTTSProvider,
        "new_model": NewTTSProvider,  # 添加新提供者
    }
```

### 步骤3: 更新配置
```yaml
# config/tts.yaml
models:
  new_model:
    enabled: true
    provider: new_model
    # 模型特定配置...
```

## 测试

所有测试通过 ✅
```bash
uv run pytest tests/test_story.py -v
# 9 passed
```
