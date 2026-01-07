from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_movements_simplify_and_bundling():
    # Request simplified movements and bundling metadata
    r = client.get("/api/movements?simplify=true&tolerance=0.001&bundling=true")
    assert r.status_code == 200
    j = r.json()
    assert "features" in j
    assert isinstance(j.get("features"), list)
    # bundling key should be present and aggregated (dict by unit)
    assert "bundling" in j
    bund = j.get("bundling")
    assert isinstance(bund, dict)
    # if bundling has entries, each entry should have aggregated metrics
    for unit, meta in bund.items():
        assert "weight" in meta and "count" in meta
        assert "start" in meta and "end" in meta and "angle" in meta


def test_movements_grouping():
    r = client.get("/api/movements?group=true")
    assert r.status_code == 200
    j = r.json()
    assert "groups" in j
    groups = j.get("groups")
    assert isinstance(groups, dict)
