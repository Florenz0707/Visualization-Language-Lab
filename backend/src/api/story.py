from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from src.services.data_loader import load_json
from src.services.tts.config_loader import TTSConfigLoader

router = APIRouter()


@router.get("/story/outline")
async def get_story_outline(
    chapter_id: Optional[int] = Query(
        None, description="Optional chapter ID to get specific chapter"
    ),
):
    """Return story outline with chapters for Story Mode.

    Returns all chapters if no chapter_id is provided, or a specific chapter if chapter_id is given.
    Each chapter contains:
    - id: Chapter identifier
    - title: Chapter title
    - date: Historical date (YYYY-MM-DD)
    - event_ids: List of related event IDs
    - camera: Camera parameters (center coordinates, zoom, pitch, bearing)
    - narrative: Historical background text (200-300 words)
    - image: Image source attribution
    """
    try:
        data = load_json("story/outline/chapters.json")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    chapters = data.get("chapters", [])

    if chapter_id is not None:
        # Filter for specific chapter
        chapter = next((c for c in chapters if c.get("id") == chapter_id), None)
        if not chapter:
            raise HTTPException(
                status_code=404, detail=f"Chapter {chapter_id} not found"
            )
        return {"chapter": chapter}

    # Return all chapters
    return {
        "title": data.get("title", "Napoleon's 1812 Russian Campaign"),
        "description": data.get("description", ""),
        "chapters": chapters,
    }


@router.get("/story/tts/{chapter_id}")
async def get_chapter_audio(
    chapter_id: int,
    model: Optional[str] = Query(None, description="TTS model name (default: kokoro)"),
):
    """Return TTS audio file for a specific chapter.

    Args:
        chapter_id: Chapter ID to get audio for
        model: TTS model name (optional, defaults to configured default)

    Returns:
        Audio file (WAV format) for the chapter narrative
    """
    try:
        # Get project root and config
        project_root = Path(__file__).resolve().parent.parent.parent
        config_loader = TTSConfigLoader()

        # Determine model name
        if model is None:
            config = config_loader.load()
            model = config.get("default_model", "kokoro")

        # Get model-specific directory
        tts_dir = project_root / config_loader.get_output_dir(model)
        audio_path = tts_dir / f"{chapter_id}.wav"

        # Check if audio file exists
        if not audio_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Audio file for chapter {chapter_id} not found (model: {model}). "
                "TTS generation may still be in progress.",
            )

        # Return audio file
        return FileResponse(
            path=str(audio_path),
            media_type="audio/wav",
            filename=f"chapter_{chapter_id}_{model}.wav",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
