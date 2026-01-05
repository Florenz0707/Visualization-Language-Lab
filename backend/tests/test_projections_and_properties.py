def test_events_projection_webmercator(client):
    r = client.get("/api/events?projection=webmercator")
    assert r.status_code == 200
    data = r.json()
    feats = data.get("features", [])
    assert feats, "no features returned"
    # first feature should be a Point and coordinates in meters (large magnitude)
    geom = feats[0].get("geometry", {})
    assert geom.get("type") == "Point"
    coords = geom.get("coordinates")
    assert isinstance(coords, list) and len(coords) == 2
    # web mercator x/y expected magnitude >> 1e5 for Europe
    assert abs(coords[0]) > 1e5 or abs(coords[1]) > 1e5


def test_movements_projection_lambert(client):
    r = client.get("/api/movements?projection=lambert")
    assert r.status_code == 200
    data = r.json()
    feats = data.get("features", [])
    assert feats
    for f in feats:
        geom = f.get("geometry", {})
        assert geom.get("type") in ("LineString", "MultiLineString")
        coords = geom.get("coordinates")
        # coordinates should be numbers (projected); check magnitude
        if isinstance(coords, list) and coords:
            first = coords[0]
            # inner coord may be [x,y]
            if isinstance(first, list) and len(first) >= 2:
                assert abs(first[0]) > 1e4 or abs(first[1]) > 1e4


def test_territories_properties(client):
    r = client.get("/api/territories")
    assert r.status_code == 200
    data = r.json()
    feats = data.get("features", [])
    assert feats
    for f in feats:
        props = f.get("properties", {})
        assert "faction" in props or "count" in props
        # count, if present, should be int-like
        if "count" in props:
            assert isinstance(props["count"], int)


def test_events_date_boundary(client):
    # Request a narrow window unlikely to include all events
    r = client.get("/api/events?start=1812-10-01&end=1812-10-31")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("features", []), list)
