"""
DEM数据处理脚本
处理JAXA AW3D30 DEM数据用于1812年拿破仑东征可视化项目

功能：
1. 合并多个DEM瓦片
2. 裁剪到项目区域
3. 生成等高线GeoJSON
4. 生成hillshade（山体阴影）
5. 生成heightmap PNG（用于3D渲染）
6. 投影转换（可选）
"""

import os
import subprocess
from pathlib import Path
import json

# 路径配置
DATA_DIR = Path(__file__).parent.parent / "data"
DEM_INPUT_DIR = DATA_DIR / "dem" / "jaxa_aw3d30"
DEM_OUTPUT_DIR = DATA_DIR / "dem" / "processed"
GEOJSON_DIR = DATA_DIR / "geojson"

# 创建输出目录
DEM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

# 项目区域边界（WGS84）
# 北纬50-60°，东经20-45°
BBOX = {
    "west": 20,
    "south": 50,
    "east": 45,
    "north": 60
}

# 关键事件位置（用于局部高精度处理）
KEY_LOCATIONS = [
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"name": "Smolensk", "lat": 54.7818, "lon": 32.0401},
    {"name": "Borodino", "lat": 55.5167, "lon": 35.8167},
    {"name": "Vilnius", "lat": 54.6872, "lon": 25.2797},
    {"name": "Berezina", "lat": 54.3667, "lon": 28.0167},
]


def check_gdal():
    """检查GDAL是否安装"""
    try:
        result = subprocess.run(["gdalinfo", "--version"],
                              capture_output=True, text=True, check=True)
        print(f"✅ GDAL已安装: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误: 未找到GDAL")
        print("\n请安装GDAL:")
        print("  Windows: https://trac.osgeo.org/osgeo4w/")
        print("  Conda: conda install -c conda-forge gdal")
        print("  Linux: sudo apt install gdal-bin")
        print("  macOS: brew install gdal")
        return False


def find_dem_files():
    """查找所有DEM DSM文件"""
    print("\n搜索DEM文件...")

    dem_files = []

    # 查找JAXA AW3D30 DSM文件
    if DEM_INPUT_DIR.exists():
        for tile_dir in DEM_INPUT_DIR.iterdir():
            if tile_dir.is_dir():
                # JAXA数据结构: N055E035_N060E040/N055E035_N060E040/ALPSMLC30_N*_DSM.tif
                inner_dir = tile_dir / tile_dir.name
                if inner_dir.exists():
                    dsm_files = list(inner_dir.glob("*_DSM.tif"))
                    dem_files.extend(dsm_files)

    if dem_files:
        print(f"✅ 找到 {len(dem_files)} 个DSM文件")
        # 显示前5个
        for f in dem_files[:5]:
            print(f"  - {f.name}")
        if len(dem_files) > 5:
            print(f"  ... 还有 {len(dem_files) - 5} 个文件")
    else:
        print("⚠️  未找到DEM文件")
        print(f"请确保DEM数据位于: {DEM_INPUT_DIR}")

    return dem_files


def create_vrt(dem_files, output_vrt):
    """创建VRT虚拟栅格（合并所有DEM）"""
    print("\n步骤1: 创建虚拟栅格 (VRT)...")

    cmd = [
        "gdalbuildvrt",
        str(output_vrt),
    ] + [str(f) for f in dem_files]

    print(f"执行命令: gdalbuildvrt {output_vrt.name} [...]")

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ VRT创建成功: {output_vrt}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建VRT失败: {e}")
        print(e.stderr.decode() if e.stderr else "")
        return False


def crop_dem(input_file, output_file, bbox):
    """裁剪DEM到项目区域"""
    print("\n步骤2: 裁剪DEM到项目区域...")
    print(f"区域: {bbox['west']}E-{bbox['east']}E, {bbox['south']}N-{bbox['north']}N")

    cmd = [
        "gdalwarp",
        "-te", str(bbox['west']), str(bbox['south']), str(bbox['east']), str(bbox['north']),
        "-tr", "0.001", "0.001",  # 约100米分辨率
        "-r", "bilinear",  # 双线性重采样
        "-co", "COMPRESS=LZW",
        "-co", "TILED=YES",
        str(input_file),
        str(output_file)
    ]

    print(f"执行命令: gdalwarp -te {bbox['west']} {bbox['south']} {bbox['east']} {bbox['north']} ...")

    try:
        subprocess.run(cmd, check=True, capture_output=True)

        # 获取文件信息
        size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"✅ 裁剪完成: {output_file.name} ({size_mb:.1f} MB)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 裁剪失败: {e}")
        print(e.stderr.decode() if e.stderr else "")
        return False


def generate_contours(dem_file, output_geojson, interval=100):
    """生成等高线"""
    print(f"\n步骤3: 生成等高线 (间隔{interval}m)...")

    # 先生成Shapefile
    temp_shp = DEM_OUTPUT_DIR / "contours_temp.shp"

    cmd_contour = [
        "gdal_contour",
        "-a", "elevation",
        "-i", str(interval),
        str(dem_file),
        str(temp_shp)
    ]

    print(f"执行命令: gdal_contour -a elevation -i {interval} ...")

    try:
        subprocess.run(cmd_contour, check=True, capture_output=True)
        print("✅ 等高线生成成功")

        # 转换为GeoJSON
        print("转换为GeoJSON...")
        cmd_convert = [
            "ogr2ogr",
            "-f", "GeoJSON",
            str(output_geojson),
            str(temp_shp)
        ]

        subprocess.run(cmd_convert, check=True, capture_output=True)

        # 清理临时文件
        for ext in [".shp", ".shx", ".dbf", ".prj"]:
            temp_file = DEM_OUTPUT_DIR / f"contours_temp{ext}"
            if temp_file.exists():
                temp_file.unlink()

        size_mb = output_geojson.stat().st_size / 1024 / 1024
        print(f"✅ GeoJSON生成: {output_geojson.name} ({size_mb:.1f} MB)")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ 生成等高线失败: {e}")
        print(e.stderr.decode() if e.stderr else "")
        return False


def generate_hillshade(dem_file, output_file):
    """生成hillshade（山体阴影）"""
    print("\n步骤4: 生成hillshade...")

    cmd = [
        "gdaldem", "hillshade",
        "-z", "2",  # 垂直夸张系数
        "-az", "315",  # 光源方位角
        "-alt", "45",  # 光源高度角
        "-co", "COMPRESS=LZW",
        str(dem_file),
        str(output_file)
    ]

    print("执行命令: gdaldem hillshade -z 2 -az 315 -alt 45 ...")

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"✅ Hillshade生成: {output_file.name} ({size_mb:.1f} MB)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 生成hillshade失败: {e}")
        print(e.stderr.decode() if e.stderr else "")
        return False


def generate_heightmap(dem_file, output_png, width=2048):
    """生成heightmap PNG（用于Three.js）"""
    print(f"\n步骤5: 生成heightmap PNG ({width}x{width})...")

    # 计算高度比例
    height = width  # 正方形

    cmd = [
        "gdal_translate",
        "-of", "PNG",
        "-outsize", str(width), str(height),
        "-scale",  # 自动缩放到0-255
        str(dem_file),
        str(output_png)
    ]

    print(f"执行命令: gdal_translate -of PNG -outsize {width} {height} ...")

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        size_mb = output_png.stat().st_size / 1024 / 1024
        print(f"✅ Heightmap生成: {output_png.name} ({size_mb:.1f} MB)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 生成heightmap失败: {e}")
        print(e.stderr.decode() if e.stderr else "")
        return False


def reproject_dem(input_file, output_file, target_epsg="EPSG:3034"):
    """投影转换（WGS84 → Lambert Conformal Conic）"""
    print(f"\n步骤6: 投影转换 → {target_epsg}...")

    cmd = [
        "gdalwarp",
        "-t_srs", target_epsg,
        "-r", "bilinear",
        "-co", "COMPRESS=LZW",
        str(input_file),
        str(output_file)
    ]

    print(f"执行命令: gdalwarp -t_srs {target_epsg} ...")

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"✅ 投影转换完成: {output_file.name} ({size_mb:.1f} MB)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 投影转换失败: {e}")
        print(e.stderr.decode() if e.stderr else "")
        return False


def get_dem_statistics(dem_file):
    """获取DEM统计信息"""
    print("\n步骤7: 获取DEM统计信息...")

    cmd = ["gdalinfo", "-stats", str(dem_file)]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        output = result.stdout

        # 提取关键信息
        print("DEM统计:")
        for line in output.split('\n'):
            if any(key in line for key in ['Size', 'Origin', 'Pixel Size', 'Minimum', 'Maximum', 'Mean']):
                print(f"  {line.strip()}")

        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  获取统计信息失败: {e}")
        return False


def create_processing_summary():
    """创建处理摘要JSON"""
    print("\n步骤8: 创建处理摘要...")

    summary = {
        "project": "Napoleon 1812 Campaign - DEM Processing",
        "date_processed": "2025-12-29",
        "source": "JAXA AW3D30",
        "region": {
            "west": BBOX['west'],
            "south": BBOX['south'],
            "east": BBOX['east'],
            "north": BBOX['north']
        },
        "resolution": "~100m",
        "coordinate_system": "WGS84 (EPSG:4326)",
        "outputs": {
            "merged_dem": "merged_dem_cropped.tif",
            "hillshade": "hillshade.tif",
            "heightmap": "heightmap_2048.png",
            "contours": "contours_100m.geojson",
            "projected_dem": "merged_dem_lambert.tif"
        },
        "key_locations": KEY_LOCATIONS
    }

    summary_file = DEM_OUTPUT_DIR / "processing_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"✅ 摘要保存: {summary_file.name}")


def main():
    print("=" * 70)
    print("DEM数据处理工具")
    print("1812拿破仑东征项目")
    print("=" * 70)

    # 检查GDAL
    if not check_gdal():
        return

    # 查找DEM文件
    dem_files = find_dem_files()
    if not dem_files:
        print("\n❌ 未找到DEM文件，退出")
        return

    print("\n" + "=" * 70)
    print("处理流程")
    print("=" * 70)
    print("1. 创建虚拟栅格 (VRT) - 合并所有瓦片")
    print("2. 裁剪到项目区域")
    print("3. 生成等高线 GeoJSON")
    print("4. 生成hillshade")
    print("5. 生成heightmap PNG (3D渲染用)")
    print("6. 投影转换 (可选)")
    print("7. 获取统计信息")
    print("8. 创建处理摘要")
    print("=" * 70)

    confirm = input("\n继续处理? (y/n): ").strip().lower()
    if confirm != 'y':
        print("取消处理")
        return

    print("\n" + "=" * 70)
    print("开始处理...")
    print("=" * 70)

    # 定义输出文件
    vrt_file = DEM_OUTPUT_DIR / "merged_dem.vrt"
    cropped_dem = DEM_OUTPUT_DIR / "merged_dem_cropped.tif"
    contours_file = GEOJSON_DIR / "contours_100m.geojson"
    hillshade_file = DEM_OUTPUT_DIR / "hillshade.tif"
    heightmap_file = DEM_OUTPUT_DIR / "heightmap_2048.png"
    lambert_dem = DEM_OUTPUT_DIR / "merged_dem_lambert.tif"

    # 执行处理流程
    success_count = 0

    if create_vrt(dem_files, vrt_file):
        success_count += 1
    else:
        print("\n❌ VRT创建失败，无法继续")
        return

    if crop_dem(vrt_file, cropped_dem, BBOX):
        success_count += 1
    else:
        print("\n⚠️  裁剪失败，跳过后续步骤")
        return

    # 后续步骤使用裁剪后的DEM
    if generate_contours(cropped_dem, contours_file, interval=100):
        success_count += 1

    if generate_hillshade(cropped_dem, hillshade_file):
        success_count += 1

    if generate_heightmap(cropped_dem, heightmap_file, width=2048):
        success_count += 1

    # 投影转换（可选）
    do_reproject = input("\n是否进行投影转换到Lambert? (y/n): ").strip().lower()
    if do_reproject == 'y':
        if reproject_dem(cropped_dem, lambert_dem):
            success_count += 1

    # 统计信息
    get_dem_statistics(cropped_dem)

    # 创建摘要
    create_processing_summary()

    print("\n" + "=" * 70)
    print("处理完成!")
    print("=" * 70)
    print(f"成功: {success_count} 个步骤")
    print(f"\n输出目录: {DEM_OUTPUT_DIR}")
    print(f"GeoJSON目录: {GEOJSON_DIR}")

    print("\n生成的文件:")
    for file in DEM_OUTPUT_DIR.iterdir():
        if file.is_file():
            size_mb = file.stat().st_size / 1024 / 1024
            print(f"  - {file.name} ({size_mb:.1f} MB)")

    print("\n下一步:")
    print("1. 使用QGIS查看生成的DEM和等高线")
    print("2. 在Three.js中加载heightmap_2048.png")
    print("3. 在Mapbox中加载hillshade和等高线")


if __name__ == "__main__":
    main()
