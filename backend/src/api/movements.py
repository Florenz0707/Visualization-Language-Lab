from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from src.services.data_loader import load_geojson

router = APIRouter()


@router.get("/movements")
async def get_movements() -> Dict[str, Any]:
    """Return movements FeatureCollection loaded from data/geojson/movements.geojson."""
    try:
        gj = load_geojson("movements.geojson")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return gj
