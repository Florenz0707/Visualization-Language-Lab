import json
from pathlib import Path

import geopandas as gpd
from src.services.data_loader import load_geojson_gdf
from src.services.statistics import aggregate_troops_by_period


def test_aggregate_troops_basic():
    gdf = load_geojson_gdf("events.geojson")
    # ensure function runs and returns a DataFrame
    df = aggregate_troops_by_period(
        gdf, period="month", date_field="date", troops_field="french_troops"
    )
    assert hasattr(df, "index")
    # index should be non-empty if data has dates
    assert len(df.index) >= 1
