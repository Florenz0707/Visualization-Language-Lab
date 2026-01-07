from __future__ import annotations

from datetime import date
from typing import Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_geojson_gdf
from src.services.statistics import aggregate_troops_by_period

router = APIRouter()


def _to_list(df: pd.DataFrame) -> List[Dict]:
    out = []
    if df is None or df.shape[0] == 0:
        return out
    # df is expected to have either single column 'troops' or multiple columns per faction
    if "troops" in df.columns:
        for idx, row in df.itertuples():
            pass


@router.get("/statistics/troops")
async def get_troops_stats(
    start: date = Query(...),
    end: date = Query(...),
    faction: str | None = Query(None),
    period: str = Query("month"),
):
    """Return time-series troop counts aggregated by `period`.

    - `start`, `end`: ISO date strings (YYYY-MM-DD)
    - `faction`: optional, one of 'french'|'russian' to limit results
    - `period`: aggregation period ('month','week','day')
    """
    try:
        gdf = load_geojson_gdf("events.geojson")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="events.geojson not found")

    # coerce event dates
    gdf["_dt"] = pd.to_datetime(gdf.get("date"), errors="coerce")
    mask = (gdf["_dt"].dt.date >= start) & (gdf["_dt"].dt.date <= end)
    gdf = gdf[mask]

    if gdf.empty:
        return {"french": [], "russian": []}

    # build series for french and russian by summing their respective troop fields
    french_df = aggregate_troops_by_period(
        gdf, period=period, date_field="date", troops_field="french_troops"
    )
    russian_df = aggregate_troops_by_period(
        gdf, period=period, date_field="date", troops_field="russian_troops"
    )

    def df_to_list(df: pd.DataFrame):
        if df is None or df.shape[0] == 0:
            return []
        # df index are ISO timestamps
        out = []
        for idx, row in df.itertuples():
            # when df has one column 'troops', row is scalar; if multiple, row is tuple
            if isinstance(row, (int, float)):
                count = row
            else:
                # row may be a Series-like; attempt to extract 'troops' or first value
                try:
                    count = row[0]
                except Exception:
                    count = None
            out.append({"date": idx, "count": int(count) if count is not None else 0})
        return out

    resp: Dict[str, List[Dict]] = {
        "french": df_to_list(french_df),
        "russian": df_to_list(russian_df),
    }

    if faction:
        faction = faction.lower()
        if faction not in resp:
            raise HTTPException(status_code=400, detail="Unknown faction")
        return {faction: resp[faction]}

    return resp
