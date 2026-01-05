from datetime import datetime


def test_get_events_all(client):
    r = client.get("/api/events")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert isinstance(data.get("features"), list)
    assert len(data.get("features")) >= 1


def test_get_events_filter(client):
    r_all = client.get("/api/events")
    total = len(r_all.json().get("features", []))
    r = client.get("/api/events?start=1812-09-01&end=1812-10-01")
    assert r.status_code == 200
    data = r.json()
    assert len(data.get("features", [])) <= total
    for f in data.get("features", []):
        d = f.get("properties", {}).get("date")
        if d:
            dt = datetime.fromisoformat(d).date()
            assert dt >= datetime.fromisoformat("1812-09-01").date()
            assert dt <= datetime.fromisoformat("1812-10-01").date()
