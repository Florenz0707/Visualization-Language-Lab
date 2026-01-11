# TTS (Text-to-Speech) 模块使用说明

## 概述

本项目使用 **Kokoro-82M** 模型实现高质量的文本转语音功能，为故事模式的每个章节生成中文旁白音频。

## 功能特性

- ✅ 自动检测缺失的音频文件
- ✅ 支持14个章节的中文旁白生成
- ✅ RESTful API接口供前端调用
- ✅ 命令行工具手动生成音频
- ✅ 非阻塞式启动检查
- ✅ 轻量级模型，CPU可运行

## 技术实现

### 使用的模型

- **模型**: Kokoro-82M (8200万参数)
- **库**: kokoro Python library (v0.9.4+)
- **语言支持**: 中文 (Mandarin Chinese)
- **音频格式**: WAV (24kHz采样率)
- **特点**: 开源权重、本地运行、高效快速

### 依赖项

```toml
kokoro>=0.9.4
soundfile>=0.12.1
numpy>=2.4.0
```

## 使用方法

### 0. 配置代理（中国大陆用户必读）

如果你在中国大陆无法直接访问HuggingFace，需要配置代理：

1. 在 `.env` 文件中添加代理配置：
```bash
# Proxy Settings (for accessing HuggingFace in China)
PROXY=http://127.0.0.1:7077
```

2. 确保你的代理服务正在运行（如Clash、V2Ray等）

3. 测试代理配置是否正常：
```bash
uv run scripts/test_proxy.py
```

如果看到 `✓ Successfully connected to HuggingFace via proxy`，说明配置成功！

### 1. 手动生成音频文件

使用提供的脚本批量生成所有章节的音频：

```bash
# 生成缺失的音频文件
uv run scripts/generate_tts_audio.py

# 强制重新生成所有音频文件
uv run scripts/generate_tts_audio.py --force
```

### 2. API接口调用

前端可以通过以下API获取章节音频：

```http
GET /api/story/tts/{chapter_id}
```

**示例**:
```bash
# 获取第1章的音频
curl http://localhost:8000/api/story/tts/1 --output chapter_1.wav
```

**响应**:
- 成功 (200): 返回WAV格式音频文件
- 未找到 (404): 音频文件不存在
- 错误 (500): 服务器内部错误

### 3. 自动检查

服务启动时会自动检查TTS目录：

```bash
uv run uvicorn src.main:app --reload
```

启动日志会显示：
```
INFO: TTS directory ready: /path/to/data/story/tts
INFO: Found X existing TTS audio files
```

## 目录结构

```
backend/
├── data/
│   └── story/
│       ├── outline/
│       │   └── chapters.json      # 章节数据（包含narrative文本）
│       └── tts/
│           ├── 1.wav              # 第1章音频
│           ├── 2.wav              # 第2章音频
│           └── ...                # 其他章节音频
├── src/
│   ├── services/
│   │   └── tts.py                 # TTS服务模块
│   └── api/
│       └── story.py               # Story API（包含TTS端点）
└── scripts/
    └── generate_tts_audio.py      # TTS生成脚本
```

## 测试

运行TTS相关测试：

```bash
# 运行所有story测试（包括TTS）
uv run pytest tests/test_story.py -v

# 只运行TTS测试
uv run pytest tests/test_story.py::test_get_chapter_audio_valid -v
uv run pytest tests/test_story.py::test_get_chapter_audio_invalid -v
```

## 高级配置

### 自定义音频参数

在 `src/services/tts.py` 中可以调整：

- `sample_rate`: 采样率（默认24000Hz，Kokoro原生采样率）
- `voice`: 语音选项（默认'af_heart'）
- `speed`: 语速（默认1.0）

### 可用的语音选项

Kokoro支持多种语音，常用的包括：
- `af_heart`: 女声（默认）
- `am_adam`: 男声
- 其他语音请参考kokoro文档

### 语言支持

修改 `KPipeline(lang_code='z')` 中的语言代码：
- `'z'`: 中文 (Mandarin Chinese)
- `'a'`: 英语 (American English)
- 其他语言代码请参考kokoro文档

## 性能考虑

- **首次生成**: 14个章节约需5-15分钟（CPU）或2-5分钟（GPU）
- **模型大小**: 约200MB（首次运行自动下载）
- **运行环境**: CPU即可运行，无需GPU
- **存储空间**: 每个音频文件约1-3MB，总计约20-40MB
- **内存占用**: 约500MB-1GB

## 故障排除

### 问题1: 模型下载失败（中国大陆常见）

```bash
# 错误信息: Connection timeout / Unable to reach huggingface.co

# 解决方案1: 配置代理
# 在 .env 文件中添加:
PROXY=http://127.0.0.1:7077

# 解决方案2: 使用HuggingFace镜像站
# 设置环境变量:
export HF_ENDPOINT=https://hf-mirror.com

# 解决方案3: 手动下载模型
# 从镜像站下载后放到缓存目录
# ~/.cache/huggingface/hub/
```

### 问题2: 代理配置不生效

```bash
# 检查代理是否正在运行
curl -x http://127.0.0.1:7077 https://www.google.com

# 检查.env文件是否正确加载
# 在代码中添加日志查看环境变量
```

### 问题3: 缺少soundfile依赖

```bash
# 解决方案: 安装soundfile
uv add soundfile
```

### 问题4: 音频文件不存在

```bash
# 解决方案: 运行生成脚本
uv run scripts/generate_tts_audio.py
```

### 问题5: 中文发音不准确

```bash
# 解决方案: 确保使用中文语言代码 'z'
# 在 src/services/tts.py 中检查: KPipeline(lang_code='z')
```

## 参考资料

- [Kokoro-82M GitHub](https://github.com/hexgrad/kokoro)
- [Kokoro Python库文档](https://pypi.org/project/kokoro/)
- [FastAPI文件响应](https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse)

## 更新日志

- **2026-01-11**: 初始实现
  - 添加TTS服务模块
  - 实现API端点
  - 创建生成脚本
  - 完成测试和文档
  - 切换到kokoro库实现
  - 移除torch和transformers依赖
  - 优化为轻量级方案
