# 数据资源下载与处理指南

> **项目**: 1812拿破仑东征地理可视化
> **更新日期**: 2025-12-29
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

## 🚀 完整流程（一站式）

### 步骤1：环境准备

#### 安装uv（推荐）

[uv](https://github.com/astral-sh/uv) 是极速Python包管理器，比pip快10-100倍。

```bash
# Linux/macOS/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version
```

#### 创建Python环境

```bash
cd backend

# 使用uv创建虚拟环境（自动安装Python 3.11）
uv venv

# 激活环境
# Linux/macOS/WSL:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# 安装项目依赖
uv sync
```

#### 安装GDAL工具（必需）

```bash
# Ubuntu/WSL
sudo apt update
sudo apt install gdal-bin python3-gdal

# macOS
brew install gdal

# Windows - 安装OSGeo4W
# 访问: https://trac.osgeo.org/osgeo4w/
# 或使用Conda: conda install -c conda-forge gdal

# 验证安装
ogr2ogr --version
gdalinfo --version
```

---

### 步骤2：下载原始数据

#### 2.1 行政区划边界（自动下载）

```bash
cd backend

# 下载Natural Earth数据（国家、省份、城市、河流）
uv run scripts/download_geodata.py

# 预期输出：
# ✅ 下载完成: ne_10m_admin_0_countries.zip
# ✅ 下载完成: ne_10m_admin_1_states_provinces.zip
# ✅ 下载完成: ne_10m_populated_places.zip
# ✅ 下载完成: ne_10m_rivers_lake_centerlines.zip
```

#### 2.2 DEM高程数据（半自动）

```bash
# 运行下载脚本（需JAXA账号）
uv run scripts/download_jaxa_aw3d30.py

# 如果没有JAXA账号，手动下载关键瓦片：
# 1. 注册账号: https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm
# 2. 下载以下3个关键瓦片（~450MB）：
```

**关键瓦片下载链接**：

```plain
https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v2404/N055E035_N060E040.zip
https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v2404/N055E030_N060E035.zip
https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v2404/N050E025_N055E030.zip
```

保存至：`backend/data/dem/jaxa_aw3d30/`

#### 2.3 历史地图（可选）

```bash
# 下载Minard经典图表
cd backend/data/historical_maps
curl -o Minard.png https://upload.wikimedia.org/wikipedia/commons/2/29/Minard.png
```

---

### 步骤3：数据处理与转换

#### 3.1 转换Shapefile为GeoJSON

```bash
cd backend

# 运行自动转换脚本
uv run scripts/convert_shapefiles_to_geojson.py

# 脚本会自动：
# 1. 检查GDAL/OGR工具
# 2. 转换4种Natural Earth数据集
# 3. 可选：创建过滤数据集（东欧国家、大城市等）

# 预期输出：
# ✅ 转换: 国家边界 -> countries.geojson (23.4 MB)
# ✅ 转换: 省份边界 -> provinces.geojson (18.7 MB)
# ✅ 转换: 主要城市 -> cities.geojson (2.8 MB)
# ✅ 转换: 河流湖泊 -> rivers.geojson (15.2 MB)
```

#### 3.2 生成Events GeoJSON

```bash
# 从历史事件时间线生成GeoJSON
uv run scripts/generate_events_geojson.py

# 输出: data/geojson/events.geojson
```

#### 3.3 处理DEM数据（高级）

```bash
# 使用自动化脚本处理DEM
uv run scripts/process_dem.py

# 手动处理（可选）：
# 1. 裁剪到项目区域
gdalwarp -te 20 50 45 60 -tr 0.001 0.001 input.tif output.tif

# 2. 生成等高线
gdal_contour -a elevation -i 100 dem.tif contours.shp
ogr2ogr -f GeoJSON contours.geojson contours.shp

# 3. 生成山体阴影
gdaldem hillshade dem.tif hillshade.tif -z 2
```

---

### 步骤4：验证数据完整性

```bash
cd backend

# 运行验证脚本
uv run scripts/validate_data.py

# 预期输出：
# ✅ Events GeoJSON: 17 events
# ✅ 国家边界: countries.geojson (23.4 MB)
# ✅ 城市数据: cities.geojson (2.8 MB)
# ✅ 河流数据: rivers.geojson (15.2 MB)
# ✅ DEM数据: 3 tiles (450 MB)
# ⚠️  Movements: 未找到（需手动创建）
```

**祝下载顺利！** 🚀

如果您成功下载了所有数据，可以继续进行数据处理和后端API开发。
