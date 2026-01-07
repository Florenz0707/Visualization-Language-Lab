import os
import sys
from pathlib import Path

# ensure imports work
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.main import app


def test_flows_endpoint_basic():
    client = TestClient(app)
    resp = client.get("/api/flows")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("type") == "FeatureCollection"
    assert isinstance(data.get("features"), list)
    if data["features"]:
        f = data["features"][0]
        assert f["geometry"]["type"] == "LineString"
        coords = f["geometry"]["coordinates"]
        assert len(coords) == 2
        assert "unit" in f["properties"]


def test_flows_simplify_flag():
    client = TestClient(app)
    r1 = client.get("/api/flows?simplify=true&threshold=0.5")
    r2 = client.get("/api/flows?simplify=false")
    assert r1.status_code == 200 and r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    # structure should be same length
    assert len(d1.get("features", [])) == len(d2.get("features", []))
