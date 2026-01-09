from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from src.services.data_loader import load_json

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
        data = load_json("story/outline/example.json")
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
