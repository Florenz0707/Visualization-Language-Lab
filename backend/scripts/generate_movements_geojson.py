"""Generate movements.geojson from events.geojson using simple grouping rules.

Creates LineString movements for:
 - `french_grande_armee`: events with `french_troops` or commanded by Napoleon
 - `austrian_corps`: events with `austrian_troops` or id starting with evt_sch_

Run with: `uv run python scripts/generate_movements_geojson.py`
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "geojson"
EVENTS_PATH = DATA_DIR / "events.geojson"
OUT_PATH = DATA_DIR / "movements.geojson"


def load_events() -> Dict[str, Any]:
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_date(d: str) -> datetime | None:
    try:
        return datetime.fromisoformat(d)
    except Exception:
        return None


def build_movement(features: List[Dict[str, Any]], unit: str) -> Dict[str, Any] | None:
    if len(features) < 2:
        return None
    # sort by date
    features = sorted(
        features,
        key=lambda f: (
            parse_date(f.get("properties", {}).get("date") or "") or datetime.min
        ),
    )
    coords = [
        f["geometry"]["coordinates"]
        for f in features
        if f.get("geometry") and f["geometry"].get("coordinates")
    ]
    if len(coords) < 2:
        return None
    props = {
        "unit": unit,
        "event_ids": [f.get("properties", {}).get("id") for f in features],
        "start_date": features[0].get("properties", {}).get("date"),
        "end_date": features[-1].get("properties", {}).get("date"),
        "events_count": len(features),
    }
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coords},
        "properties": props,
    }


def main() -> int:
    if not EVENTS_PATH.exists():
        print(f"Events file not found: {EVENTS_PATH}")
        return 2
    data = load_events()
    features = data.get("features", [])

    french_feats = []
    austrian_feats = []

    for f in features:
        props = f.get("properties", {})
        fid = props.get("id", "")
        # French grouping heuristics
        if props.get("french_troops") is not None or any(
            c for c in (props.get("french_commanders") or []) if "Napoleon" in c
        ):
            french_feats.append(f)
            continue

        # Austrian grouping heuristics
        if props.get("austrian_troops") is not None or fid.startswith("evt_sch_"):
            austrian_feats.append(f)
            continue

    movement_features = []
    m = build_movement(french_feats, "french_grande_armee")
    if m:
        movement_features.append(m)
    m2 = build_movement(austrian_feats, "austrian_corps")
    if m2:
        movement_features.append(m2)

    out = {"type": "FeatureCollection", "features": movement_features}

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote movements to {OUT_PATH} ({len(movement_features)} features)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
