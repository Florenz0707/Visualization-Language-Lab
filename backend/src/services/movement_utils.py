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
) -> List[Dict[str, Any]]:
    """Generate simple bundling precompute data from a movements GeoJSON.

    For each feature, compute start/end coordinates, vector, angle and weight.
    Returns list of dicts: {unit, start, end, vector, angle, weight}
    """
    out = []
    for f in gj.get("features", []):
        geom = f.get("geometry")
        if not geom:
            continue
        try:
            line = shape(geom)
            if not isinstance(line, LineString):
                # try to extract first LineString
                continue
        except Exception:
            continue

        start, end = _line_start_end_coords(line)
        vector, angle = _vector_and_angle(start, end)
        props = f.get("properties", {})
        weight = 1
        if weight_field and weight_field in props:
            try:
                weight = float(props.get(weight_field) or 1)
            except Exception:
                weight = 1

        out.append(
            {
                "unit": props.get("unit"),
                "start": [float(start[0]), float(start[1])],
                "end": [float(end[0]), float(end[1])],
                "vector": [float(vector[0]), float(vector[1])],
                "angle": float(angle),
                "weight": float(weight),
            }
        )

    return out
