"""
地理数据下载脚本
用于下载1812年拿破仑东征项目所需的地理数据
包括：SRTM DEM、历史地图、行政区划边界
"""

import os
import requests
from pathlib import Path
import zipfile
import tarfile

# 创建数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
DEM_DIR = DATA_DIR / "dem"
BOUNDARIES_DIR = DATA_DIR / "boundaries"
MAPS_DIR = DATA_DIR / "historical_maps"

for dir_path in [DEM_DIR, BOUNDARIES_DIR, MAPS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, output_path: Path, chunk_size: int = 8192):
    """下载文件并显示进度"""
    print(f"正在下载: {url}")
    print(f"保存至: {output_path}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"\r进度: {percent:.1f}%", end='')

    print("\n下载完成！")
    return output_path


def download_srtm_dem():
    """
    下载SRTM DEM数据（北纬50-60°，东经20-45°）

    数据源选项：
    1. USGS EarthExplorer: https://earthexplorer.usgs.gov/
    2. OpenTopography: https://opentopography.org/
    3. CGIAR-CSI SRTM: https://srtm.csi.cgiar.org/
    """
    print("\n=== SRTM DEM数据下载 ===")
    print("覆盖区域: 北纬50-60°，东经20-45°")
    print("\n推荐数据源:")
    print("1. CGIAR-CSI SRTM 90m - 免费，无需注册")
    print("   URL: https://srtm.csi.cgiar.org/srtmdata/")
    print("\n2. NASA SRTM 30m - 需要注册")
    print("   URL: https://earthexplorer.usgs.gov/")

    # CGIAR-CSI SRTM 瓦片列表（覆盖东欧-俄罗斯）
    srtm_tiles = [
        # 格式: (纬度, 经度)
        (50, 20), (50, 25), (50, 30), (50, 35), (50, 40),
        (55, 20), (55, 25), (55, 30), (55, 35), (55, 40),
        (60, 20), (60, 25), (60, 30), (60, 35), (60, 40),
    ]

    print("\n需要下载的SRTM瓦片（5°x5°网格）:")
    for lat, lon in srtm_tiles:
        tile_name = f"srtm_{lat:02d}_{lon:02d}"
        print(f"  - {tile_name}")

    print("\n自动下载示例（CGIAR-CSI）:")
    # 示例：下载一个瓦片
    example_tile = "srtm_38_03"  # 覆盖莫斯科地区
    example_url = f"https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/{example_tile}.zip"

    print(f"示例URL: {example_url}")
    print("\n注意：CGIAR网站可能需要手动下载。")
    print("完整瓦片列表已保存至: dem_tiles_list.txt")

    # 保存瓦片列表
    tile_list_file = DEM_DIR / "dem_tiles_list.txt"
    with open(tile_list_file, 'w', encoding='utf-8') as f:
        f.write("# SRTM DEM瓦片下载列表\n")
        f.write("# 覆盖区域: 北纬50-60°，东经20-45°\n\n")
        for lat, lon in srtm_tiles:
            tile_name = f"srtm_{(lat // 5) * 5 + 3:02d}_{(lon // 5) * 5 + 3:02d}"
            url = f"https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/{tile_name}.zip"
            f.write(f"{url}\n")

    print(f"瓦片列表已保存至: {tile_list_file}")


def download_natural_earth_data():
    """
    下载Natural Earth数据（行政区划边界）
    免费、公开数据，适合历史地图
    """
    print("\n=== Natural Earth行政区划数据下载 ===")

    datasets = [
        {
            "name": "国家边界（1:10m）",
            "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
            "file": "ne_10m_admin_0_countries.zip"
        },
        {
            "name": "一级行政区（1:10m）",
            "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip",
            "file": "ne_10m_admin_1_states_provinces.zip"
        },
        {
            "name": "主要城市（1:10m）",
            "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip",
            "file": "ne_10m_populated_places.zip"
        },
        {
            "name": "河流湖泊（1:10m）",
            "url": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip",
            "file": "ne_10m_rivers_lake_centerlines.zip"
        }
    ]

    for dataset in datasets:
        print(f"\n下载: {dataset['name']}")
        output_path = BOUNDARIES_DIR / dataset['file']

        try:
            download_file(dataset['url'], output_path)

            # 解压
            print("正在解压...")
            with zipfile.ZipFile(output_path, 'r') as zip_ref:
                extract_dir = BOUNDARIES_DIR / dataset['file'].replace('.zip', '')
                extract_dir.mkdir(exist_ok=True)
                zip_ref.extractall(extract_dir)
            print(f"解压完成: {extract_dir}")

        except Exception as e:
            print(f"下载失败: {e}")
            print(f"请手动下载: {dataset['url']}")


def download_osm_data():
    """
    下载OpenStreetMap历史数据提取
    可以获取现代道路网络（用于参考）
    """
    print("\n=== OpenStreetMap数据下载 ===")
    print("推荐使用Geofabrik提取服务")
    print("URL: https://download.geofabrik.de/")

    regions = [
        ("俄罗斯", "https://download.geofabrik.de/russia-latest-free.shp.zip"),
        ("波兰", "https://download.geofabrik.de/europe/poland-latest-free.shp.zip"),
        ("波罗的海", "https://download.geofabrik.de/europe/lithuania-latest-free.shp.zip"),
    ]

    print("\n可下载的区域:")
    for region, url in regions:
        print(f"  - {region}: {url}")

    print("\n注意：OSM数据为现代数据，需要手动筛选适用于1812年的要素")


def create_download_instructions():
    """创建详细的下载说明文档"""
    instructions_file = DATA_DIR / "DOWNLOAD_INSTRUCTIONS.md"

    content = """# 地理数据下载说明

## 1. SRTM DEM数据（数字高程模型）

### 覆盖区域
- 北纬50-60°，东经20-45°
- 覆盖波兰、立陶宛、白俄罗斯、乌克兰西部、俄罗斯西部

### 数据源选项

#### 选项A：CGIAR-CSI SRTM（推荐，90m分辨率）
- 网站：https://srtm.csi.cgiar.org/srtmdata/
- 分辨率：90米
- 格式：GeoTIFF
- 优点：免费，无需注册
- 缺点：分辨率较低

**下载步骤：**
1. 访问 https://srtm.csi.cgiar.org/srtmdata/
2. 选择"SRTM Data Search"
3. 在地图上选择区域或输入坐标
4. 下载对应的5°x5°瓦片（.zip格式）
5. 解压后得到.tif文件

**所需瓦片：**
- srtm_38_03.zip（覆盖莫斯科）
- srtm_38_04.zip（覆盖斯摩棱斯克）
- srtm_37_03.zip
- srtm_37_04.zip
- 更多瓦片见 `dem_tiles_list.txt`

#### 选项B：NASA SRTM（30m分辨率）
- 网站：https://earthexplorer.usgs.gov/
- 分辨率：30米（更高精度）
- 格式：GeoTIFF
- 需要注册USGS账号（免费）

**下载步骤：**
1. 注册账号：https://ers.cr.usgs.gov/register/
2. 登录 EarthExplorer
3. 在"Search Criteria"中输入坐标或画框选择区域
4. 在"Data Sets"中选择：Digital Elevation > SRTM > SRTM 1 Arc-Second Global
5. 点击"Results"查看可用瓦片
6. 下载所需瓦片

#### 选项C：OpenTopography（学术用途）
- 网站：https://opentopography.org/
- 提供全球DEM数据API
- 可直接指定边界框下载

## 2. 行政区划边界数据

### Natural Earth Data（推荐）

**网站：** https://www.naturalearthdata.com/

**下载列表：**
1. **国家边界**
   - URL: https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip
   - 用途：1812年欧洲国家边界参考

2. **一级行政区**
   - URL: https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip
   - 用途：省/州边界

3. **主要城市**
   - URL: https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip
   - 用途：历史城市位置参考

4. **河流湖泊**
   - URL: https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip
   - 用途：涅曼河、别列津纳河等

**注意：** Natural Earth为现代数据，1812年边界需要手动调整

## 3. 历史地图底图

### 公有领域历史地图源

#### David Rumsey地图收藏
- 网站：https://www.davidrumsey.com/
- 搜索："Russia 1812" 或 "Napoleon"
- 格式：高分辨率JPEG/TIFF
- 可下载georeferenced版本

#### Library of Congress
- 网站：https://www.loc.gov/maps/
- 搜索："Russia 1812 Napoleon"
- 公有领域，可自由使用

#### Wikimedia Commons
- 网站：https://commons.wikimedia.org/
- 搜索："1812 Russia map"
- 推荐地图：
  - "Carte figurative" by Charles Minard (1869)
  - 19世纪俄罗斯帝国地图

## 4. OpenStreetMap数据（现代参考）

### Geofabrik提取服务
- 网站：https://download.geofabrik.de/

**下载区域：**
- 俄罗斯：https://download.geofabrik.de/russia-latest-free.shp.zip
- 波兰：https://download.geofabrik.de/europe/poland-latest-free.shp.zip
- 立陶宛：https://download.geofabrik.de/europe/lithuania-latest-free.shp.zip
- 白俄罗斯：https://download.geofabrik.de/europe/belarus-latest-free.shp.zip

## 5. 使用Python自动下载

运行本脚本：
```bash
python scripts/download_geodata.py
```

或使用命令行工具：

### wget下载示例
```bash
# 下载Natural Earth国家边界
wget https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip

# 下载Geofabrik俄罗斯数据
wget https://download.geofabrik.de/russia-latest-free.shp.zip
```

### curl下载示例
```bash
# 下载Natural Earth城市数据
curl -O https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip
```

## 6. 数据处理流程

下载完成后，按以下顺序处理：

1. **解压所有.zip文件**
2. **GDAL裁剪DEM到项目区域**
   ```bash
   gdalwarp -te 20 50 45 60 -tr 0.001 0.001 input.tif output.tif
   ```
3. **转换Shapefile为GeoJSON**
   ```bash
   ogr2ogr -f GeoJSON output.geojson input.shp
   ```
4. **投影转换**（如需）
   ```bash
   gdalwarp -t_srs EPSG:3034 input.tif output_lambert.tif
   ```

## 7. 数据存储结构

```
backend/data/
├── dem/                          # DEM数据
│   ├── raw/                      # 原始SRTM瓦片
│   ├── merged/                   # 合并后的DEM
│   └── processed/                # 处理后的高程图
├── boundaries/                   # 行政区划
│   ├── countries/
│   ├── provinces/
│   └── cities/
├── historical_maps/              # 历史地图
│   ├── minard_1869.tif
│   └── russia_1812.jpg
└── geojson/                      # GeoJSON成品
    ├── events.geojson
    ├── movements.geojson
    └── territories.geojson
```

## 8. 推荐数据大小

- SRTM DEM（15个瓦片）：约 500MB - 1GB
- Natural Earth边界：约 50MB
- 历史地图（高分辨率）：约 100-500MB
- OSM数据（可选）：约 1-5GB

**总计：约 2-7GB**

## 9. 数据许可

- **SRTM DEM**: 公有领域（Public Domain）
- **Natural Earth**: 公有领域（Public Domain）
- **OSM**: ODbL License（需署名）
- **历史地图**: 检查各来源的具体许可

## 10. 故障排除

### 问题：下载速度慢
- 解决：使用多线程下载工具（aria2c）
- 或使用国内镜像源（如有）

### 问题：SRTM瓦片找不到
- 解决：检查瓦片命名规则，确认坐标正确
- 或使用OpenTopography API

### 问题：文件损坏
- 解决：验证MD5/SHA256校验和
- 重新下载损坏的文件

---

**更新日期：** 2025-12-29
**维护者：** 开发者A
"""

    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n详细下载说明已保存至: {instructions_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("1812拿破仑东征项目 - 地理数据下载工具")
    print("=" * 60)

    # 创建下载说明文档
    create_download_instructions()

    # SRTM DEM下载指引
    download_srtm_dem()

    print("\n" + "=" * 60)
    input("按Enter键继续下载Natural Earth数据...")

    # Natural Earth数据自动下载
    download_natural_earth_data()

    # OSM数据指引
    print("\n" + "=" * 60)
    download_osm_data()

    print("\n" + "=" * 60)
    print("数据下载脚本执行完成！")
    print(f"数据保存目录: {DATA_DIR}")
    print(f"详细说明文档: {DATA_DIR / 'DOWNLOAD_INSTRUCTIONS.md'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
