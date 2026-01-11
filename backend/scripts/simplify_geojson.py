#!/usr/bin/env python3
"""
数据简化脚本 - 降低GeoJSON数据精度和体积

功能:
1. 简化几何形状 (Douglas-Peucker算法)
2. 降低坐标精度
3. 按地区和缩放级别生成多级LOD数据
4. 支持bbox过滤

使用方法:
    uv run python scripts/simplify_geojson.py --input data/geojson/contours.geojson --output data/geojson/contours_simplified.geojson --tolerance 0.001
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pyproj
    from shapely.geometry import mapping, shape
    from shapely.ops import transform
except ImportError:
    print(
        "Error: Required packages not found. Install with: uv pip install shapely pyproj"
    )
    sys.exit(1)


def round_coordinates(coords: Any, precision: int = 6) -> Any:
    """递归地对坐标进行精度舍入"""
    if isinstance(coords[0], (int, float)):
        # 单个坐标点 [lon, lat]
        return [round(c, precision) for c in coords]
    else:
        # 嵌套坐标
        return [round_coordinates(c, precision) for c in coords]


def simplify_geometry(
    geom: Dict, tolerance: float = 0.001, preserve_topology: bool = True
) -> Dict:
    """简化几何形状"""
    try:
        shp = shape(geom)
        simplified = shp.simplify(tolerance, preserve_topology=preserve_topology)
        return mapping(simplified)
    except Exception as e:
        print(f"Warning: Failed to simplify geometry: {e}")
        return geom


def filter_by_bbox(feature: Dict, bbox: Tuple[float, float, float, float]) -> bool:
    """检查feature是否在bbox范围内"""
    try:
        geom = shape(feature["geometry"])
        minx, miny, maxx, maxy = bbox
        bbox_geom = shape(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [minx, miny],
                        [maxx, miny],
                        [maxx, maxy],
                        [minx, maxy],
                        [minx, miny],
                    ]
                ],
            }
        )
        return geom.intersects(bbox_geom)
    except:
        return True


def process_geojson(
    input_path: Path,
    output_path: Path,
    tolerance: float = 0.001,
    precision: int = 6,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    simplify: bool = True,
) -> Dict[str, Any]:
    """处理GeoJSON文件"""
    print(f"Reading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        print("Error: Input must be a FeatureCollection")
        return {"error": "Invalid GeoJSON type"}

    features = data.get("features", [])
    print(f"Original features: {len(features)}")

    # 过滤bbox
    if bbox:
        print(f"Filtering by bbox: {bbox}")
        features = [f for f in features if filter_by_bbox(f, bbox)]
        print(f"After bbox filter: {len(features)}")

    # 处理每个feature
    processed_features = []
    for i, feature in enumerate(features):
        if i % 100 == 0:
            print(f"Processing feature {i}/{len(features)}...")

        geom = feature.get("geometry")
        if not geom:
            continue

        # 简化几何
        if simplify:
            geom = simplify_geometry(geom, tolerance)

        # 降低精度
        geom["coordinates"] = round_coordinates(geom["coordinates"], precision)

        feature["geometry"] = geom
        processed_features.append(feature)

    # 创建输出
    output_data = {"type": "FeatureCollection", "features": processed_features}

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False)

    # 统计信息
    original_size = input_path.stat().st_size
    output_size = output_path.stat().st_size
    reduction = (1 - output_size / original_size) * 100

    stats = {
        "original_features": len(features),
        "output_features": len(processed_features),
        "original_size_mb": round(original_size / 1024 / 1024, 2),
        "output_size_mb": round(output_size / 1024 / 1024, 2),
        "reduction_percent": round(reduction, 2),
    }

    print(f"\nProcessing complete!")
    print(f"Original size: {stats['original_size_mb']} MB")
    print(f"Output size: {stats['output_size_mb']} MB")
    print(f"Reduction: {stats['reduction_percent']}%")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Simplify GeoJSON files")
    parser.add_argument("--input", "-i", required=True, help="Input GeoJSON file")
    parser.add_argument("--output", "-o", required=True, help="Output GeoJSON file")
    parser.add_argument(
        "--tolerance",
        "-t",
        type=float,
        default=0.001,
        help="Simplification tolerance (default: 0.001)",
    )
    parser.add_argument(
        "--precision",
        "-p",
        type=int,
        default=6,
        help="Coordinate precision (default: 6)",
    )
    parser.add_argument("--bbox", help="Bounding box filter: minx,miny,maxx,maxy")
    parser.add_argument(
        "--no-simplify", action="store_true", help="Skip geometry simplification"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    bbox = None
    if args.bbox:
        try:
            bbox = tuple(map(float, args.bbox.split(",")))
            if len(bbox) != 4:
                raise ValueError
        except:
            print("Error: bbox must be in format: minx,miny,maxx,maxy")
            sys.exit(1)

    process_geojson(
        input_path=input_path,
        output_path=output_path,
        tolerance=args.tolerance,
        precision=args.precision,
        bbox=bbox,
        simplify=not args.no_simplify,
    )


if __name__ == "__main__":
    main()
