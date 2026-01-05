import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

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
