import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure repository root is on sys.path so `import src` works
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
