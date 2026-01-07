from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from shapely.geometry import LineString, shape
from src.services.data_loader import load_geojson, reproject_geojson
from src.services.movement_utils import (
    generate_bundling_data,
    group_movements_by_unit,
    simplify_path,
)

router = APIRouter()


@router.get("/movements")
async def get_movements(
    projection: Optional[str] = Query("wgs84"),
    simplify: bool = Query(False),
    tolerance: float = Query(0.01),
    group: bool = Query(False),
    bundling: bool = Query(False),
) -> Dict[str, Any]:
    """Return movements FeatureCollection.

    Optional query params:
    - `simplify` (bool): apply Douglas-Peucker simplification with `tolerance`.
    - `tolerance` (float): simplification tolerance in coordinate units.
    - `group` (bool): return grouped features by `unit` under `groups` key.
    - `bundling` (bool): include precomputed bundling metadata under `bundling` key.
    """
    try:
        if projection == "wgs84":
            gj = load_geojson("movements.geojson")
        else:
            gj = reproject_geojson("movements.geojson", projection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # optionally simplify geometries
    if simplify:
        for f in gj.get("features", []):
            geom = f.get("geometry")
            if not geom:
                continue
            try:
                line = shape(geom)
                if isinstance(line, LineString):
                    simp = simplify_path(line, tolerance)
                    f["geometry"] = simp.__geo_interface__
            except Exception:
                continue

    result: Dict[str, Any] = {
        "type": "FeatureCollection",
        "features": gj.get("features", []),
    }

    # grouping by unit
    if group:
        result["groups"] = group_movements_by_unit(gj, unit_field="unit")

    # precompute bundling metadata
    if bundling:
        result["bundling"] = generate_bundling_data(gj, weight_field="events_count")

    return result
