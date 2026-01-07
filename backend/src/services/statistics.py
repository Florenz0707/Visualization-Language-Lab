from __future__ import annotations

from typing import Iterable, Optional

import geopandas as gpd
import pandas as pd

PERIOD_ALIAS = {
    "month": "M",
    "week": "W",
    "day": "D",
    "year": "Y",
}


def _normalize_period(period: str) -> str:
    return PERIOD_ALIAS.get(period, period)


def aggregate_troops_by_period(
    events: gpd.GeoDataFrame,
    period: str = "month",
    date_field: str = "date",
    troops_field: str = "troops",
    group_field: Optional[str] = None,
) -> pd.DataFrame:
    """Aggregate troop counts from an events GeoDataFrame by time period.

    Args:
        events: GeoDataFrame containing event features with date and troops fields.
        period: aggregation period, one of 'month','week','day','year' or any
            pandas offset alias (e.g. 'M','W','D').
        date_field: property/column name with event date (ISO string or datetime).
        troops_field: property/column name with troop counts (numeric).
        group_field: optional column to group by (e.g. 'faction' or 'location_name').

    Returns:
        DataFrame indexed by period (ISO string for period start) with aggregated
        troop counts. If `group_field` is provided, columns are group values.
    """
    if date_field not in events.columns:
        raise KeyError(f"date_field '{date_field}' not present in events")

    df = events.copy()

    # parse dates
    df[date_field] = pd.to_datetime(df[date_field], errors="coerce")
    if df[date_field].isna().all():
        raise ValueError("No valid dates found in events for aggregation")

    # normalize period alias
    freq = _normalize_period(period)

    # create period index (use period start as timestamp)
    try:
        period_idx = df[date_field].dt.to_period(freq)
        period_start = period_idx.dt.to_timestamp()
    except Exception:
        # fallback: use pandas Grouper with freq directly
        period_start = df[date_field].dt.to_period(freq).dt.to_timestamp()

    df = df.assign(_period=period_start)

    # coerce troops to numeric, treat missing as 0
    if troops_field in df.columns:
        df["_troops"] = pd.to_numeric(df[troops_field], errors="coerce").fillna(0)
    else:
        df["_troops"] = 0

    if group_field and group_field in df.columns:
        grouped = (
            df.groupby(["_period", group_field])["_troops"].sum().unstack(fill_value=0)
        )
        # convert index to ISO date strings for easier JSON serialization
        grouped.index = grouped.index.to_series().dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return grouped

    grouped = df.groupby("_period")["_troops"].sum()
    out = grouped.to_frame(name="troops")
    out.index = out.index.to_series().dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return out
