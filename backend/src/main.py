from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.events import router as events_router

app = FastAPI(title="1812 Visualization Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok", "service": "1812 Visualization Backend"}
