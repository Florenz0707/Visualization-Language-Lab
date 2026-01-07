**API 接口说明 (基础)**

- **GET /api/events**: 返回 `events.geojson` 的 FeatureCollection。
  - Query 参数：`start` (YYYY-MM-DD，可选), `end` (YYYY-MM-DD，可选), `projection` (可选, 默认 `wgs84`) — 支持值：`wgs84`（EPSG:4326）、`webmercator`（EPSG:3857）、`lambert`（EPSG:3034）。
  - 示例：`/api/events?start=1812-09-01&end=1812-10-01`

- **GET /api/movements**: 返回 `movements.geojson` 的 FeatureCollection（军队行军轨迹）。
  - 可选 Query 参数：
    - `projection` (可选, 默认 `wgs84`) — 支持 `wgs84`,`webmercator`,`lambert`
    - `simplify` (bool, 默认 `false`) — 是否对路径应用简化
    - `tolerance` (float, 默认 `0.01`) — 简化容差（坐标单位）
    - `group` (bool, 默认 `false`) — 是否按 `unit` 字段分组并在响应中返回 `groups`
    - `bundling` (bool, 默认 `false`) — 是否在响应中包含 `bundling` 预计算数据（start/end, vector, angle, weight）
  - 示例：`/api/movements?simplify=true&tolerance=0.005&bundling=true`

- **GET /api/territories**: 返回 `territories.geojson` 的 FeatureCollection（按事件缓冲合并的控制区）。
  - Query 参数：`projection` (可选, 默认 `wgs84`) — 支持值：`wgs84`（EPSG:4326）、`webmercator`（EPSG:3857）、`lambert`（EPSG:3034）。
  - 示例：`/api/territories?projection=lambert`

- **GET /api/flows**: 返回简化的 flow 对（每条行军轨迹的起止点），用于前端流向图（flow map）渲染。
  - Query 参数:
    - `simplify` (bool, 默认 true): 是否对路径应用 Douglas–Peucker 简化
    - `threshold` (float, 默认 0.01): 简化容差（仅在 `simplify=true` 时生效）
  - 响应: GeoJSON FeatureCollection，每个 Feature 为一条 LineString（仅包含起点与终点坐标）及若干 properties (`unit`, `events_count`, `start_date`, `end_date`)。
  - 兼容模式: 当环境变量 `LIGHTWEIGHT_MODE=1` 时，端点返回空的 FeatureCollection（用于测试/CI 以避免加载大文件）。
  - 示例：`/api/flows?simplify=true&threshold=0.05`

- **GET /api/statistics/troops**: 返回时间序列兵力统计（按 period 聚合）。
  - Query 参数：
    - `start` (YYYY-MM-DD, 必需)
    - `end` (YYYY-MM-DD, 必需)
    - `faction` (可选, `french` 或 `russian`)
    - `period` (可选, 默认 `month`, 支持 `month`, `week`, `day`)
  - 响应：JSON 对象，键为兵力类别（`french`/`russian`），值为时间序列数组：
    ```json
    {
      "french": [{"date": "1812-06-01T00:00:00Z", "count": 420000}, ...],
      "russian": [{"date": "1812-06-01T00:00:00Z", "count": 300000}, ...]
    }
    ```
  - 示例：`/api/statistics/troops?start=1812-06-01&end=1812-12-31&period=month`

备注：

- 若某些数据文件不存在，请运行相应的生成脚本：
  - `scripts/generate_movements_geojson.py` -> 生成 `data/geojson/movements.geojson`
  - `scripts/generate_terrirories_geojson.py` -> 生成 `data/geojson/territories.geojson`
  - `scripts/process_dem.py` 或 `gdal_contour` -> 生成 `data/geojson/contours.geojson`
