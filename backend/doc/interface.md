**API 接口说明 (基础)**

- **GET /api/events**: 返回 `events.geojson` 的 FeatureCollection。
  - Query 参数：`start` (YYYY-MM-DD，可选), `end` (YYYY-MM-DD，可选), `projection` (wgs84，预留)
  - 示例：`/api/events?start=1812-09-01&end=1812-10-01`

- **GET /api/movements**: 返回 `movements.geojson` 的 FeatureCollection（军队行军轨迹）。
  - 无需参数。
  - 示例：`/api/movements`

- **GET /api/territories**: 返回 `territories.geojson` 的 FeatureCollection（按事件缓冲合并的控制区）。
  - Query 参数：`projection` (wgs84，预留)
  - 示例：`/api/territories`

备注：
- 若某些数据文件不存在，请运行相应的生成脚本：
  - `scripts/generate_movements_geojson.py` -> 生成 `data/geojson/movements.geojson`
  - `scripts/generate_terrirories_geojson.py` -> 生成 `data/geojson/territories.geojson`
  - `scripts/process_dem.py` 或 `gdal_contour` -> 生成 `data/geojson/contours.geojson`

- 本接口为最小实现，返回静态 GeoJSON。后续可加入投影转换、时间窗口切片与缓存策略。
