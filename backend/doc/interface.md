**API 接口说明 (基础)**

- **GET /api/events**: 返回 `events.geojson` 的 FeatureCollection。
  - Query 参数：
    - `start` (YYYY-MM-DD，可选) — 起始日期过滤
    ````markdown
    **API 接口说明 (基础)**

    - **GET /api/events**: 返回 `events.geojson` 的 FeatureCollection。
      - Query 参数：
        - `start` (YYYY-MM-DD，可选) — 起始日期过滤
        - `end` (YYYY-MM-DD，可选) — 结束日期过滤
        - `bbox` (可选) — 空间范围过滤，格式：`minx,miny,maxx,maxy`（逗号分隔的浮点数）
        - `projection` (可选, 默认 `wgs84`) — 支持值：`wgs84`（EPSG:4326）、`webmercator`（EPSG:3857）、`lambert`（EPSG:3034）
      - 性能优化：使用时间索引（B-tree）和空间索引（R-tree）加速查询
      - 示例：`/api/events?start=1812-09-01&end=1812-10-01&bbox=20,50,40,60`

    - **GET /api/movements**: 返回 `movements.geojson` 的 FeatureCollection（军队行军轨迹）。
      - 可选 Query 参数：
        - `projection` (可选, 默认 `wgs84`) — 支持 `wgs84`,`webmercator`,`lambert`
        - `bbox` (可选) — 空间范围过滤，格式：`minx,miny,maxx,maxy`（逗号分隔的浮点数）
        - `simplify` (bool, 默认 `false`) — 是否对路径应用简化
        - `tolerance` (float, 默认 `0.01`) — 简化容差（坐标单位）
        - `lod` (int, 可选, 1-7) — LOD等级：1=最高细节，7=聚合点
        - `zoom` (int, 可选, 0-12) — 地图缩放级别，自动选择合适的LOD
        - `group` (bool, 默认 `false`) — 是否按 `unit` 字段分组并在响应中返回 `groups`
        - `bundling` (bool, 默认 `false`) — 是否在响应中包含 `bundling` 预计算数据
      - LOD系统：
        - LOD 1-2: 高细节（zoom > 7）
        - LOD 3-4: 中等细节（zoom 5-7）
        - LOD 5-6: 低细节（zoom 3-5）
        - LOD 7: 聚合为点（zoom < 3）
      - 性能优化：使用空间索引（R-tree）加速 bbox 查询
      - 示例：`/api/movements?zoom=18&bbox=20,50,40,60`

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

    - **GET /api/story/outline**: 返回 Story Mode 的章节大纲数据。
      - Query 参数：
        - `chapter_id` (int, 可选) — 指定章节 ID，返回单个章节；不指定则返回所有章节
      - 响应：JSON 对象，包含标题、描述和章节列表。每个章节包含：
        - `id`: 章节标识符
        - `title`: 章节标题
        - `date`: 历史日期 (YYYY-MM-DD)
        - `event_ids`: 关联的事件 ID 列表
        - `camera`: 镜头参数对象 (`center` 坐标, `zoom`, `pitch`, `bearing`)
        - `narrative`: 历史背景文本（200-300字）
        - `image`: 配图信息对象 (`url`, `attribution`)
      - 示例：`/api/story/outline` 或 `/api/story/outline?chapter_id=1`

    - **GET /api/story/tts/{chapter_id}**: 返回指定章节的TTS音频文件。
      - 路径参数：
        - `chapter_id` (int, 必需) — 章节ID
      - 响应：WAV格式音频文件（`audio/wav`）
      - 说明：
        - 服务启动时会自动检测 `data/story/tts/` 目录下的音频文件
        - 如果音频文件不存在，会使用 Kokoro-82M 模型自动生成
        - 音频内容为对应章节的 `narrative` 字段文本
        - 音频文件命名格式：`{chapter_id}.wav`
      - 示例：`/api/story/tts/1` 返回第1章的音频文件

    备注：

    - 若某些数据文件不存在，请运行相应的生成脚本：
      - `scripts/generate_movements_geojson.py` -> 生成 `data/geojson/movements.geojson`
      - `scripts/generate_terrirories_geojson.py` -> 生成 `data/geojson/territories.geojson`
      - `scripts/process_dem.py` 或 `gdal_contour` -> 生成 `data/geojson/contours.geojson`

    ---

    新增接口：

    - **GET /api/temperature/1812**: 返回 1812 年指定日期的绝对温度（线性插值），响应仅包含 `date` 和 `temperature_c`。
      - Query 参数：
        - `date_str` (必需, YYYY-MM-DD) — 查询的历史日期，必须位于 1812 年内
        - `scope` (可选, 默认 `bbox`) — `global` 或 `bbox`；当使用 `bbox` 时会在数据集上按区域加权平均
        - `bbox` (可选) — 覆盖区域的边界，格式：`minlat,maxlat,minlon,maxlon`（若提供则自动使用 `bbox`）
      - 说明：
        - 使用仓库内的 Berkeley Earth 子集（`data/noaa/berkeley/Raw_TAVG_1750_1850.nc`）计算绝对温度：
          `absolute = climatology(month) + temperature(anomaly)`，对时间轴按十进制年进行线性插值。
        - 若请求日期等于 `1812-01-01` 则为年初月的插值结果；若不在数据时间范围内，使用最近端点值（最近邻外推）。
      - 响应示例（成功）：
        ```json
        {"date": "1812-03-15", "temperature_c": -1.23}
        ```

    ````
