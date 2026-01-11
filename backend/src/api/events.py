from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import (
    build_spatiotemporal_index,
    load_geojson,
    reproject_geojson,
)

router = APIRouter()

# 战役区域的默认bbox (经度20-45, 纬度50-60)
DEFAULT_CAMPAIGN_BBOX = (20.0, 50.0, 45.0, 60.0)


def _parse_date(s: str) -> Optional[date]:
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


@router.get("/events")
async def get_events(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    projection: str = Query("wgs84"),
    bbox: Optional[str] = Query(None),
):
    """Return events FeatureCollection filtered by optional start/end dates and bbox.

    Date format: ISO8601 (YYYY-MM-DD or full datetime).
    Supported projections: `wgs84` (default), `webmercator`, `lambert`.
    bbox format: 'minx,miny,maxx,maxy' (comma-separated floats).
    If bbox is not provided, defaults to campaign area (N50-60, E20-45).
    """
    # Parse bbox if provided, otherwise use default campaign bbox
    if bbox:
        try:
            parts = bbox.split(",")
            if len(parts) != 4:
                raise HTTPException(
                    status_code=400, detail="bbox must be 'minx,miny,maxx,maxy'"
                )
            bbox_tuple = tuple(float(p) for p in parts)
        except ValueError:
            raise HTTPException(status_code=400, detail="bbox values must be numeric")
    else:
        bbox_tuple = DEFAULT_CAMPAIGN_BBOX

    # If projection is wgs84, use optimized indexing
    if projection == "wgs84":
        try:
            # Use temporal/spatial index for efficient queries
            if start or end or bbox:
                idx = build_spatiotemporal_index("events.geojson")
                sdate = _parse_date(start) if start else None
                edate = _parse_date(end) if end else None
                filtered = idx.query(bbox=bbox_tuple, start=sdate, end=edate)
                return {"type": "FeatureCollection", "features": filtered}
            else:
                # No filtering needed, return all
                gj = load_geojson("events.geojson")
                return {"type": "FeatureCollection", "features": gj.get("features", [])}
        except FileNotFoundError as e:
            raise HTTPException(status_code=500, detail=str(e))

    # For other projections, reproject via GeoPandas
    try:
        gj = reproject_geojson("events.geojson", projection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    features = gj.get("features", [])
    if start or end:
        sdate = _parse_date(start) if start else None
        edate = _parse_date(end) if end else None

        def in_range_feat(feat: dict) -> bool:
            props = feat.get("properties", {})
            d = props.get("date")
            if not d:
                return True
            try:
                dt = datetime.fromisoformat(d).date()
            except Exception:
                return True
            if sdate and dt < sdate:
                return False
            if edate and dt > edate:
                return False
            return True

        features = [f for f in features if in_range_feat(f)]

    return {"type": "FeatureCollection", "features": features}
