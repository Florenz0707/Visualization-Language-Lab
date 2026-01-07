"""Precompute simplified movements GeoJSON for multiple LODs.

Usage:
    uv run python scripts/precompute_movements_lods.py
"""
from __future__ import annotations

import json
from pathlib import Path

from src.services.data_loader import load_geojson
from src.services.movement_utils import precompute_lods

DEFAULT_LOD_MAP = {1: 0.0001, 2: 0.001, 3: 0.01}


def main():
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data" / "geojson"
    gj = load_geojson("movements.geojson")
    written = precompute_lods(gj, DEFAULT_LOD_MAP, data_dir)
    print("Wrote:")
    for p in written:
        print("  -", p)


if __name__ == "__main__":
    main()
