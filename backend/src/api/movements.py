from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_geojson, reproject_geojson

router = APIRouter()


@router.get("/movements")
async def get_movements(projection: Optional[str] = Query("wgs84")) -> Dict[str, Any]:
    """Return movements FeatureCollection loaded from data/geojson/movements.geojson.

    Supported projections: `wgs84` (default), `webmercator`, `lambert`.
    """
    try:
        if projection == "wgs84":
            gj = load_geojson("movements.geojson")
        else:
            gj = reproject_geojson("movements.geojson", projection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return gj
