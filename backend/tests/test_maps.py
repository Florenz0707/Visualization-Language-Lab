"""
测试地图数据API端点
"""
import pytest


def test_get_map_countries(client):
    """测试获取国家地图数据"""
    r = client.get("/api/maps/countries")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert isinstance(data.get("features"), list)
    assert len(data.get("features")) >= 1


def test_get_map_with_bbox(client):
    """测试bbox过滤"""
    # 获取全部数据
    r_all = client.get("/api/maps/cities_major")
    total = len(r_all.json().get("features", []))

    # 使用bbox过滤
    r = client.get("/api/maps/cities_major?bbox=20,50,40,60")
    assert r.status_code == 200
    data = r.json()
    filtered_count = len(data.get("features", []))
    assert filtered_count <= total


def test_get_map_with_projection(client):
    """测试投影转换"""
    r = client.get("/api/maps/cities_major?projection=webmercator")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"


def test_get_map_with_simplify(client):
    """测试几何简化"""
    r = client.get("/api/maps/rivers?simplify=true&tolerance=0.01")
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
    assert len(data.get("features", [])) >= 1


def test_get_map_invalid_type(client):
    """测试无效的地图类型"""
    r = client.get("/api/maps/invalid_type")
    assert r.status_code == 400


def test_get_map_invalid_bbox(client):
    """测试无效的bbox格式"""
    r = client.get("/api/maps/cities?bbox=invalid")
    assert r.status_code == 400


def test_get_map_combined_params(client):
    """测试组合参数"""
    r = client.get(
        "/api/maps/cities_major?bbox=20,50,40,60&projection=lambert&simplify=true&tolerance=0.005"
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
