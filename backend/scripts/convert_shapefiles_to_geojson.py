"""
Shapefile到GeoJSON转换脚本
用于将Natural Earth的Shapefile数据转换为GeoJSON格式
支持国家边界、城市点、河流等地理数据的转换
"""

import os
import subprocess
from pathlib import Path
import sys


# 目录配置
DATA_DIR = Path(__file__).parent.parent / "data"
BOUNDARIES_DIR = DATA_DIR / "boundaries"
GEOJSON_DIR = DATA_DIR / "geojson"

# 确保输出目录存在
GEOJSON_DIR.mkdir(parents=True, exist_ok=True)


# 转换配置：源文件 -> 目标文件
CONVERSION_TASKS = [
    {
        "name": "国家边界",
        "source": BOUNDARIES_DIR / "ne_10m_admin_0_countries" / "ne_10m_admin_0_countries.shp",
        "target": GEOJSON_DIR / "countries.geojson",
        "description": "世界各国边界数据"
    },
    {
        "name": "省份边界",
        "source": BOUNDARIES_DIR / "ne_10m_admin_1_states_provinces" / "ne_10m_admin_1_states_provinces.shp",
        "target": GEOJSON_DIR / "provinces.geojson",
        "description": "一级行政区划边界"
    },
    {
        "name": "主要城市",
        "source": BOUNDARIES_DIR / "ne_10m_populated_places" / "ne_10m_populated_places.shp",
        "target": GEOJSON_DIR / "cities.geojson",
        "description": "世界主要城市点位"
    },
    {
        "name": "河流湖泊",
        "source": BOUNDARIES_DIR / "ne_10m_rivers_lake_centerlines" / "ne_10m_rivers_lake_centerlines.shp",
        "target": GEOJSON_DIR / "rivers.geojson",
        "description": "河流和湖泊中心线"
    }
]


def check_ogr2ogr():
    """检查ogr2ogr是否已安装"""
    try:
        result = subprocess.run(
            ["ogr2ogr", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ 检测到GDAL/OGR: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("❌ 未检测到ogr2ogr工具")
    print("\n请安装GDAL:")
    print("  - Windows: 安装OSGeo4W (https://trac.osgeo.org/osgeo4w/)")
    print("  - Ubuntu/WSL: sudo apt install gdal-bin")
    print("  - macOS: brew install gdal")
    print("  - Conda: conda install -c conda-forge gdal")
    return False


def convert_shapefile(source: Path, target: Path, name: str, description: str) -> bool:
    """
    使用ogr2ogr将Shapefile转换为GeoJSON

    Args:
        source: 源Shapefile路径
        target: 目标GeoJSON路径
        name: 数据集名称
        description: 数据集描述

    Returns:
        转换是否成功
    """
    # 检查源文件是否存在
    if not source.exists():
        print(f"⚠️  跳过 {name}: 源文件不存在")
        print(f"   路径: {source}")
        return False

    print(f"\n{'='*60}")
    print(f"转换: {name}")
    print(f"描述: {description}")
    print(f"源文件: {source.name}")
    print(f"目标: {target.name}")
    print(f"{'='*60}")

    try:
        # 构建ogr2ogr命令
        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",           # 输出格式
            "-t_srs", "EPSG:4326",     # 目标坐标系（WGS84）
            "-progress",               # 显示进度
            str(target),               # 输出文件
            str(source)                # 输入文件
        ]

        # 执行转换
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # 获取文件大小
            size_mb = target.stat().st_size / (1024 * 1024)
            print(f"✅ 转换成功！")
            print(f"   输出: {target}")
            print(f"   大小: {size_mb:.2f} MB")
            return True
        else:
            print(f"❌ 转换失败！")
            print(f"   错误信息: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 转换出错: {str(e)}")
        return False


def convert_with_filter(source: Path, target: Path, name: str, where_clause: str):
    """
    使用SQL WHERE子句过滤并转换Shapefile

    Args:
        source: 源Shapefile路径
        target: 目标GeoJSON路径
        name: 数据集名称
        where_clause: SQL WHERE子句（例如：'POP_MAX > 1000000'）
    """
    if not source.exists():
        print(f"⚠️  跳过 {name}: 源文件不存在")
        return False

    print(f"\n转换: {name} (带过滤)")
    print(f"过滤条件: {where_clause}")

    try:
        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            "-where", where_clause,
            str(target),
            str(source)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size_mb = target.stat().st_size / (1024 * 1024)
            print(f"✅ 转换成功！大小: {size_mb:.2f} MB")
            return True
        else:
            print(f"❌ 转换失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 转换出错: {str(e)}")
        return False


def create_filtered_datasets():
    """
    创建过滤后的专用数据集（可选）
    例如：仅东欧地区、仅大城市等
    """
    print("\n" + "="*60)
    print("创建过滤数据集（可选）")
    print("="*60)

    # 1. 仅东欧国家（用于1812项目）
    countries_src = BOUNDARIES_DIR / "ne_10m_admin_0_countries" / "ne_10m_admin_0_countries.shp"
    if countries_src.exists():
        # 东欧相关国家
        eastern_europe = [
            'Russia', 'Poland', 'Lithuania', 'Belarus', 'Ukraine',
            'Latvia', 'Estonia', 'Germany', 'Austria', 'France'
        ]
        where = "NAME IN ('" + "','".join(eastern_europe) + "')"

        convert_with_filter(
            countries_src,
            GEOJSON_DIR / "countries_eastern_europe.geojson",
            "东欧国家",
            where
        )

    # 2. 仅大城市（人口>100万）
    cities_src = BOUNDARIES_DIR / "ne_10m_populated_places" / "ne_10m_populated_places.shp"
    if cities_src.exists():
        convert_with_filter(
            cities_src,
            GEOJSON_DIR / "cities_major.geojson",
            "主要大城市",
            "POP_MAX > 1000000"
        )

    # 3. 历史相关城市（1812东征路线）
    if cities_src.exists():
        historical_cities = [
            'Moscow', 'Vilnius', 'Minsk', 'Smolensk', 'Warsaw',
            'Kaunas', 'Vitebsk', 'Borodino', 'Maloyaroslavets'
        ]
        where = "NAME IN ('" + "','".join(historical_cities) + "')"

        convert_with_filter(
            cities_src,
            GEOJSON_DIR / "cities_1812_campaign.geojson",
            "1812东征相关城市",
            where
        )


def main():
    """主函数"""
    print("="*60)
    print("Shapefile到GeoJSON转换工具")
    print("Natural Earth数据转换")
    print("="*60)

    # 检查工具
    if not check_ogr2ogr():
        sys.exit(1)

    # 执行转换任务
    success_count = 0
    fail_count = 0
    skip_count = 0

    for task in CONVERSION_TASKS:
        if task["source"].exists():
            result = convert_shapefile(
                task["source"],
                task["target"],
                task["name"],
                task["description"]
            )
            if result:
                success_count += 1
            else:
                fail_count += 1
        else:
            skip_count += 1
            print(f"\n⚠️  跳过 {task['name']}: 源文件不存在")

    # 可选：创建过滤数据集
    print("\n是否创建过滤数据集？(y/n): ", end='')
    if input().lower().strip() == 'y':
        create_filtered_datasets()

    # 总结
    print("\n" + "="*60)
    print("转换完成！")
    print("="*60)
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"⚠️  跳过: {skip_count}")
    print(f"\n输出目录: {GEOJSON_DIR}")

    # 列出生成的文件
    geojson_files = list(GEOJSON_DIR.glob("*.geojson"))
    if geojson_files:
        print(f"\n生成的GeoJSON文件 ({len(geojson_files)}个):")
        for f in sorted(geojson_files):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  - {f.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
