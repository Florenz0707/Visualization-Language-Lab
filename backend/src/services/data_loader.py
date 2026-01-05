import json
import json as _json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import geopandas as gpd
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "geojson"


@lru_cache(maxsize=32)
def load_geojson(name: str) -> Dict[str, Any]:
    """Load a GeoJSON file from data/geojson and cache it.

    Args:
        name: filename under data/geojson (e.g. 'events.geojson')

    Returns:
        Parsed GeoJSON as a dict.
    """
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"GeoJSON not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


PROJECTIONS = {
    "wgs84": "EPSG:4326",
    "webmercator": "EPSG:3857",
    "lambert": "EPSG:3034",
}


def load_geojson_gdf(name: str) -> gpd.GeoDataFrame:
    """Load a GeoJSON into a GeoDataFrame (assumes WGS84 source).

    Args:
        name: filename under data/geojson

    Returns:
        GeoDataFrame with CRS EPSG:4326
    """
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"GeoJSON not found: {path}")
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    return gdf


def gdf_to_geojson_dict(gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    """Convert GeoDataFrame to GeoJSON dict."""
    g = gdf.copy()
    # Convert datetime-like columns to ISO strings to avoid JSON serialization issues
    for col in g.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(g[col]):
                g[col] = g[col].astype(str)
        except Exception:
            pass

        # Convert numpy arrays or other array-like objects to Python lists
        try:
            if g[col].dtype == object:
                g[col] = g[col].apply(
                    lambda v: v.tolist() if hasattr(v, "tolist") else v
                )
        except Exception:
            pass

    # Ensure no numpy types remain that break json.dumps
    def _convert_numpy(o):
        if isinstance(o, np.generic):
            return o.item()
        return o

    # apply conversion across object columns
    for col in g.columns:
        if g[col].dtype == object:
            g[col] = g[col].apply(lambda v: _convert_numpy(v))

    return _json.loads(g.to_json())


def reproject_geojson(name: str, projection: str) -> Dict[str, Any]:
    """Load GeoJSON file and reproject to requested projection name.

    Supported projection names: keys of PROJECTIONS.
    """
    proj = PROJECTIONS.get(projection, "EPSG:4326")
    gdf = load_geojson_gdf(name)
    try:
        gdf2 = gdf.to_crs(proj)
    except Exception:
        # If reprojection fails, return original as dict
        return gdf_to_geojson_dict(gdf)
    return gdf_to_geojson_dict(gdf2)
