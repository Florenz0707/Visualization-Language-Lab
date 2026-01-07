def test_get_contours(client):
    r = client.get("/api/terrain/contours")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert isinstance(data.get("features"), list)
    assert len(data.get("features")) > 0


def test_get_dem_success(client):
    # use a valid bbox within project area
    r = client.get("/api/terrain/dem?bbox=20,50,45,60&resolution=512")
    assert r.status_code == 200
    data = r.json()
    assert data.get("format") == "png"
    img_b64 = data.get("image_base64")
    assert isinstance(img_b64, str)
    assert len(img_b64) > 100


def test_get_dem_bad_bbox(client):
    r = client.get("/api/terrain/dem?bbox=invalid&resolution=256")
    assert r.status_code == 400
    assert "bbox" in r.json().get("detail", "")
