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


@router.get("/movements")
async def get_movements(
    projection: Optional[str] = Query("wgs84"),
    simplify: bool = Query(False),
    tolerance: float = Query(0.01),
    group: bool = Query(False),
    bundling: bool = Query(False),
    lod: Optional[int] = Query(None),
    bbox: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Return movements FeatureCollection.

    Optional query params:
    - `simplify` (bool): apply Douglas-Peucker simplification with `tolerance`.
    - `tolerance` (float): simplification tolerance in coordinate units.
    - `group` (bool): return grouped features by `unit` under `groups` key.
    - `bundling` (bool): include precomputed bundling metadata under `bundling` key.
    - `bbox` (str): bounding box filter as 'minx,miny,maxx,maxy'.
    """
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
    LOD_TOLERANCES = {1: 0.0001, 2: 0.001, 3: 0.01}
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
