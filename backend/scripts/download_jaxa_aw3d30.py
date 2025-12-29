"""
JAXA AW3D30 DEM数据自动下载脚本
用于1812年拿破仑东征项目
"""

import requests
import os
from pathlib import Path
import time

# 数据保存目录
DEM_DIR = Path(__file__).parent.parent / "data" / "dem" / "jaxa_aw3d30"
DEM_DIR.mkdir(parents=True, exist_ok=True)

# JAXA AW3D30 基础URL
BASE_URL = "https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v2404/"

# 覆盖区域：北纬50-60°，东经20-45°
# AW3D30瓦片为5°x5°
LAT_RANGES = [
    (50, 55),
    (55, 60)
]

LON_RANGES = [
    (20, 25),
    (25, 30),
    (30, 35),
    (35, 40),
    (40, 45)
]


def generate_tile_name(lat1: int, lat2: int, lon1: int, lon2: int) -> str:
    """
    生成JAXA瓦片文件名
    格式: N{lat1}E{lon1}_N{lat2}E{lon2}.zip
    """
    lat1_str = f"N{lat1:03d}" if lat1 >= 0 else f"S{abs(lat1):03d}"
    lat2_str = f"N{lat2:03d}" if lat2 >= 0 else f"S{abs(lat2):03d}"
    lon1_str = f"E{lon1:03d}" if lon1 >= 0 else f"W{abs(lon1):03d}"
    lon2_str = f"E{lon2:03d}" if lon2 >= 0 else f"W{abs(lon2):03d}"

    return f"{lat1_str}{lon1_str}_{lat2_str}{lon2_str}.zip"


def download_file(url: str, output_path: Path, timeout: int = 300) -> bool:
    """
    下载文件并显示进度

    Args:
        url: 下载链接
        output_path: 保存路径
        timeout: 超时时间（秒）

    Returns:
        bool: 是否下载成功
    """
    try:
        print(f"\n正在下载: {output_path.name}")
        print(f"URL: {url}")

        # 发送请求
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        # 写入文件
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # 显示进度
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / 1024 / 1024
                        mb_total = total_size / 1024 / 1024
                        print(f"\r进度: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

        print(f"\n✅ 下载完成: {output_path.name}")
        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"\n⚠️  瓦片不存在 (404): {output_path.name}")
        else:
            print(f"\n❌ HTTP错误 ({e.response.status_code}): {e}")
        return False

    except requests.exceptions.Timeout:
        print(f"\n❌ 下载超时: {output_path.name}")
        return False

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False


def download_all_tiles(skip_existing: bool = True, delay: float = 1.0):
    """
    下载所有覆盖区域的瓦片

    Args:
        skip_existing: 是否跳过已存在的文件
        delay: 每次下载之间的延迟（秒），避免服务器压力
    """
    print("=" * 70)
    print("JAXA AW3D30 DEM数据批量下载")
    print("=" * 70)
    print(f"\n覆盖区域: 北纬50-60°，东经20-45°")
    print(f"分辨率: 30米")
    print(f"瓦片大小: 5°x5°")

    # 生成所有瓦片列表
    tiles = []
    for lat1, lat2 in LAT_RANGES:
        for lon1, lon2 in LON_RANGES:
            tile_name = generate_tile_name(lat1, lat2, lon1, lon2)
            url = BASE_URL + tile_name
            output_path = DEM_DIR / tile_name

            tiles.append({
                'name': tile_name,
                'url': url,
                'path': output_path,
                'lat': f"{lat1}-{lat2}°N",
                'lon': f"{lon1}-{lon2}°E"
            })

    print(f"\n共需下载 {len(tiles)} 个瓦片:")
    print("-" * 70)
    for i, tile in enumerate(tiles, 1):
        status = "✓ 已存在" if tile['path'].exists() else "⬇ 待下载"
        print(f"{i:2d}. {tile['name']:30s} | {tile['lat']:12s} | {tile['lon']:12s} | {status}")

    # 统计
    existing = sum(1 for t in tiles if t['path'].exists())
    to_download = len(tiles) - existing

    print("-" * 70)
    print(f"已存在: {existing} 个, 需下载: {to_download} 个")

    if to_download == 0:
        print("\n✅ 所有瓦片已下载完成!")
        return

    # 估算大小（每个瓦片约100-200MB）
    estimated_size_mb = to_download * 150
    print(f"预计下载大小: ~{estimated_size_mb:.0f} MB ({estimated_size_mb/1024:.1f} GB)")

    # 确认下载
    print("\n" + "=" * 70)
    confirm = input("确认开始下载? (y/n): ").strip().lower()

    if confirm != 'y':
        print("取消下载")
        return

    # 开始下载
    print("\n" + "=" * 70)
    print("开始下载...")
    print("=" * 70)

    success_count = 0
    failed_tiles = []

    for i, tile in enumerate(tiles, 1):
        # 跳过已存在的文件
        if skip_existing and tile['path'].exists():
            print(f"\n[{i}/{len(tiles)}] ⏭️  跳过已存在: {tile['name']}")
            continue

        print(f"\n[{i}/{len(tiles)}]")

        # 下载文件
        if download_file(tile['url'], tile['path']):
            success_count += 1
        else:
            failed_tiles.append(tile['name'])

        # 延迟，避免服务器压力
        if i < len(tiles):
            time.sleep(delay)

    # 下载完成统计
    print("\n" + "=" * 70)
    print("下载完成!")
    print("=" * 70)
    print(f"成功: {success_count} 个")
    print(f"失败: {len(failed_tiles)} 个")
    print(f"保存位置: {DEM_DIR}")

    if failed_tiles:
        print(f"\n失败的瓦片:")
        for tile in failed_tiles:
            print(f"  - {tile}")


def download_key_tiles():
    """
    只下载关键位置的瓦片（用于快速测试）
    """
    print("=" * 70)
    print("下载关键区域瓦片")
    print("=" * 70)

    # 关键区域
    key_tiles = [
        # 覆盖莫斯科、博罗季诺（35-40°E, 55-60°N）
        (55, 60, 35, 40, "莫斯科-博罗季诺"),
        # 覆盖斯摩棱斯克、维捷布斯克（30-35°E, 55-60°N）
        (55, 60, 30, 35, "斯摩棱斯克"),
        # 覆盖维尔纽斯、别列津纳河（25-30°E, 50-55°N）
        (50, 55, 25, 30, "维尔纽斯-别列津纳"),
    ]

    print("\n将下载以下3个关键瓦片:")
    for lat1, lat2, lon1, lon2, location in key_tiles:
        tile_name = generate_tile_name(lat1, lat2, lon1, lon2)
        print(f"  - {tile_name}: {location}")

    print(f"\n预计总大小: ~450 MB")

    confirm = input("\n确认下载? (y/n): ").strip().lower()

    if confirm != 'y':
        print("取消下载")
        return

    success_count = 0

    for lat1, lat2, lon1, lon2, location in key_tiles:
        tile_name = generate_tile_name(lat1, lat2, lon1, lon2)
        url = BASE_URL + tile_name
        output_path = DEM_DIR / tile_name

        if output_path.exists():
            print(f"\n⏭️  {tile_name} 已存在，跳过")
            continue

        print(f"\n下载 {location}...")
        if download_file(url, output_path):
            success_count += 1

        time.sleep(1)

    print("\n" + "=" * 70)
    print(f"✅ 完成! 成功下载 {success_count} 个瓦片")
    print(f"保存位置: {DEM_DIR}")


def list_tiles():
    """列出所有需要下载的瓦片"""
    print("=" * 70)
    print("JAXA AW3D30瓦片列表")
    print("=" * 70)
    print(f"\n覆盖区域: 北纬50-60°，东经20-45°\n")

    for lat1, lat2 in LAT_RANGES:
        for lon1, lon2 in LON_RANGES:
            tile_name = generate_tile_name(lat1, lat2, lon1, lon2)
            url = BASE_URL + tile_name
            print(f"{tile_name:30s} | {url}")


def main():
    print("=" * 70)
    print("JAXA AW3D30 DEM数据下载工具")
    print("1812拿破仑东征项目")
    print("=" * 70)

    print("\n请选择操作:")
    print("1. 下载所有瓦片 (10个, ~1.5GB)")
    print("2. 下载关键区域瓦片 (3个, ~450MB) - 推荐快速测试")
    print("3. 列出所有瓦片URL")
    print("0. 退出")

    choice = input("\n请输入选项 (0-3): ").strip()

    if choice == "1":
        download_all_tiles(skip_existing=True, delay=2.0)
    elif choice == "2":
        download_key_tiles()
    elif choice == "3":
        list_tiles()
    elif choice == "0":
        print("退出")
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
