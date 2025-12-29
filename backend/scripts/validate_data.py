"""
数据完整性验证脚本
检查项目所需的所有地理数据是否已正确下载和处理
包括：GeoJSON文件、DEM数据、历史地图等
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import sys


# 目录配置
DATA_DIR = Path(__file__).parent.parent / "data"
GEOJSON_DIR = DATA_DIR / "geojson"
DEM_DIR = DATA_DIR / "dem"
BOUNDARIES_DIR = DATA_DIR / "boundaries"
MAPS_DIR = DATA_DIR / "historical_maps"


class DataValidator:
    """数据验证器"""

    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def check_geojson_file(self, filepath: Path, name: str, required: bool = True) -> bool:
        """
        验证GeoJSON文件

        Args:
            filepath: 文件路径
            name: 显示名称
            required: 是否必需

        Returns:
            验证是否通过
        """
        if not filepath.exists():
            msg = f"{name}: 文件不存在 ({filepath.name})"
            if required:
                self.results['failed'].append(msg)
                print(f"❌ {msg}")
                return False
            else:
                self.results['warnings'].append(msg)
                print(f"⚠️  {msg}")
                return False

        try:
            # 读取GeoJSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查基本结构
            if data.get('type') not in ['FeatureCollection', 'Feature']:
                self.results['failed'].append(f"{name}: 无效的GeoJSON类型")
                print(f"❌ {name}: 无效的GeoJSON类型")
                return False

            # 获取特征数量
            if data['type'] == 'FeatureCollection':
                feature_count = len(data.get('features', []))
            else:
                feature_count = 1

            # 获取文件大小
            size_mb = filepath.stat().st_size / (1024 * 1024)

            msg = f"{name}: {filepath.name} ({feature_count} 个特征, {size_mb:.2f} MB)"
            self.results['passed'].append(msg)
            print(f"✅ {msg}")
            return True

        except json.JSONDecodeError as e:
            msg = f"{name}: JSON格式错误 - {str(e)}"
            self.results['failed'].append(msg)
            print(f"❌ {msg}")
            return False
        except Exception as e:
            msg = f"{name}: 验证出错 - {str(e)}"
            self.results['failed'].append(msg)
            print(f"❌ {msg}")
            return False

    def check_shapefile_dataset(self, directory: Path, name: str) -> bool:
        """
        验证Shapefile数据集（检查.shp, .shx, .dbf文件）

        Args:
            directory: 数据集目录
            name: 显示名称

        Returns:
            验证是否通过
        """
        if not directory.exists():
            msg = f"{name}: 目录不存在"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return False

        # 查找.shp文件
        shp_files = list(directory.glob("*.shp"))

        if not shp_files:
            msg = f"{name}: 未找到Shapefile"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return False

        # 检查关键文件
        shp_file = shp_files[0]
        stem = shp_file.stem
        required_extensions = ['.shp', '.shx', '.dbf']

        missing = []
        for ext in required_extensions:
            if not (directory / f"{stem}{ext}").exists():
                missing.append(ext)

        if missing:
            msg = f"{name}: 缺少文件 {', '.join(missing)}"
            self.results['failed'].append(msg)
            print(f"❌ {msg}")
            return False

        # 计算目录大小
        total_size = sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)

        msg = f"{name}: {directory.name} ({size_mb:.2f} MB)"
        self.results['passed'].append(msg)
        print(f"✅ {msg}")
        return True

    def check_dem_data(self) -> Tuple[int, float]:
        """
        检查DEM数据

        Returns:
            (瓦片数量, 总大小MB)
        """
        jaxa_dir = DEM_DIR / "jaxa_aw3d30"

        if not jaxa_dir.exists():
            msg = "DEM数据: jaxa_aw3d30目录不存在"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return 0, 0.0

        # 查找所有.tif文件
        tif_files = list(jaxa_dir.rglob("*.tif"))

        if not tif_files:
            msg = "DEM数据: 未找到TIFF文件"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return 0, 0.0

        # 计算总大小
        total_size = sum(f.stat().st_size for f in tif_files)
        size_mb = total_size / (1024 * 1024)

        # 统计ZIP文件（原始下载）
        zip_files = list(jaxa_dir.glob("*.zip"))

        msg = f"DEM数据: {len(tif_files)} 个TIFF文件"
        if zip_files:
            msg += f", {len(zip_files)} 个ZIP文件"
        msg += f" ({size_mb:.2f} MB)"

        self.results['passed'].append(msg)
        print(f"✅ {msg}")
        return len(tif_files), size_mb

    def check_processed_dem(self) -> bool:
        """检查处理后的DEM数据"""
        processed_dir = DEM_DIR / "processed"

        if not processed_dir.exists():
            msg = "处理后DEM: 目录不存在（可选）"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return False

        # 检查关键文件
        files_to_check = {
            'merged_dem.tif': '合并的DEM',
            'heightmap.png': '高程贴图',
            'hillshade.tif': '山体阴影'
        }

        found_files = []
        for filename, description in files_to_check.items():
            filepath = processed_dir / filename
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                found_files.append(f"{description} ({size_mb:.2f} MB)")

        if found_files:
            msg = f"处理后DEM: {', '.join(found_files)}"
            self.results['passed'].append(msg)
            print(f"✅ {msg}")
            return True
        else:
            msg = "处理后DEM: 未找到处理文件（可选）"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return False

    def check_historical_maps(self) -> bool:
        """检查历史地图"""
        if not MAPS_DIR.exists():
            msg = "历史地图: 目录不存在"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return False

        # 检查Minard图
        minard_path = MAPS_DIR / "Minard.png"
        if minard_path.exists():
            size_mb = minard_path.stat().st_size / (1024 * 1024)
            msg = f"历史地图: Minard.png ({size_mb:.2f} MB)"
            self.results['passed'].append(msg)
            print(f"✅ {msg}")
            return True
        else:
            msg = "历史地图: Minard.png 未找到"
            self.results['warnings'].append(msg)
            print(f"⚠️  {msg}")
            return False


def print_section_header(title: str):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}\n")


def main():
    """主函数"""
    print("="*60)
    print("数据完整性验证")
    print("1812拿破仑东征地理可视化项目")
    print("="*60)

    validator = DataValidator()

    # 1. 验证GeoJSON文件
    print_section_header("📍 GeoJSON数据验证")

    geojson_files = [
        (GEOJSON_DIR / "events.geojson", "历史事件", True),
        (GEOJSON_DIR / "countries.geojson", "国家边界", True),
        (GEOJSON_DIR / "provinces.geojson", "省份边界", False),
        (GEOJSON_DIR / "cities.geojson", "主要城市", True),
        (GEOJSON_DIR / "rivers.geojson", "河流湖泊", True),
        (GEOJSON_DIR / "movements.geojson", "军队移动轨迹", True),
        (GEOJSON_DIR / "territories.geojson", "领土变化", False),
        (GEOJSON_DIR / "cities_major.geojson", "大城市（过滤）", False),
        (GEOJSON_DIR / "cities_1812_campaign.geojson", "东征相关城市", False),
        (GEOJSON_DIR / "countries_eastern_europe.geojson", "东欧国家（过滤）", False),
    ]

    for filepath, name, required in geojson_files:
        validator.check_geojson_file(filepath, name, required)

    # 2. 验证Shapefile原始数据
    print_section_header("🗺️  Shapefile原始数据验证")

    shapefile_datasets = [
        (BOUNDARIES_DIR / "ne_10m_admin_0_countries", "国家边界 Shapefile"),
        (BOUNDARIES_DIR / "ne_10m_admin_1_states_provinces", "省份边界 Shapefile"),
        (BOUNDARIES_DIR / "ne_10m_populated_places", "城市点 Shapefile"),
        (BOUNDARIES_DIR / "ne_10m_rivers_lake_centerlines", "河流线 Shapefile"),
    ]

    for directory, name in shapefile_datasets:
        validator.check_shapefile_dataset(directory, name)

    # 3. 验证DEM数据
    print_section_header("🏔️  DEM高程数据验证")

    tif_count, dem_size = validator.check_dem_data()
    validator.check_processed_dem()

    # 检查等高线
    contours_path = DEM_DIR / "contours.geojson"
    validator.check_geojson_file(contours_path, "等高线", required=False)

    # 4. 验证历史地图
    print_section_header("🖼️  历史地图验证")

    validator.check_historical_maps()

    # 5. 总结报告
    print_section_header("📊 验证总结")

    passed_count = len(validator.results['passed'])
    failed_count = len(validator.results['failed'])
    warning_count = len(validator.results['warnings'])

    print(f"✅ 通过: {passed_count} 项")
    print(f"❌ 失败: {failed_count} 项")
    print(f"⚠️  警告: {warning_count} 项")

    # 详细列表
    if validator.results['failed']:
        print("\n❌ 失败项目:")
        for msg in validator.results['failed']:
            print(f"   - {msg}")

    if validator.results['warnings']:
        print("\n⚠️  警告项目:")
        for msg in validator.results['warnings']:
            print(f"   - {msg}")

    # 项目就绪状态
    print("\n" + "="*60)

    # 检查必需文件
    required_files = [
        GEOJSON_DIR / "events.geojson",
        GEOJSON_DIR / "countries.geojson",
        GEOJSON_DIR / "cities.geojson",
        GEOJSON_DIR / "rivers.geojson",
    ]

    all_required_exist = all(f.exists() for f in required_files)
    has_dem = tif_count > 0

    if all_required_exist and has_dem:
        print("🎉 项目数据已就绪！可以开始开发。")
        print("\n建议:")
        print("  1. 如果缺少 movements.geojson，需要手动创建军队移动轨迹")
        print("  2. 可选：运行 process_dem.py 处理DEM数据生成高程贴图")
        print("  3. 可选：下载更多历史地图到 data/historical_maps/story/")
        return_code = 0
    elif all_required_exist:
        print("⚠️  基础GeoJSON文件已就绪，但缺少DEM数据")
        print("\n建议:")
        print("  1. 运行 download_jaxa_aw3d30.py 下载DEM数据")
        print("  2. 创建 movements.geojson 军队移动轨迹")
        return_code = 1
    else:
        print("❌ 项目数据不完整，无法开始开发")
        print("\n建议:")
        print("  1. 运行 download_geodata.py 下载行政区划数据")
        print("  2. 运行 convert_shapefiles_to_geojson.py 转换GeoJSON")
        print("  3. 运行 download_jaxa_aw3d30.py 下载DEM数据")
        print("  4. 创建 movements.geojson 军队移动轨迹")
        return_code = 2

    print("="*60)

    sys.exit(return_code)


if __name__ == "__main__":
    main()
