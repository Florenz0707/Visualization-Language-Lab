# 数据资源下载指南

> **项目**: 1812拿破仑东征地理可视化
> **更新日期**: 2025-12-29
> **维护者**: 开发者A

本文档说明如何获取项目所需的所有地理数据资源。

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

## 🚀 快速开始

### 方式1：自动下载脚本（推荐）

```bash
# 1. 安装Python依赖
cd backend
pip install requests

# 2. 下载行政区划数据（自动）
python scripts/download_geodata.py

# 3. 下载DEM数据（需JAXA账号）
python scripts/download_jaxa_aw3d30.py
# 选择选项2：下载关键瓦片（~450MB，快速测试）
# 或选项1：下载完整数据（~1.5GB，完整覆盖）

# 4. 生成Events GeoJSON
python scripts/generate_events_geojson.py
```

### 方式2：手动下载（备选）

如果自动脚本失败，参考下方各资源的手动下载方法。

---

## 📦 详细下载指南

### 1. DEM高程数据（必需）

#### JAXA AW3D30（推荐，30米分辨率）

**注册账号**：

1. 访问 <https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm>
2. 点击 "Registration" 注册（免费）
3. 登录后即可下载

**下载瓦片**（覆盖北纬50-60°，东经20-45°）：

**关键瓦片（快速测试，3个，~450MB）**：

```plain
https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v2404/N055E035_N060E040.zip
https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v2404/N055E030_N060E035.zip
https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v2404/N050E025_N055E030.zip
```

**完整瓦片列表（10个，~1.5GB）**：

```plain
N050E020_N055E025.zip  N050E025_N055E030.zip  N050E030_N055E035.zip
N050E035_N055E040.zip  N050E040_N055E045.zip  N055E020_N060E025.zip
N055E025_N060E030.zip  N055E030_N060E035.zip  N055E035_N060E040.zip
N055E040_N060E045.zip
```

**保存位置**：`backend/data/dem/jaxa_aw3d30/`

**解压**：解压后每个瓦片约1-2GB，包含多个1°x1°的DSM文件

---

### 2. 行政区划边界（必需）

**自动下载**（推荐）：

```bash
python scripts/download_geodata.py
```

**手动下载**（Natural Earth Data）：

| 数据集 | 下载链接 | 用途 |
|-------|---------|------|
| 国家边界 | <https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip> | 国界 |
| 省份边界 | <https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip> | 行政区 |
| 主要城市 | <https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip> | 城市点 |
| 河流湖泊 | <https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip> | 水系 |

**保存位置**：`backend/data/boundaries/`

**解压**：自动脚本会自动解压

---

### 3. 历史地图底图（推荐）

#### Minard 1869经典图表

**直接下载**：

```bash
# 高分辨率PNG
curl -o Minard.png https://upload.wikimedia.org/wikipedia/commons/2/29/Minard.png
```

**保存位置**：`backend/data/historical_maps/Minard.png`

**状态**：✅ 已下载

---

#### 其他历史地图（可选）

**David Rumsey地图收藏**：

1. 访问 <https://www.davidrumsey.com/>
2. 搜索 "Russia 1812" 或 "Napoleon"
3. 下载高分辨率GeoTIFF或JPEG

**推荐地图**：

- "Russia in Europe" (1812)
- "Map of Napoleon's Russian Campaign"
- 19世纪俄罗斯帝国地图

**保存位置**：`backend/data/historical_maps/`

---

### 4. Story Mode配图（可选）

**公有领域历史画作**（Wikimedia Commons）：

```bash
# Battle of Borodino (弗朗茨·鲁博绘)
https://commons.wikimedia.org/wiki/File:Rubo_Borodino.jpg

# Moscow Fire 1812 (莫斯科大火)
https://commons.wikimedia.org/wiki/File:Fire_of_Moscow.jpg


# Napoleon Crossing the Alps (雅克-路易·大卫)
https://commons.wikimedia.org/wiki/File:David_-_Napoleon_crossing_the_Alps_-_Malmaison2.jpg
```

**保存位置**：`backend/data/historical_maps/story/`

**建议处理**：

- 统一尺寸：1920x1080
- 格式转换：WebP（优化加载）
- 文件命名：`battle_borodino.webp`, `moscow_fire.webp` 等

---

## 🛠️ 数据处理

下载完成后，需要进行以下处理：

### 1. DEM数据处理

```bash
# 裁剪到项目区域
gdalwarp -te 20 50 45 60 -tr 0.001 0.001 input.tif output.tif

# 生成等高线
gdal_contour -a elevation -i 100 dem.tif contours.shp
ogr2ogr -f GeoJSON contours.geojson contours.shp

# 生成hillshade
gdaldem hillshade dem.tif hillshade.tif -z 2
```

### 2. 转换Shapefile为GeoJSON

```bash
# 转换Natural Earth数据
ogr2ogr -f GeoJSON countries.geojson ne_10m_admin_0_countries.shp
ogr2ogr -f GeoJSON cities.geojson ne_10m_populated_places.shp
ogr2ogr -f GeoJSON rivers.geojson ne_10m_rivers_lake_centerlines.shp
```

### 3. 生成Events GeoJSON

```bash
python scripts/generate_events_geojson.py
```

---

## 📂 最终目录结构

```plain
backend/data/
├── 1812_campaign_timeline.json       # 历史事件数据（已有）
├── geojson/                          # GeoJSON成品
│   ├── events.geojson                # ✅ 已生成
│   ├── movements.geojson             # ⚠️ 待创建
│   ├── territories.geojson           # ⚠️ 待创建
│   ├── countries.geojson             # 从boundaries转换
│   ├── cities.geojson                # 从boundaries转换
│   └── rivers.geojson                # 从boundaries转换
├── dem/                              # DEM数据
│   ├── jaxa_aw3d30/                  # JAXA原始数据
│   │   ├── N055E035_N060E040/
│   │   └── ...
│   ├── raw/                          # 其他DEM源
│   ├── processed/                    # 处理后数据
│   │   ├── merged_dem.tif            # 合并的DEM
│   │   ├── heightmap.png             # 高程贴图
│   │   └── hillshade.tif             # 山体阴影
│   └── contours.geojson              # 等高线
├── boundaries/                       # 行政区划（Shapefile）
│   ├── ne_10m_admin_0_countries/
│   ├── ne_10m_populated_places/
│   └── ne_10m_rivers_lake_centerlines/
└── historical_maps/                  # 历史地图
    ├── Minard.png                    # ✅ 已下载
    └── story/                        # Story Mode配图
        ├── battle_borodino.webp
        ├── moscow_fire.webp
        └── ...
```

---

## ⚠️ 注意事项

### Git LFS配置

**大文件不应提交到Git**：

```bash
# 添加到.gitignore
echo "backend/data/dem/" >> .gitignore
echo "backend/data/boundaries/*.zip" >> .gitignore
echo "backend/data/historical_maps/*.tif" >> .gitignore
```

**推荐做法**：

- 仅提交小型GeoJSON文件（<10MB）
- DEM数据通过本指南手动下载
- 或使用云存储（Google Drive/OneDrive）共享

---

## 📊 数据大小估算

| 数据类型 | 快速测试 | 完整数据 |
|---------|---------|---------|
| JAXA DEM | ~450MB | ~12GB |
| Natural Earth | ~50MB | ~50MB |
| 历史地图 | ~10MB | ~100MB |
| GeoJSON | <1MB | <1MB |
| **总计** | **~500MB** | **~12GB** |

---

## 🆘 故障排除

### 问题：JAXA下载需要登录

**解决**：

1. 确认已注册账号并登录
2. 或使用OpenTopography替代方案（无需登录）

### 问题：GDAL命令不可用

**解决**：

```bash
# Windows: 安装OSGeo4W
https://trac.osgeo.org/osgeo4w/

# 或使用Conda
conda install -c conda-forge gdal

# Linux/Mac
sudo apt install gdal-bin  # Ubuntu
brew install gdal          # macOS
```

### 问题：下载速度慢

**解决**：

- 使用多线程下载工具（aria2c）
- 或分时段下载（避开高峰期）
- 或使用VPN（如JAXA在某些地区访问慢）

### 问题：文件损坏

**解决**：

1. 检查文件完整性（MD5/SHA256）
2. 重新下载损坏的文件
3. 尝试其他数据源

---

## 📞 协作支持

如有问题，请联系：

- **开发者A**（数据工程师）：负责DEM和GeoJSON数据
- **GitHub Issues**：项目仓库Issues页面
- **文档更新**：本文档持续更新

---

## 🔄 更新日志

- **2025-12-29**: 初始版本，添加JAXA DEM和Natural Earth下载指南
- **2025-12-29**: 添加OpenTopography替代方案
- **2025-12-29**: 完成Events GeoJSON生成

---

## ✅ 数据验证

下载完成后，运行验证脚本：

```bash
# 验证数据完整性
python scripts/validate_data.py

# 输出示例：
# ✅ Events GeoJSON: 17 events
# ✅ DEM数据: 10 tiles (12.4 GB)
# ✅ 行政区划: 4 datasets
# ⚠️  Movements: 未找到
```

---

**祝下载顺利！** 🚀

如果您成功下载了所有数据，可以继续进行数据处理和后端API开发。
