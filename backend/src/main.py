import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.api.events import router as events_router
from src.api.movements import router as movements_router
from src.api.terrain import router as terrain_router
from src.api.territories import router as territories_router

app = FastAPI(title="1812 Visualization Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure GZip middleware; minimum size can be tuned via GZIP_MIN_SIZE env var
try:
    gzip_min = int(os.getenv("GZIP_MIN_SIZE", "1000"))
except Exception:
    gzip_min = 1000
app.add_middleware(GZipMiddleware, minimum_size=gzip_min)

app.include_router(events_router, prefix="/api")
app.include_router(movements_router, prefix="/api")
app.include_router(territories_router, prefix="/api")
app.include_router(terrain_router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok", "service": "1812 Visualization Backend"}
