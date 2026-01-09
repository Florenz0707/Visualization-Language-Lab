from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from shapely.geometry import LineString, shape
from src.services.data_loader import (
    build_spatial_index,
    load_geojson,
    reproject_geojson,
)
from src.services.movement_utils import (
    generate_bundling_data,
    group_movements_by_unit,
    simplify_path,
)

router = APIRouter()

# Zoom to LOD mapping for automatic LOD selection
ZOOM_TO_LOD = {
    0: 7,
    1: 7,
    2: 7,  # Very far out - aggregated points
    3: 6,
    4: 6,  # Far out - very simplified
    5: 5,
    6: 4,  # Medium distance - simplified
    7: 3,
    8: 2,  # Close - detailed
    9: 1,
    10: 1,
    11: 1,
    12: 1,  # Very close - full detail
}

# Extended LOD tolerance mapping
LOD_TOLERANCES = {
    1: 0.00005,  # High detail
    2: 0.0001,  # Medium-high detail
    3: 0.0005,  # Medium detail
    4: 0.001,  # Medium-low detail
    5: 0.005,  # Low detail
    6: 0.01,  # Very low detail
    7: 0.05,  # Minimal detail (fallback if aggregate not available)
}


@router.get("/movements")
async def get_movements(
    projection: Optional[str] = Query("wgs84"),
    simplify: bool = Query(False),
    tolerance: float = Query(0.01),
    group: bool = Query(False),
    bundling: bool = Query(False),
    lod: Optional[int] = Query(None, ge=1, le=7),
    zoom: Optional[int] = Query(None, ge=0, le=12),
    bbox: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Return movements FeatureCollection.

    Optional query params:
    - `projection` (str): coordinate projection (wgs84, webmercator, lambert)
    - `simplify` (bool): apply Douglas-Peucker simplification with `tolerance`
    - `tolerance` (float): simplification tolerance in coordinate units
    - `group` (bool): return grouped features by `unit` under `groups` key
    - `bundling` (bool): include precomputed bundling metadata under `bundling` key
    - `lod` (int): Level of Detail (1-7), 1=highest detail, 7=aggregated points
    - `zoom` (int): Map zoom level (0-12), automatically selects appropriate LOD
    - `bbox` (str): bounding box filter as 'minx,miny,maxx,maxy'

    Note: If both `lod` and `zoom` are provided, `lod` takes precedence.
    """
    # Auto-select LOD from zoom level if zoom provided and lod not specified
    if zoom is not None and lod is None:
        lod = ZOOM_TO_LOD.get(zoom, 3)  # Default to medium detail
    # Parse bbox if provided
    bbox_tuple = None
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

    try:
        if projection == "wgs84":
            gj = load_geojson("movements.geojson")
        else:
            gj = reproject_geojson("movements.geojson", projection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Apply spatial filtering if bbox provided
    if bbox_tuple:
        try:
            idx = build_spatial_index("movements.geojson")
            if idx:
                # Use spatial index for efficient bbox query
                gj["features"] = idx.query_bbox(bbox_tuple)
            else:
                # Fallback: manual filtering if rtree not available
                filtered = []
                for f in gj.get("features", []):
                    geom = f.get("geometry")
                    if geom:
                        try:
                            bounds = shape(geom).bounds
                            # Check if bounds intersect with bbox
                            if not (
                                bounds[2] < bbox_tuple[0]
                                or bounds[0] > bbox_tuple[2]
                                or bounds[3] < bbox_tuple[1]
                                or bounds[1] > bbox_tuple[3]
                            ):
                                filtered.append(f)
                        except Exception:
                            continue
                gj["features"] = filtered
        except Exception:
            # If indexing fails, continue with all features
            pass

    # handle LOD: if lod provided, try to load precomputed file, otherwise
    # fallback to using a tolerance mapping and simplify on-the-fly
    if lod is not None:
        try:
            fname = f"movements_lod_{lod}.geojson"
            if projection == "wgs84":
                gj_lod = load_geojson(fname)
            else:
                gj_lod = reproject_geojson(fname, projection)
            gj = gj_lod
        except FileNotFoundError:
            # fallback: determine tolerance from lod and simplify
            tol = LOD_TOLERANCES.get(lod, tolerance)
            for f in gj.get("features", []):
                geom = f.get("geometry")
                if not geom:
                    continue
                try:
                    line = shape(geom)
                    if isinstance(line, LineString):
                        simp = simplify_path(line, tol)
                        f["geometry"] = simp.__geo_interface__
                except Exception:
                    continue
    else:
        # optionally simplify geometries when no lod requested
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
