"""
地图数据API - 提供按地区和精度过滤的地图数据
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_geojson, reproject_geojson

router = APIRouter()

# 战役区域的默认bbox (经度20-45, 纬度50-60)
DEFAULT_CAMPAIGN_BBOX = (20.0, 50.0, 45.0, 60.0)

# 支持的地图数据类型
MAP_DATA_TYPES = {
    "countries": "countries_eastern_europe.geojson",
    "provinces": "provinces.geojson",
    "cities": "cities.geojson",
    "cities_major": "cities_major.geojson",
    "rivers": "rivers.geojson",
    "contours": "contours.geojson",
}


def filter_by_bbox(features: list, bbox: tuple) -> list:
    """按bbox过滤features"""
    from shapely.geometry import box, shape

    minx, miny, maxx, maxy = bbox
    bbox_geom = box(minx, miny, maxx, maxy)

    filtered = []
    for feature in features:
        try:
            geom = shape(feature["geometry"])
            if geom.intersects(bbox_geom):
                filtered.append(feature)
        except:
            continue

    return filtered


@router.get("/maps/{map_type}")
async def get_map_data(
    map_type: str,
    bbox: Optional[str] = Query(None, description="Bounding box: minx,miny,maxx,maxy"),
    projection: str = Query(
        "wgs84", description="Projection: wgs84, webmercator, lambert"
    ),
    simplify: bool = Query(False, description="Apply geometry simplification"),
    tolerance: float = Query(0.001, description="Simplification tolerance"),
):
    """
    获取地图数据

    参数:
    - map_type: 地图类型 (countries, provinces, cities, cities_major, rivers, contours)
    - bbox: 边界框过滤 (minx,miny,maxx,maxy)
    - projection: 投影方式 (wgs84, webmercator, lambert)
    - simplify: 是否简化几何形状
    - tolerance: 简化容差
    """
    # 验证map_type
    if map_type not in MAP_DATA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid map_type. Supported types: {', '.join(MAP_DATA_TYPES.keys())}",
        )

    # 获取文件名
    filename = MAP_DATA_TYPES[map_type]

    # 投影转换 (直接使用文件名)
    if projection != "wgs84":
        data = reproject_geojson(filename, projection)
    else:
        data = load_geojson(filename)

    # 解析bbox (如果未提供,使用默认战役区域bbox)
    if bbox:
        try:
            parts = bbox.split(",")
            if len(parts) != 4:
                raise ValueError
            bbox_tuple = tuple(map(float, parts))
        except:
            raise HTTPException(status_code=400, detail="Invalid bbox format")
    else:
        bbox_tuple = DEFAULT_CAMPAIGN_BBOX

    # 过滤bbox (始终应用)
    data["features"] = filter_by_bbox(data["features"], bbox_tuple)

    # 简化几何
    if simplify:
        from shapely.geometry import mapping, shape

        simplified_features = []
        for feature in data["features"]:
            try:
                geom = shape(feature["geometry"])
                simplified = geom.simplify(tolerance, preserve_topology=True)
                feature["geometry"] = mapping(simplified)
                simplified_features.append(feature)
            except:
                simplified_features.append(feature)
        data["features"] = simplified_features

    return data
