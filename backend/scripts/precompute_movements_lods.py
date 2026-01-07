"""Precompute simplified movements GeoJSON for multiple LODs.

Usage:
    uv run python scripts/precompute_movements_lods.py
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOD_MAP = {1: 0.0001, 2: 0.001, 3: 0.01}


def main():
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data" / "geojson"
    # load movements.geojson without importing heavy GIS libs
    with open(data_dir / "movements.geojson", "r", encoding="utf-8") as fh:
        gj = json.load(fh)
    # ensure we can import from src when invoked as a script in CI/local
    import sys

    # add repository backend root so `import src` works
    sys.path.insert(0, str(root))
    from src.services.movement_utils import precompute_lods

    written = precompute_lods(gj, DEFAULT_LOD_MAP, data_dir)
    print("Wrote:")
    for p in written:
        print("  -", p)


if __name__ == "__main__":
    main()
