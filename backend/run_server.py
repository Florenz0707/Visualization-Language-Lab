"""Start the FastAPI app using environment HOST/PORT.

Usage:
  uv run python run_server.py

Environment variables:
  HOST (default: 127.0.0.1)
  PORT (default: 8000)
  RELOAD (true/1 to enable reload)
"""
import os
from pathlib import Path

import uvicorn


def load_dotenv(dotenv_path: str | Path) -> None:
    p = Path(dotenv_path)
    if not p.exists():
        return
    try:
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # do not override environment variables already set
            os.environ.setdefault(key, val)
    except Exception:
        # best-effort loader — ignore errors so server can still start
        return


def getenv_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


def main() -> None:
    # load .env from the repository root (same folder as this script)
    here = Path(__file__).resolve().parent
    dotenv = here.joinpath(".env")
    load_dotenv(dotenv)

    host = os.getenv("HOST", "127.0.0.1")
    port = getenv_int("PORT", 8000)
    reload = os.getenv("RELOAD", "false").lower() in ("1", "true", "yes")

    print(f"Starting uvicorn on {host}:{port} (reload={reload})")
    uvicorn.run("src.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
