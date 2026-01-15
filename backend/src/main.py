import os
from pathlib import Path

from loguru import logger


def _load_dotenv_from_repo_root() -> None:
    """Best-effort load of a .env file from the repository root into os.environ.

    Does not overwrite existing environment variables.
    """
    try:
        here = Path(__file__).resolve().parent
        repo_root = here.parent
        dotenv = repo_root / ".env"
        if not dotenv.exists():
            return
        for raw in dotenv.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)
            logger.debug(f"Set Env : ({k} -> {v})")
    except Exception:
        return


_load_dotenv_from_repo_root()

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.api.events import router as events_router
from src.api.flows import router as flows_router
from src.api.maps import router as maps_router
from src.api.movements import router as movements_router
from src.api.statistics import router as statistics_router
from src.api.story import router as story_router
from src.api.temperature import router as temperature_router
from src.api.terrain import router as terrain_router
from src.api.territories import router as territories_router

app = FastAPI(title="1812 Visualization Backend")


@app.on_event("startup")
async def startup_event():
    """Check and generate TTS audio files on startup."""
    try:
        from src.services.tts_service import check_and_generate_tts_files

        # Get project root directory
        project_root = Path(__file__).resolve().parent.parent
        chapters_json = project_root / "data" / "story" / "outline" / "chapters.json"

        # Check if chapters.json exists
        if chapters_json.exists():
            logger.info("Checking TTS audio files...")
            check_and_generate_tts_files(chapters_json)
        else:
            logger.warning(f"Chapters file not found: {chapters_json}")
    except Exception as e:
        logger.error(f"Failed to initialize TTS: {e}")
        # Don't fail startup if TTS initialization fails
        pass


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure GZip middleware; minimum size can be tuned via GZIP_MIN_SIZE env var
try:
    gzip_min = int(os.getenv("GZIP_MIN_SIZE", "1000"))
except Exception:
    gzip_min = 1000
finally:
    app.add_middleware(GZipMiddleware, minimum_size=gzip_min)

app.include_router(events_router, prefix="/api")
app.include_router(movements_router, prefix="/api")
app.include_router(territories_router, prefix="/api")
app.include_router(terrain_router, prefix="/api")
app.include_router(flows_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")
app.include_router(story_router, prefix="/api")
app.include_router(maps_router, prefix="/api")
app.include_router(temperature_router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok", "service": "1812 Visualization Backend"}
