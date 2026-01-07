import base64
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_geojson

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEM_PROCESSED = DATA_DIR / "dem" / "processed"


@router.get("/terrain/contours")
async def get_contours(interval: int = Query(100)) -> Dict:
    """Return contours GeoJSON. Interval param is accepted for compatibility.

    Currently returns the precomputed `data/geojson/contours.geojson`.
    """
    try:
        gj = load_geojson("contours.geojson")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return gj


@router.get("/terrain/dem")
async def get_dem(bbox: str = Query(...), resolution: int = Query(512)) -> Dict:
    """Return a precomputed heightmap PNG (Base64) and metadata.

    This is a lightweight implementation: it returns the processed heightmap
    `data/dem/processed/heightmap_2048.png` encoded as base64. The `bbox`
    and `resolution` parameters are accepted for compatibility; current
    implementation does not perform on-the-fly cropping.
    """
    # validate bbox format
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(
            status_code=400, detail="bbox must be 'minx,miny,maxx,maxy'"
        )
    try:
        bbox_f = [float(p) for p in parts]
    except Exception:
        raise HTTPException(status_code=400, detail="bbox values must be numeric")

    heightmap = DEM_PROCESSED / "heightmap_2048.png"
    if not heightmap.exists():
        raise HTTPException(status_code=404, detail=f"Heightmap not found: {heightmap}")

    try:
        data = heightmap.read_bytes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    b64 = base64.b64encode(data).decode("ascii")
    return {
        "format": "png",
        "image_base64": b64,
        "requested_bbox": bbox_f,
        "requested_resolution": resolution,
        "source": str(heightmap.relative_to(Path.cwd())),
    }
