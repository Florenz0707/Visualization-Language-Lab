# 1812 年拿破仑东征 — 后端（数据工程 + API）

简要说明：本仓库包含用于历史地理数据处理与后端 API 的脚本与最小服务实现，负责将处理后的 GeoJSON / DEM 等数据对外提供给前端可视化使用。

主要目录结构：

- `data/`：所有输入与处理后的地理数据（GeoJSON、DEM、历史地图等）。
  - `geojson/`：准备好的 GeoJSON（`events.geojson`、`movements.geojson`、`territories.geojson`、`contours.geojson` 等）。
  - `dem/`：原始与处理后的 DEM 栅格数据。
  - `boundaries/`：原始 shapefile 边界数据（可通过脚本转换为 GeoJSON）。

- `scripts/`：数据下载、处理和生成脚本。
  - `validate_data.py`：数据完整性检查脚本（会提示缺失文件对应的生成脚本）。
  - `generate_movements_geojson.py`：从事件点合成 `movements.geojson`。
  - `generate_terrirories_geojson.py`：按缓冲与溶解生成 `territories.geojson`。
  - `process_dem.py`：DEM 处理（裁剪、重采样、生成 hillshade/contours）。
  - 其它下载/转换脚本见 `scripts/`。

- `src/`：FastAPI 服务代码（最小实现）。
  - `src/main.py`：FastAPI 应用入口。
  - `src/api/`：各 API 路由（`events`, `movements`, `territories`）。
  - `src/services/`：数据加载与缓存工具。
    - `src/services/llm/`：大语言模型（LLM）服务模块。
    - `src/services/tts/`：文本转语音（TTS）服务模块。

- `doc/`：文档（包含 `doc/interface.md` 的基础接口说明）。

主要功能

- 数据验证与生成：使用 `scripts/` 下脚本校验并生成缺失的 GeoJSON（如 `movements.geojson`、`territories.geojson`、`contours.geojson`）。
- 后端 API：提供最小的 REST 接口以返回静态 GeoJSON（目前实现：`/api/events`、`/api/movements`、`/api/territories`）。
- LLM 服务：集成大语言模型服务，支持 DashScope（通义千问）和 DeepSeek 等多种模型提供商。
- TTS 服务：文本转语音服务，支持 Kokoro-82M 模型自动生成章节旁白音频。

快速开始（开发环境）

1. 创建并激活虚拟环境，安装依赖（推荐使用 `pyproject.toml`）：

```bash
uv sync
```

2. 验证数据完整性：

```bash
uv run ./scripts/validate_data.py
```

3. 如缺少某些生成文件，可运行对应脚本：

```bash
uv run python scripts/generate_movements_geojson.py
uv run python scripts/generate_terrirories_geojson.py
uv run python scripts/process_dem.py
```

4. 启动开发服务器（FastAPI + Uvicorn）：

方式 A — 直接使用 `uvicorn`：

```bash
uv run uvicorn src.main:app --reload --port 8000
```

方式 B — 使用仓库内的 `run_server.py`（推荐）：

`run_server.py` 会读取环境变量 `HOST`/`PORT`/`RELOAD` 并以相同参数启动 Uvicorn：

```bash
# 使用默认（127.0.0.1:8000）
uv run python run_server.py

# 在不同主机/端口运行并启用自动重载
HOST=0.0.0.0 PORT=8080 RELOAD=1 uv run python run_server.py
```

5. 常用接口（基础）：

- `GET /api/events` — 返回 `events.geojson`（支持 `start`/`end` 查询参数）。
- `GET /api/movements` — 返回 `movements.geojson`。
- `GET /api/territories` — 返回 `territories.geojson`。

投影支持：
- 所有接口支持可选查询参数 `projection`，允许返回不同坐标参考系：
  - `wgs84`（默认，EPSG:4326）
  - `webmercator`（EPSG:3857）
  - `lambert`（EPSG:3034）

示例：
```bash
# 请求 Web Mercator 投影的事件数据
curl 'http://127.0.0.1:8000/api/events?projection=webmercator'

# 请求 Lambert 投影的领土 GeoJSON
curl 'http://127.0.0.1:8000/api/territories?projection=lambert'
```

## LLM 服务配置

本项目集成了大语言模型（LLM）服务，支持多种模型提供商。

### 环境变量配置

在 `.env` 文件中添加 API Keys：

```bash
# DashScope (阿里云百炼) API Key
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 支持的模型

**DashScope (阿里云百炼):**
- `qwen-max`: 通义千问 Max 模型
- `qwen-plus`: 通义千问 Plus 模型
- `deepseek-r1`: DeepSeek R1 模型（支持思考模式）

**DeepSeek (直连):**
- `deepseek-chat`: DeepSeek Chat 模型（默认）

### 使用示例

```python
from src.services.llm import LLMFactory

# 创建工厂实例
factory = LLMFactory()

# 获取默认模型
provider = factory.get_provider()

# 发送消息
messages = [
    {"role": "user", "content": "介绍1812年拿破仑战争"}
]

# 非流式响应
response = provider.chat(messages)
print(response)

# 流式响应
for chunk in provider.chat(messages, stream=True):
    print(chunk, end="", flush=True)
```

### 测试 LLM 服务

运行测试脚本验证配置：

```bash
# 测试环境变量加载
uv run python test_llm_env.py

# 测试 DeepSeek 适配器
uv run python test_deepseek.py

# 运行完整示例
uv run python examples/llm_example.py
```

### 详细文档

- **LLM 服务文档**: `src/services/llm/README.md`
- **API 接口文档**: `doc/interface.md`
- **配置文件**: `config/llm.yaml`
