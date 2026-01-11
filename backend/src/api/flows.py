import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from shapely import wkt
from shapely.geometry import LineString
from src.services.data_loader import load_geojson

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


@router.get("/flows")
async def get_flow_data(
    simplify: bool = Query(True), threshold: float = Query(0.01)
) -> Dict[str, Any]:
    """Return flow pairs (start/end) derived from `movements.geojson`.

    Automatically filters to campaign area (N50-60, E20-45).

    Query params:
      - `simplify`: whether to apply Douglas-Peucker simplification
      - `threshold`: tolerance passed to `shapely.geometry.LineString.simplify`
    """
    # lightweight test mode: avoid heavy processing and return empty collection
    if os.getenv("LIGHTWEIGHT_MODE", "0") == "1":
        return {"type": "FeatureCollection", "features": []}

    try:
        gj = load_geojson("movements.geojson")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    features = []
    for feat in gj.get("features", []):
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords:
            continue
        try:
            line = LineString(coords)
        except Exception:
            continue

        if simplify:
            try:
                line_s = line.simplify(threshold)
            except Exception:
                line_s = line
        else:
            line_s = line

        start = list(line_s.coords[0])
        end = list(line_s.coords[-1])

        properties = feat.get("properties", {})
        out_feat = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [start, end]},
            "properties": {
                "unit": properties.get("unit"),
                "events_count": properties.get("events_count"),
                "start_date": properties.get("start_date"),
                "end_date": properties.get("end_date"),
            },
        }
        features.append(out_feat)

    # 应用默认战役区域bbox过滤
    features = filter_by_bbox(features, DEFAULT_CAMPAIGN_BBOX)

    return {"type": "FeatureCollection", "features": features}
