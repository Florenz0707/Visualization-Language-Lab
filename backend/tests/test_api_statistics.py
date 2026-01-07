from datetime import date

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_statistics_troops_endpoint():
    resp = client.get(
        "/api/statistics/troops?start=1812-06-01&end=1812-12-31&period=month"
    )
    assert resp.status_code == 200
    j = resp.json()
    assert "french" in j and "russian" in j
    assert isinstance(j["french"], list)
    # lists may be empty on minimal data, but should be present
    assert isinstance(j["russian"], list)
