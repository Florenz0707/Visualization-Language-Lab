from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_geojson, reproject_geojson

router = APIRouter()


@router.get("/territories")
async def get_territories(projection: Optional[str] = Query("wgs84")) -> Dict[str, Any]:
    """Return territories FeatureCollection. Supports projection query param."""
    try:
        if projection == "wgs84":
            gj = load_geojson("territories.geojson")
        else:
            gj = reproject_geojson("territories.geojson", projection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return gj
