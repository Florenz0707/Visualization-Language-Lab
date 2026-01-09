from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, shape


def simplify_path(line: LineString, tolerance: float) -> LineString:
    return line.simplify(tolerance, preserve_topology=True)


def _line_start_end_coords(
    line: LineString,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    coords = list(line.coords)
    return coords[0], coords[-1]


def _vector_and_angle(
    a: Tuple[float, float], b: Tuple[float, float]
) -> Tuple[Tuple[float, float], float]:
    vx = b[0] - a[0]
    vy = b[1] - a[1]
    angle = math.degrees(math.atan2(vy, vx))
    return (vx, vy), angle


def group_movements_by_unit(
    gj: Dict[str, Any], unit_field: str = "unit"
) -> Dict[str, List[Dict]]:
    """Group movement features by a properties field (e.g. `unit`).

    Returns a dict: unit -> list of feature objects
    """
    groups: Dict[str, List[Dict]] = {}
    for f in gj.get("features", []):
        props = f.get("properties", {})
        unit = props.get(unit_field) or "unknown"
        groups.setdefault(unit, []).append(f)
    return groups


def generate_bundling_data(
    gj: Dict[str, Any], weight_field: Optional[str] = None
) -> Dict[str, Any]:
    """Generate aggregated bundling data from a movements GeoJSON.

    Aggregates by `unit` and returns a mapping unit -> aggregated metrics:
    {
      unit: {
         "count": int,  # number of features
         "weight": float, # total weight
         "start": [x,y],  # weighted average start
         "end": [x,y],    # weighted average end
         "angle": float,  # weighted circular mean angle (degrees)
      }
    }
    """
    groups: Dict[str, Dict[str, float]] = {}
    # accumulator per unit
    for f in gj.get("features", []):
        geom = f.get("geometry")
        if not geom:
            continue
        try:
            line = shape(geom)
            if not isinstance(line, LineString):
                continue
        except Exception:
            continue

        start, end = _line_start_end_coords(line)
        _, angle = _vector_and_angle(start, end)
        props = f.get("properties", {})
        weight = 1.0
        if weight_field and weight_field in props:
            try:
                weight = float(props.get(weight_field) or 1.0)
            except Exception:
                weight = 1.0

        unit = props.get("unit") or "unknown"
        acc = groups.setdefault(
            unit,
            {
                "count": 0,
                "weight": 0.0,
                "start_x": 0.0,
                "start_y": 0.0,
                "end_x": 0.0,
                "end_y": 0.0,
                "sum_sin": 0.0,
                "sum_cos": 0.0,
            },
        )

        acc["count"] += 1
        acc["weight"] += weight
        acc["start_x"] += start[0] * weight
        acc["start_y"] += start[1] * weight
        acc["end_x"] += end[0] * weight
        acc["end_y"] += end[1] * weight
        import math

        rad = math.radians(angle)
        acc["sum_cos"] += math.cos(rad) * weight
        acc["sum_sin"] += math.sin(rad) * weight

    # finalize aggregation
    out: Dict[str, Any] = {}
    for unit, acc in groups.items():
        w = acc["weight"] if acc["weight"] != 0 else acc["count"] or 1
        start = [acc["start_x"] / w, acc["start_y"] / w]
        end = [acc["end_x"] / w, acc["end_y"] / w]
        import math

        angle = (
            math.degrees(math.atan2(acc["sum_sin"], acc["sum_cos"]))
            if (acc["sum_sin"] or acc["sum_cos"])
            else 0.0
        )

        out[unit] = {
            "count": int(acc["count"]),
            "weight": float(acc["weight"]),
            "start": [float(start[0]), float(start[1])],
            "end": [float(end[0]), float(end[1])],
            "angle": float(angle),
        }

    return out


def simplify_geojson(gj: Dict[str, Any], tolerance: float) -> Dict[str, Any]:
    """Return a new GeoJSON dict with LineString geometries simplified by tolerance."""
    from shapely.geometry import shape

    out = {"type": gj.get("type", "FeatureCollection"), "features": []}
    for f in gj.get("features", []):
        geom = f.get("geometry")
        if not geom:
            out["features"].append(f)
            continue
        try:
            geom_obj = shape(geom)
            if isinstance(geom_obj, LineString):
                simp = geom_obj.simplify(tolerance, preserve_topology=True)
                new_f = {**f, "geometry": simp.__geo_interface__}
                out["features"].append(new_f)
            else:
                out["features"].append(f)
        except Exception:
            out["features"].append(f)
    return out


def aggregate_to_points(gj: Dict[str, Any], group_by: str = "unit") -> Dict[str, Any]:
    """Aggregate LineString movements to Point features by grouping.

    For low LOD levels, convert movement paths to aggregated points
    representing the centroid of each group.

    Args:
        gj: GeoJSON FeatureCollection with LineString features
        group_by: Property field to group by (default: "unit")

    Returns:
        GeoJSON FeatureCollection with Point features
    """
    from shapely.geometry import MultiPoint, Point

    groups: Dict[str, List[Tuple[float, float]]] = {}
    group_props: Dict[str, Dict[str, Any]] = {}

    for f in gj.get("features", []):
        geom = f.get("geometry")
        props = f.get("properties", {})
        group_key = props.get(group_by) or "unknown"

        if not geom:
            continue

        try:
            line = shape(geom)
            if isinstance(line, LineString):
                # Get centroid of the line
                centroid = line.centroid
                groups.setdefault(group_key, []).append((centroid.x, centroid.y))

                # Accumulate properties
                if group_key not in group_props:
                    group_props[group_key] = {
                        group_by: group_key,
                        "count": 0,
                        "total_events": 0,
                    }
                group_props[group_key]["count"] += 1
                if "events_count" in props:
                    try:
                        group_props[group_key]["total_events"] += int(
                            props["events_count"]
                        )
                    except Exception:
                        pass
        except Exception:
            continue

    # Create point features from aggregated groups
    features = []
    for group_key, coords in groups.items():
        if not coords:
            continue

        # Calculate centroid of all centroids
        multi_point = MultiPoint(coords)
        centroid = multi_point.centroid

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [centroid.x, centroid.y]},
            "properties": group_props.get(group_key, {group_by: group_key}),
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def precompute_lods(gj: Dict[str, Any], lod_map: dict, out_dir) -> list:
    """Precompute simplified GeoJSON files for given LOD map.

    lod_map: mapping of lod -> tolerance or 'aggregate'
    out_dir: Path-like directory to write files
    Returns list of written file paths
    """
    import json
    from pathlib import Path

    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    written = []
    for lod, config in lod_map.items():
        if config == "aggregate":
            # For lowest LOD, aggregate to points
            outgj = aggregate_to_points(gj)
        else:
            # For other LODs, simplify with tolerance
            outgj = simplify_geojson(gj, config)

        fname = p / f"movements_lod_{lod}.geojson"
        with open(fname, "w", encoding="utf-8") as fh:
            json.dump(outgj, fh, ensure_ascii=False, indent=2)
        written.append(str(fname))
    return written
