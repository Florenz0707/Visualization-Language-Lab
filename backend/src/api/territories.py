import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_geojson, reproject_geojson

router = APIRouter()

# 战役区域的默认bbox (经度20-45, 纬度50-60)
DEFAULT_CAMPAIGN_BBOX = (20.0, 50.0, 45.0, 60.0)


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


@router.get("/territories")
async def get_territories(projection: Optional[str] = Query("wgs84")) -> Dict[str, Any]:
    """Return territories FeatureCollection. Supports projection query param.

    Automatically filters to campaign area (N50-60, E20-45).
    """
    # In LIGHTWEIGHT_MODE we avoid loading large GeoJSON files and return
    # an empty FeatureCollection to speed up tests.
    if os.getenv("LIGHTWEIGHT_MODE", "0") == "1":
        return {"type": "FeatureCollection", "features": []}
    try:
        if projection == "wgs84":
            gj = load_geojson("territories.geojson")
        else:
            gj = reproject_geojson("territories.geojson", projection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 应用默认战役区域bbox过滤
    gj["features"] = filter_by_bbox(gj["features"], DEFAULT_CAMPAIGN_BBOX)

    return gj
