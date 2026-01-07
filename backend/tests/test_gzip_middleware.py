import os
import sys
from pathlib import Path

# Ensure environment var is set before importing app so middleware uses it
os.environ.setdefault("GZIP_MIN_SIZE", "0")

# make project importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.main import app


def test_gzip_middleware_registered_with_config():
    # GZipMiddleware should be registered on the app and configured
    found = False
    for m in app.user_middleware:
        if getattr(m.cls, "__name__", "") == "GZipMiddleware":
            found = True
    assert found, "GZipMiddleware not registered on the FastAPI app"


def test_root_response_ok():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"
