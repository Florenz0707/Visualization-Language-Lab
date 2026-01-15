# 数据资源下载与处理指南

> **项目**: 1812拿破仑东征地理可视化
> **更新日期**: 2026-01-15
> **维护者**: 开发者A

本文档说明如何获取和处理项目所需的所有地理数据资源，包含**完整流程**：环境配置 → 数据下载 → 格式转换 → 验证。

---

## 📋 资源清单

| 资源类型 | 状态 | 大小 | 优先级 | 说明 |
|---------|------|------|--------|------|
| 历史事件数据 | ✅ 已完成 | <1MB | 必需 | 已生成 |
| Events GeoJSON | ✅ 已完成 | <1MB | 必需 | 已生成 |
| DEM高程数据 | ⬇️ 需下载 | ~12GB | 必需 | 3D地形渲染 |
| 行政区划边界 | ⬇️ 需下载 | ~50MB | 必需 | 自动下载 |
| 历史地图 | ⬇️ 需下载 | ~10MB | 推荐 | Story Mode |
| Movements轨迹 | ⚠️ 待创建 | - | 必需 | 需手动绘制 |

---

````markdown
# 数据资源下载与处理指南（自动扫描更新）

> **项目**: 1812拿破仑东征地理可视化
> **更新日期**: 2026-01-15
> **维护者**: 项目仓库

本文档汇总了当前 `data/` 目录下的主要数据集、占用空间、关键文件位置和生成脚本，便于复现与后续处理。

---

## 当前 data 目录概览（磁盘使用）

以下为对 `data/` 直接子项的快速统计（运行 `du -sh data/*` 得到）：

- `data/data.md`: 约 8.0K
- `data/1812_campaign_timeline.json`: 约 20K
- `data/historical_maps`: 约 680K
- `data/story`: 约 32M
- `data/boundaries`: 约 97M
- `data/noaa`: 约 219M
- `data/geojson`: 约 432M
- `data/dem`: 约 13G

> 注：以上大小为 2026-01-15 的磁盘使用快照。

---

## 目录与关键文件说明

- `data/dem/`（约 13G）
	- 子目录 `jaxa_aw3d30/`：包含 JAXA AW3D30 瓦片（当前项目区域相关瓦片）：
		- N050E020_N055E025/
		- N050E025_N055E030/
		- N050E030_N055E035/
		- N050E035_N055E040/
		- N050E040_N055E045/
		- N055E020_N060E025/
		- N055E025_N060E030/
		- N055E030_N060E035/
		- N055E035_N060E040/
		- N055E040_N060E045/
	- `processed/`：脚本处理后输出的裁剪/瓦片化结果（用于渲染和等高线）。

- `data/geojson/`（约 432M）
	- 存放已生成的 GeoJSON：`countries.geojson`、`provinces.geojson`、`cities.geojson`、`events.geojson`、`movements*.geojson`、`contours.geojson` 等。

- `data/boundaries/`（约 97M）
	- 包含 Natural Earth 原始边界数据（国家、省份、城市、河流等的 shapefiles / 解压目录）。

- `data/historical_maps/`（约 680K）
	- 项目中使用的历史地图图像（例如 Minard 等），用于故事视图和参考。

- `data/story/`（约 32M）
	- Story 模块的媒体、艺术品和相关资源。

- `data/1812_campaign_timeline.json`（约 20K）
	- 项目事件时间线的 JSON 源，供 `scripts/generate_events_geojson.py` 使用。

- `data/noaa/`（约 219M）
	- `berkeley/`：包含从 Berkeley Earth 下载并处理的重建产品（用于替代历史观测站在 1812 年附近缺失的情况）：
		- `Raw_TAVG_LatLong1.nc` — 原始 Berkeley Earth 全局 TAVG 网格（约 199MB，包含 1750+ 的十进制年份时间坐标）。
		- `Raw_TAVG_1750_1850.nc` — 从 `Raw_TAVG_LatLong1.nc` 子集得到的 1750–1850 范围（约 29MB）。
		- `Raw_TAVG_1750_1850.global_mean_temperature.dates.csv` — 1750–1850 的全球加权平均时间序列（已将十进制年份转换为中月日期）。
		- `absolute_temperature_1812_global.csv` — 基于 `climatology` + `anomaly` 计算得到的 1812（1月中旬）全局绝对温度（单行 CSV）。

> 复现脚本：`scripts/download_berkeley_1812.py`（下载与子集化），`scripts/get_abs_temp_by_climatology.py`（使用 climatology 计算绝对温度并导出 CSV）。

---

## 如何复现或更新这些数据

1. 下载并准备环境（参见仓库根目录的运行说明）：

```bash
cd backend
uv venv
source .venv/bin/activate
uv sync
```

2. 生成/刷新 GeoJSON 与边界数据：

```bash
uv run scripts/download_geodata.py
uv run scripts/convert_shapefiles_to_geojson.py
```

3. 处理 DEM：

```bash
uv run scripts/download_jaxa_aw3d30.py   # 若需要自动下载
uv run scripts/process_dem.py
```

4. 获取并处理 Berkeley Earth 温度重建（已在仓库中完成示例）

```bash
uv run scripts/download_berkeley_1812.py   # 从 Berkeley Earth 下载并子集
uv run scripts/get_abs_temp_by_climatology.py --year 1812.0416666666667
```

---

## 说明与建议

- 本次扫描聚焦于磁盘上已有的文件；若需要更详细的内容索引（例如每个 GeoJSON 的 feature 计数、每个 DEM 瓦片的分辨率或具体文件哈希），我可以运行额外的检查脚本并把结果追加到本文件。
- 如果要把 `data/noaa/berkeley` 中的完整 1750–1850 的 bbox 内绝对温度时间序列导出为 CSV（用于可视化），我可以直接生成并保存到 `data/noaa/berkeley/` 下。
