**API 接口说明 (基础)**

- **GET /api/events**: 返回 `events.geojson` 的 FeatureCollection。
  - Query 参数：`start` (YYYY-MM-DD，可选), `end` (YYYY-MM-DD，可选), `projection` (wgs84，预留)
  - 示例：`/api/events?start=1812-09-01&end=1812-10-01`

- **支持投影参数**: 所有主要端点支持 `projection` 查询参数，允许客户端请求不同坐标参考系（默认 `wgs84`）。
  - 支持值：`wgs84`（EPSG:4326，默认）、`webmercator`（EPSG:3857）、`lambert`（EPSG:3034）。
  - 示例：`/api/events?projection=webmercator&start=1812-09-01&end=1812-10-01`

- **GET /api/movements**: 返回 `movements.geojson` 的 FeatureCollection（军队行军轨迹）。
  - 无需参数。
  - 示例：`/api/movements`

- **GET /api/territories**: 返回 `territories.geojson` 的 FeatureCollection（按事件缓冲合并的控制区）。
  - Query 参数：`projection` (wgs84，预留)
  - 示例：`/api/territories`

- **GET /api/flows**: 返回简化的 flow 对（每条行军轨迹的起止点），用于前端流向图（flow map）渲染。
  - Query 参数:
    - `simplify` (bool, 默认 true): 是否对路径应用 Douglas–Peucker 简化
    - `threshold` (float, 默认 0.01): 简化容差（仅在 `simplify=true` 时生效）
  - 响应: GeoJSON FeatureCollection，每个 Feature 为一条 LineString（仅包含起点与终点坐标）及若干 properties (`unit`, `events_count`, `start_date`, `end_date`)。
  - 兼容模式: 当环境变量 `LIGHTWEIGHT_MODE=1` 时，端点返回空的 FeatureCollection（用于测试/CI 以避免加载大文件）。
  - 示例：`/api/flows?simplify=true&threshold=0.05`

备注：
- 若某些数据文件不存在，请运行相应的生成脚本：
  - `scripts/generate_movements_geojson.py` -> 生成 `data/geojson/movements.geojson`
  - `scripts/generate_terrirories_geojson.py` -> 生成 `data/geojson/territories.geojson`
  - `scripts/process_dem.py` 或 `gdal_contour` -> 生成 `data/geojson/contours.geojson`

- 本接口为最小实现，返回静态 GeoJSON。后续可加入投影转换、时间窗口切片与缓存策略。
