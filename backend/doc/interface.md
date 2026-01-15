# API 接口说明

## 基础数据接口

### GET /api/events
返回 `events.geojson` 的 FeatureCollection。

**Query 参数：**
- `start` (YYYY-MM-DD，可选) — 起始日期过滤
- `end` (YYYY-MM-DD，可选) — 结束日期过滤
- `bbox` (可选) — 空间范围过滤，格式：`minx,miny,maxx,maxy`（逗号分隔的浮点数）
- `projection` (可选, 默认 `wgs84`) — 支持值：`wgs84`（EPSG:4326）、`webmercator`（EPSG:3857）、`lambert`（EPSG:3034）

**性能优化：** 使用时间索引（B-tree）和空间索引（R-tree）加速查询

**示例：** `/api/events?start=1812-09-01&end=1812-10-01&bbox=20,50,40,60`

---

### GET /api/movements
返回 `movements.geojson` 的 FeatureCollection（军队行军轨迹）。

**Query 参数：**
- `projection` (可选, 默认 `wgs84`) — 支持 `wgs84`,`webmercator`,`lambert`
- `bbox` (可选) — 空间范围过滤，格式：`minx,miny,maxx,maxy`（逗号分隔的浮点数）
- `simplify` (bool, 默认 `false`) — 是否对路径应用简化
- `tolerance` (float, 默认 `0.01`) — 简化容差（坐标单位）
- `lod` (int, 可选, 1-7) — LOD等级：1=最高细节，7=聚合点
- `zoom` (int, 可选, 0-12) — 地图缩放级别，自动选择合适的LOD
- `group` (bool, 默认 `false`) — 是否按 `unit` 字段分组并在响应中返回 `groups`
- `bundling` (bool, 默认 `false`) — 是否在响应中包含 `bundling` 预计算数据

**LOD系统：**
- LOD 1-2: 高细节（zoom > 7）
- LOD 3-4: 中等细节（zoom 5-7）
- LOD 5-6: 低细节（zoom 3-5）
- LOD 7: 聚合为点（zoom < 3）

**性能优化：** 使用空间索引（R-tree）加速 bbox 查询

**示例：** `/api/movements?zoom=18&bbox=20,50,40,60`

---

### GET /api/territories
返回 `territories.geojson` 的 FeatureCollection（按事件缓冲合并的控制区）。

**Query 参数：**
- `projection` (可选, 默认 `wgs84`) — 支持值：`wgs84`（EPSG:4326）、`webmercator`（EPSG:3857）、`lambert`（EPSG:3034）

**示例：** `/api/territories?projection=lambert`

---

### GET /api/flows
返回简化的 flow 对（每条行军轨迹的起止点），用于前端流向图（flow map）渲染。

**Query 参数：**
- `simplify` (bool, 默认 true) — 是否对路径应用 Douglas–Peucker 简化
- `threshold` (float, 默认 0.01) — 简化容差（仅在 `simplify=true` 时生效）

**响应：** GeoJSON FeatureCollection，每个 Feature 为一条 LineString（仅包含起点与终点坐标）及若干 properties (`unit`, `events_count`, `start_date`, `end_date`)。

**兼容模式：** 当环境变量 `LIGHTWEIGHT_MODE=1` 时，端点返回空的 FeatureCollection（用于测试/CI 以避免加载大文件）。

**示例：** `/api/flows?simplify=true&threshold=0.05`

---

## 统计接口

### GET /api/statistics/troops
返回时间序列兵力统计（按 period 聚合）。

**Query 参数：**
- `start` (YYYY-MM-DD, 必需)
- `end` (YYYY-MM-DD, 必需)
- `faction` (可选, `french` 或 `russian`)
- `period` (可选, 默认 `month`, 支持 `month`, `week`, `day`)

**响应示例：**
```json
{
  "french": [{"date": "1812-06-01T00:00:00Z", "count": 420000}, ...],
  "russian": [{"date": "1812-06-01T00:00:00Z", "count": 300000}, ...]
}
```

**示例：** `/api/statistics/troops?start=1812-06-01&end=1812-12-31&period=month`

---

## Story Mode 接口

### GET /api/story/outline
返回 Story Mode 的章节大纲数据。

**Query 参数：**
- `chapter_id` (int, 可选) — 指定章节 ID，返回单个章节；不指定则返回所有章节

**响应：** JSON 对象，包含标题、描述和章节列表。每个章节包含：
- `id`: 章节标识符
- `title`: 章节标题
- `date`: 历史日期 (YYYY-MM-DD)
- `event_ids`: 关联的事件 ID 列表
- `camera`: 镜头参数对象 (`center` 坐标, `zoom`, `pitch`, `bearing`)
- `narrative`: 历史背景文本（200-300字）
- `image`: 配图信息对象 (`url`, `attribution`)

**示例：** `/api/story/outline` 或 `/api/story/outline?chapter_id=1`

---

### GET /api/story/tts/{chapter_id}
返回指定章节的TTS音频文件。

**路径参数：**
- `chapter_id` (int, 必需) — 章节ID

**响应：** WAV格式音频文件（`audio/wav`）

**说明：**
- 服务启动时会自动检测 `data/story/tts/` 目录下的音频文件
- 如果音频文件不存在，会使用 Kokoro-82M 模型自动生成
- 音频内容为对应章节的 `narrative` 字段文本
- 音频文件命名格式：`{chapter_id}.wav`

**示例：** `/api/story/tts/1` 返回第1章的音频文件

---

## 温度数据接口

### GET /api/temperature/1812
返回 1812 年指定日期的绝对温度（线性插值）。

**Query 参数：**
- `date_str` (必需, YYYY-MM-DD) — 查询的历史日期，必须位于 1812 年内
- `scope` (可选, 默认 `bbox`) — `global` 或 `bbox`；当使用 `bbox` 时会在数据集上按区域加权平均
- `bbox` (可选) — 覆盖区域的边界，格式：`minlat,maxlat,minlon,maxlon`（若提供则自动使用 `bbox`）

**说明：**
- 使用仓库内的 Berkeley Earth 子集（`data/noaa/berkeley/Raw_TAVG_1750_1850.nc`）计算绝对温度
- 计算公式：`absolute = climatology(month) + temperature(anomaly)`
- 对时间轴按十进制年进行线性插值
- 若请求日期不在数据时间范围内，使用最近端点值（最近邻外推）

**响应示例：**
```json
{"date": "1812-03-15", "temperature_c": -1.23}
```

---

## LLM API 接口

### POST /api/llm/chat
与大语言模型进行对话交互。

**请求体 (JSON):**
```json
{
  "message": "用户消息文本",
  "system_prompt": "可选的系统提示词"
}
```

**请求参数说明:**
- `message` (string, 必需) — 用户消息文本，长度 1-10000 字符
- `system_prompt` (string, 可选) — 系统提示词，用于设定 AI 角色或上下文，最大 5000 字符

**响应 (JSON):**
```json
{
  "response": "AI 生成的回复文本",
  "model": "deepseek-chat"
}
```

**响应字段说明:**
- `response` (string) — LLM 生成的回复文本
- `model` (string) — 使用的模型名称

**说明:**
- 前端无法选择模型，只能使用后端配置的默认模型（当前为 `deepseek-chat`）
- 不支持流式响应，返回完整的回复文本
- 仅支持文本对话，不支持图片或其他多模态输入

**示例请求 (curl):**
```bash
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请简要介绍1812年拿破仑远征俄国的背景"
  }'
```

**示例响应:**
```json
{
  "response": "1812年拿破仑远征俄国的背景主要包括：1. 大陆封锁政策导致俄法关系恶化；2. 双方在波兰等地的领土争端；3. 拿破仑希望巩固欧洲霸权；4. 俄国不愿屈服于法国压力。这些因素最终促使拿破仑在1812年夏天发动了对俄国的大规模入侵。",
  "model": "deepseek-chat"
}
```

**带系统提示词的示例:**
```bash
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "分析这次战役的军事意义",
    "system_prompt": "你是一位精通1812年拿破仑俄法战争的军事历史学家"
  }'
```

---

## LLM 服务

### 服务说明
后端集成了大语言模型（LLM）服务，支持多种模型提供商，用于提供 AI 分析和对话功能。

### 支持的模型提供商

#### 1. DashScope (阿里云百炼)
- **qwen-max**: 通义千问 Max 模型
- **qwen-plus**: 通义千问 Plus 模型
- **deepseek-r1**: DeepSeek R1 模型（支持思考模式）

#### 2. DeepSeek (直连)
- **deepseek-chat**: DeepSeek Chat 模型（默认）

### 配置说明

**环境变量配置** (`.env` 文件)：
```bash
# DashScope API Key
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**模型配置** (`config/llm.yaml`)：
- 默认模型：`deepseek-chat`
- 可配置参数：temperature, max_tokens, top_p
- 支持启用/禁用特定模型

### 使用示例

```python
from src.services.llm import LLMFactory

# 创建工厂实例
factory = LLMFactory()

# 获取默认模型
provider = factory.get_provider()

# 或指定特定模型
provider = factory.get_provider("deepseek-chat")

# 发送消息
messages = [
    {"role": "system", "content": "你是一位历史学家"},
    {"role": "user", "content": "介绍1812年拿破仑战争"}
]

# 非流式响应
response = provider.chat(messages)
print(response)

# 流式响应
for chunk in provider.chat(messages, stream=True):
    print(chunk, end="", flush=True)
```

### 架构特点
- **工厂模式**: 统一的接口创建和管理
- **配置化**: 通过 YAML 文件管理模型配置
- **可扩展**: 支持注册新的模型提供商
- **实例缓存**: 自动缓存已创建的提供商实例

### 相关文档
详细使用说明请参考：`src/services/llm/README.md`
