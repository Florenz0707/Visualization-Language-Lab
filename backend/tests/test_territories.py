def test_get_territories_default(client):
    r = client.get("/api/territories")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert isinstance(data.get("features"), list)
    for f in data.get("features", []):
        geom = f.get("geometry", {})
        assert geom.get("type") in ("Polygon", "MultiPolygon")


def test_get_territories_projection_lambert(client):
    # Request territories in Lambert projection and verify coordinate magnitudes
    r = client.get("/api/territories?projection=lambert")
    assert r.status_code == 200
    data = r.json()
    feats = data.get("features", [])
    # may be empty in LIGHTWEIGHT_MODE; otherwise validate projected coords
    if not feats:
        return
    for f in feats:
        geom = f.get("geometry", {})
        assert geom.get("type") in ("Polygon", "MultiPolygon")
        coords = []
        if geom.get("type") == "Polygon":
            coords = geom.get("coordinates", [[]])[0]
        elif geom.get("type") == "MultiPolygon":
            coords = geom.get("coordinates", [[[]]])[0][0]
        if coords:
            first = coords[0]
            assert isinstance(first, list) and len(first) >= 2
            # Lambert projected coordinates should be in meter-range (large magnitude)
            assert abs(first[0]) > 1e4 or abs(first[1]) > 1e4
