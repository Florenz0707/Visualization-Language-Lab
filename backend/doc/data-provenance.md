# 数据来源与处理记录（data-provenance.md）

目的
- 记录数据来源、处理步骤、引用与置信度分级，保证可追溯性（provenance）。

1) 原始来源（示例）
- Charles Minard 图表（历史参考）
- 开放地理数据（Natural Earth, OpenStreetMap）
- SRTM / AW3D 等 DEM 提供者
- 文献与档案（论文、档案馆记录）

2) 数据处理流水（示例顺序）
1. 原始数据采集：下载 SRTM / AW3D 原始 tiff、边界 shapefile、历史事件表。
2. 初步清洗：地名标准化、坐标修正、时间格式化。
3. 生成点/线/面：使用 `scripts/generate_events_geojson.py`、`generate_movements_geojson.py`、`generate_terrirories_geojson.py`。
4. DEM 处理：使用 `scripts/process_dem.py` 进行裁剪、重采样、hillshade 与等高线生成。
5. 验证与测试：`scripts/validate_data.py` 检查几何有效性与必需字段。

3) 置信度（confidence）分级说明
- 0.95 - 1.00: 高置信度 — 来自多份独立、可靠的一手资料或明确的档案记录。
- 0.80 - 0.95: 中等置信度 — 多数来源一致或由可信二手资料推断。
- 0.50 - 0.80: 估计/推断 — 来源有限或存在不一致性，需在可视化中标注不确定性。
- < 0.50: 低置信度 — 明显为估算或存在重大争议，建议在前端以淡化/提示方式展示。

4) 数据元（建议在每个生成的文件中包含的 provenance 字段）
- `generated_at` (ISO8601): 文件生成时间
- `generated_by` (string): 脚本或工具名（例如 `generate_movements_geojson.py`）
- `source_files` (array[string]): 用到的原始文件列表或 URL
- `processing_steps` (array[string]): 关键处理步骤描述
- `confidence_note` (string, optional): 针对该文件的总体置信度说明

示例（JSON metadata）
```
{
  "generated_at": "2026-01-07T18:00:00Z",
  "generated_by": "scripts/generate_movements_geojson.py",
  "source_files": ["data/1812_campaign_timeline.json", "data/boundaries/ne_10m_admin_0_countries.shp"],
  "processing_steps": ["normalize place names","buffer events 50km","dissolve by unit"],
  "confidence_note": "Movements lines are reconstructed from event points; per-feature confidence available in properties.confidence"
}
```

5) 可复现性与版本控制
- 将所有生成脚本与参数记录在 `data/provenance/`（可选），并使用 Git tags 或 `data_version` 字段记录数据快照。推荐使用 Git LFS 存储大文件（DEM / GeoTIFF）。

6) 引用与许可
- 对于每个外部数据源在 `docs/data-provenance.md` 中列出引用（URL/作者/许可），并在生成的文件元中保留 `sources` 列表以便溯源。

维护建议
- 在 `scripts/` 中添加 `--metadata-out` 参数以在数据生成时同时写入 provenance JSON。对关键处理步骤使用日志并将其包含在文件元中。
