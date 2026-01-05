from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_geojson

router = APIRouter()


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
):
    """Return events FeatureCollection filtered by optional start/end dates.

    Date format: ISO8601 (YYYY-MM-DD or full datetime).
    """
    try:
        gj = load_geojson("events.geojson")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    features = gj.get("features", [])
    sdate = _parse_date(start) if start else None
    edate = _parse_date(end) if end else None

    def in_range(feat: dict) -> bool:
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

    filtered = [f for f in features if in_range(f)]
    return {"type": "FeatureCollection", "features": filtered}
