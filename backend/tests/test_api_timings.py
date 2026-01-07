"""
API timing test.

Usage:
  TIMING_ITERATIONS=50 TIMING_OUTPUT=tests/api_timings.json uv run pytest -q tests/test_api_timings.py

This test will perform N requests to a set of endpoints using FastAPI TestClient,
collect per-request timings, compute summary statistics and dump the results
to a JSON file specified by TIMING_OUTPUT (default: tests/api_timings.json).
"""
import json
import os
import statistics
import sys
import time
from pathlib import Path

# ensure project imports work
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.main import app

ENDPOINTS = [
    ("/", "root"),
    ("/api/movements", "movements"),
    # ("/api/territories", "territories"),
    # ("/api/terrain/contours", "terrain_contours"),
]


def profile_endpoints(client: TestClient, iterations: int):
    results = {}
    for path, name in ENDPOINTS:
        # warm-up
        try:
            client.get(path)
        except Exception:
            pass

        timings = []
        statuses = []
        for i in range(iterations):
            t0 = time.perf_counter()
            try:
                resp = client.get(path)
                dt = time.perf_counter() - t0
                timings.append(dt)
                statuses.append(resp.status_code)
            except Exception as e:
                # record failure and continue
                timings.append(None)
                statuses.append(str(e))

        # compute stats only for successful timings
        success_timings = [t for t in timings if t is not None]
        timings_sorted = sorted(success_timings)
        stats = {
            "count": len(timings),
            "succeeded": len(success_timings),
            "min": min(success_timings) if success_timings else None,
            "max": max(success_timings) if success_timings else None,
            "mean": statistics.mean(success_timings) if success_timings else None,
            "median": statistics.median(success_timings) if success_timings else None,
            "p50": statistics.median(success_timings) if success_timings else None,
            "p90": timings_sorted[int(len(success_timings) * 0.9) - 1]
            if success_timings
            else None,
            "p95": timings_sorted[int(len(success_timings) * 0.95) - 1]
            if success_timings
            else None,
            "p99": timings_sorted[int(len(success_timings) * 0.99) - 1]
            if success_timings
            else None,
            "stdev": statistics.pstdev(success_timings) if success_timings else None,
        }

        results[name] = {
            "path": path,
            "timings": timings,
            "statuses": statuses,
            "stats": stats,
        }

    return results


def write_results(out_path: str, payload: dict) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_api_timings_and_write_file():
    iterations = int(os.getenv("TIMING_ITERATIONS", "1"))
    out = os.getenv("TIMING_OUTPUT", "tests/api_timings.json")

    client = TestClient(app)
    results = profile_endpoints(client, iterations)

    # basic sanity: at least one successful response per endpoint
    for name, data in results.items():
        succeeded = [s for s in data["statuses"] if s == 200]
        assert (
            len(succeeded) >= 1
        ), f"No successful (200) responses for {name}: {set(data['statuses'])}"

    write_results(out, {"iterations": iterations, "results": results})

    print(f"Wrote timing results to {out}")
