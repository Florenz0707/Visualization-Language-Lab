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

- `doc/`：文档（包含 `doc/interface.md` 的基础接口说明）。

主要功能

- 数据验证与生成：使用 `scripts/` 下脚本校验并生成缺失的 GeoJSON（如 `movements.geojson`、`territories.geojson`、`contours.geojson`）。
- 后端 API：提供最小的 REST 接口以返回静态 GeoJSON（目前实现：`/api/events`、`/api/movements`、`/api/territories`）。

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
