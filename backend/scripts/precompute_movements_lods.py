"""Precompute simplified movements GeoJSON for multiple LODs.

Usage:
    uv run python scripts/precompute_movements_lods.py

LOD Levels:
    1: High detail (zoom > 8) - tolerance 0.00005
    2: Medium-high detail (zoom 7-8) - tolerance 0.0001
    3: Medium detail (zoom 6-7) - tolerance 0.0005
    4: Medium-low detail (zoom 5-6) - tolerance 0.001
    5: Low detail (zoom 4-5) - tolerance 0.005
    6: Very low detail (zoom 3-4) - tolerance 0.01
    7: Minimal detail (zoom < 3) - aggregated to points
"""
from __future__ import annotations

import json
from pathlib import Path

# Extended LOD mapping with more granular levels
# Based on zoom levels: higher zoom = more detail
DEFAULT_LOD_MAP = {
    1: 0.00005,  # High detail (zoom > 8)
    2: 0.0001,  # Medium-high detail (zoom 7-8)
    3: 0.0005,  # Medium detail (zoom 6-7)
    4: 0.001,  # Medium-low detail (zoom 5-6)
    5: 0.005,  # Low detail (zoom 4-5)
    6: 0.01,  # Very low detail (zoom 3-4)
    7: "aggregate",  # Minimal detail (zoom < 3) - points
}

# Zoom to LOD mapping for automatic selection
ZOOM_TO_LOD = {
    # zoom_level: lod_level
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


def main():
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data" / "geojson"

    # load movements.geojson
    movements_file = data_dir / "movements.geojson"
    if not movements_file.exists():
        print(f"Error: {movements_file} not found")
        print("Please run generate_movements_geojson.py first")
        return

    print(f"Loading {movements_file}...")
    with open(movements_file, "r", encoding="utf-8") as fh:
        gj = json.load(fh)

    feature_count = len(gj.get("features", []))
    print(f"Loaded {feature_count} movement features")

    # ensure we can import from src when invoked as a script in CI/local
    import sys

    sys.path.insert(0, str(root))
    from src.services.movement_utils import precompute_lods

    print(f"\nPrecomputing {len(DEFAULT_LOD_MAP)} LOD levels...")
    written = precompute_lods(gj, DEFAULT_LOD_MAP, data_dir)

    print("\n✓ Successfully wrote LOD files:")
    for p in written:
        print(f"  - {p}")

    print(f"\nTotal files created: {len(written)}")


if __name__ == "__main__":
    main()
