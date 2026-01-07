import sys
from pathlib import Path

import pytest

# ensure src is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services import data_loader as dl


def test_load_geojson_cache_and_clear():
    dl.clear_caches()
    a = dl.load_geojson("events.geojson")
    b = dl.load_geojson("events.geojson")
    # cached object should be identical (same id)
    assert a is b

    dl.clear_caches()
    c = dl.load_geojson("events.geojson")
    assert c is not a


def test_gdf_cache_and_copy_and_clear():
    dl.clear_caches()
    # access internal cached loader
    g1 = dl._load_geojson_gdf_cached("events.geojson")
    g2 = dl._load_geojson_gdf_cached("events.geojson")
    assert g1 is g2

    # public API returns a copy
    public1 = dl.load_geojson_gdf("events.geojson")
    public2 = dl.load_geojson_gdf("events.geojson")
    assert public1.equals(public2)
    assert public1 is not g1

    dl.clear_caches()
    g3 = dl._load_geojson_gdf_cached("events.geojson")
    assert g3 is not g1


def test_reproject_cache_and_clear():
    dl.clear_caches()
    r1 = dl.reproject_geojson("events.geojson", "webmercator")
    r2 = dl.reproject_geojson("events.geojson", "webmercator")
    assert r1 is r2

    dl.clear_caches()
    r3 = dl.reproject_geojson("events.geojson", "webmercator")
    assert r3 is not r1
