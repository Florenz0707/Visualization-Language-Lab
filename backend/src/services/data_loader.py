import json
import json as _json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
from src.services.indexing import SpatialIndex, SpatioTemporalIndex, TemporalIndex

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "geojson"
DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

# Cache sizes can be tuned via environment variables. Defaults chosen to be
# reasonably large for local development; follow planA.md suggestion.
GEOJSON_CACHE_SIZE = int(os.getenv("GEOJSON_CACHE_SIZE", "128"))
GDF_CACHE_SIZE = int(os.getenv("GDF_CACHE_SIZE", "32"))
REPROJECT_CACHE_SIZE = int(os.getenv("REPROJECT_CACHE_SIZE", "64"))
JSON_CACHE_SIZE = int(os.getenv("JSON_CACHE_SIZE", "64"))


def _load_geojson_impl(name: str) -> Dict[str, Any]:
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


# cached wrapper
load_geojson = lru_cache(maxsize=GEOJSON_CACHE_SIZE)(_load_geojson_impl)


def _load_json_impl(name: str) -> Dict[str, Any]:
    """Load a JSON file from data directory and cache it.

    Args:
        name: relative path under data/ (e.g. 'story/outline/example.json')

    Returns:
        Parsed JSON as a dict.
    """
    path = DATA_ROOT / name
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# cached wrapper
load_json = lru_cache(maxsize=JSON_CACHE_SIZE)(_load_json_impl)


PROJECTIONS = {
    "wgs84": "EPSG:4326",
    "webmercator": "EPSG:3857",
    "lambert": "EPSG:3034",
}


def _load_geojson_gdf_impl(name: str) -> gpd.GeoDataFrame:
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


# Return a copy to avoid accidental mutation of cached GeoDataFrame
def load_geojson_gdf(name: str) -> gpd.GeoDataFrame:
    gdf = _load_geojson_gdf_cached(name)
    return gdf.copy()


_load_geojson_gdf_cached = lru_cache(maxsize=GDF_CACHE_SIZE)(_load_geojson_gdf_impl)


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


def _reproject_geojson_impl(name: str, projection: str) -> Dict[str, Any]:
    """Load GeoJSON file and reproject to requested projection name.

    Supported projection names: keys of PROJECTIONS.
    """
    proj = PROJECTIONS.get(projection, "EPSG:4326")
    gdf = _load_geojson_gdf_cached(name)
    try:
        gdf2 = gdf.to_crs(proj)
    except Exception:
        # If reprojection fails, return original as dict
        return gdf_to_geojson_dict(gdf)
    return gdf_to_geojson_dict(gdf2)


# cached reproject function: keyed by (name, projection)
reproject_geojson = lru_cache(maxsize=REPROJECT_CACHE_SIZE)(_reproject_geojson_impl)


def _build_spatial_index_impl(name: str) -> Optional[SpatialIndex]:
    """Build spatial index for a GeoJSON file.

    Args:
        name: filename under data/geojson

    Returns:
        SpatialIndex instance or None if rtree not available
    """
    try:
        gj = load_geojson(name)
        features = gj.get("features", [])
        idx = SpatialIndex()
        idx.build_from_features(features)
        return idx
    except ImportError:
        # rtree not available
        return None
    except Exception:
        return None


# cached spatial index builder
build_spatial_index = lru_cache(maxsize=16)(_build_spatial_index_impl)


def _build_temporal_index_impl(name: str, date_field: str = "date") -> TemporalIndex:
    """Build temporal index for a GeoJSON file.

    Args:
        name: filename under data/geojson
        date_field: name of the date field in properties

    Returns:
        TemporalIndex instance
    """
    gj = load_geojson(name)
    features = gj.get("features", [])
    idx = TemporalIndex(date_field)
    idx.build_from_features(features)
    return idx


# cached temporal index builder
build_temporal_index = lru_cache(maxsize=16)(_build_temporal_index_impl)


def _build_spatiotemporal_index_impl(
    name: str, date_field: str = "date"
) -> SpatioTemporalIndex:
    """Build combined spatial and temporal index for a GeoJSON file.

    Args:
        name: filename under data/geojson
        date_field: name of the date field in properties

    Returns:
        SpatioTemporalIndex instance
    """
    gj = load_geojson(name)
    features = gj.get("features", [])
    idx = SpatioTemporalIndex(date_field)
    idx.build_from_features(features)
    return idx


# cached spatiotemporal index builder
build_spatiotemporal_index = lru_cache(maxsize=16)(_build_spatiotemporal_index_impl)


def clear_caches() -> None:
    """Clear internal LRU caches (useful in tests or dev)."""
    try:
        load_geojson.cache_clear()
    except Exception:
        pass
    try:
        load_json.cache_clear()
    except Exception:
        pass
    try:
        _load_geojson_gdf_cached.cache_clear()
    except Exception:
        pass
    try:
        reproject_geojson.cache_clear()
    except Exception:
        pass
    try:
        build_spatial_index.cache_clear()
    except Exception:
        pass
    try:
        build_temporal_index.cache_clear()
    except Exception:
        pass
    try:
        build_spatiotemporal_index.cache_clear()
    except Exception:
        pass
