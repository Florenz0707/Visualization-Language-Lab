# 数据字典（data-schema.md）

本文档描述仓库中主要数据产物（GeoJSON / 辅助 JSON）的字段与含义。

通用约定
- 所有 GeoJSON 使用 `FeatureCollection`，每个 feature 的 `properties` 包含业务字段。
- `confidence`：浮点数，范围 0.0 - 1.0，表示数据的置信度或可靠性（见 provenance 文档中分级规则）。

1) events.geojson（事件点）
- type: FeatureCollection
- geometry: Point
- properties:
  - `event_id` (string): 唯一标识
  - `name` (string): 事件名字
  - `date` (ISO8601 string): 事件日期（例如 `1812-09-07`）
  - `type` (string): 事件类型（如 `battle|camp|city`）
  - `troops` (number, optional): 兵力估计
  - `casualties` (number, optional): 伤亡人数估计
  - `faction` (string, optional): 阵营（`french|russian|allied` 等）
  - `confidence` (number 0-1): 置信度
  - `sources` (array[string], optional): 原始来源引用

2) movements.geojson（行军轨迹，LineString）
- properties:
  - `unit` (string): 单位或军团标识（例如 `french_grande_armee`）
  - `event_ids` (array[string]): 关联 events 的 id 列表
  - `start_date` / `end_date` (ISO8601 string): 时间范围
  - `events_count` (integer): 关联事件数
  - `confidence` (number 0-1, optional): 若轨迹为估算或合成，则可包含置信度

3) territories.geojson（面要素，Polygon / MultiPolygon）
- properties:
  - `name` (string, optional): 领土/区域名称
  - `derived_from` (string, optional): 生成方法说明（例如 `buffer(events, 50km)`）
  - `confidence` (number 0-1, optional): 区域边界的置信度

4) contours.geojson（等高线）
- properties:
  - `elevation` (number): 等高线高程（单位：米）

5) 其他产物
- `dem` 相关栅格与 `dem_heightmap.png`：为前端渲染准备的栅格/贴图，接口返回时可能以 base64 或 URL 提供。

示例：`properties` 摘要
```
{
  "event_id": "evt_001",
  "name": "Borodino",
  "date": "1812-09-07",
  "type": "battle",
  "troops": 130000,
  "faction": "french",
  "confidence": 0.95,
  "sources": ["Minard1869", "ArchiveX"]
}
```

维护建议
- 生产环境中建议对 `confidence` 值进行一致性校验（0-1），并在数据生成脚本中保留 `sources` 与处理日志字段。
