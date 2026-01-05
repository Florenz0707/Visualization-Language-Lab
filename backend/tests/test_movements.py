def test_get_movements(client):
    r = client.get("/api/movements")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert isinstance(data.get("features"), list)
    for f in data.get("features", []):
        geom = f.get("geometry", {})
        assert geom.get("type") in ("LineString", "MultiLineString")
