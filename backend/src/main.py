from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app.include_router(events_router, prefix="/api")
app.include_router(movements_router, prefix="/api")
app.include_router(territories_router, prefix="/api")
app.include_router(terrain_router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok", "service": "1812 Visualization Backend"}
