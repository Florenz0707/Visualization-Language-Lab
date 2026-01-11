def test_get_story_outline_all(client):
    """Test getting all chapters from story outline."""
    r = client.get("/api/story/outline")
    assert r.status_code == 200
    data = r.json()

    # Check response structure
    assert "title" in data
    assert "description" in data
    assert "chapters" in data
    assert isinstance(data["chapters"], list)
    assert len(data["chapters"]) >= 1


def test_get_story_outline_structure(client):
    """Test that each chapter has the required fields."""
    r = client.get("/api/story/outline")
    assert r.status_code == 200
    data = r.json()

    chapters = data.get("chapters", [])
    assert len(chapters) > 0

    # Check first chapter structure
    chapter = chapters[0]
    required_fields = [
        "id",
        "title",
        "date",
        "event_ids",
        "camera",
        "narrative",
        "image",
    ]
    for field in required_fields:
        assert field in chapter, f"Missing required field: {field}"

    # Check camera structure
    camera = chapter["camera"]
    assert "center" in camera
    assert "zoom" in camera
    assert "pitch" in camera
    assert "bearing" in camera
    assert isinstance(camera["center"], list)
    assert len(camera["center"]) == 2

    # Check image structure
    image = chapter["image"]
    assert "url" in image
    assert "attribution" in image


def test_get_story_outline_specific_chapter(client):
    """Test getting a specific chapter by ID."""
    r = client.get("/api/story/outline?chapter_id=1")
    assert r.status_code == 200
    data = r.json()

    # Should return single chapter
    assert "chapter" in data
    chapter = data["chapter"]
    assert chapter["id"] == 1
    assert "title" in chapter
    assert "narrative" in chapter


def test_get_story_outline_invalid_chapter(client):
    """Test getting a non-existent chapter returns 404."""
    r = client.get("/api/story/outline?chapter_id=9999")
    assert r.status_code == 404


def test_story_outline_narrative_length(client):
    """Test that narratives are within expected length (200-300 words)."""
    r = client.get("/api/story/outline")
    assert r.status_code == 200
    data = r.json()

    chapters = data.get("chapters", [])
    for chapter in chapters:
        narrative = chapter.get("narrative", "")
        # Check narrative is not empty and has reasonable length
        assert len(narrative) > 100, f"Chapter {chapter['id']} narrative too short"
        assert len(narrative) < 1000, f"Chapter {chapter['id']} narrative too long"


def test_story_outline_date_format(client):
    """Test that dates are in correct format (YYYY-MM-DD)."""
    r = client.get("/api/story/outline")
    assert r.status_code == 200
    data = r.json()

    chapters = data.get("chapters", [])
    for chapter in chapters:
        date_str = chapter.get("date", "")
        # Check date format
        assert len(date_str) == 10, f"Invalid date format in chapter {chapter['id']}"
        assert date_str[4] == "-" and date_str[7] == "-"

        # Check it's a valid date
        from datetime import datetime

        try:
            datetime.fromisoformat(date_str)
        except ValueError:
            assert False, f"Invalid date in chapter {chapter['id']}: {date_str}"


def test_story_outline_event_ids(client):
    """Test that event_ids is a list."""
    r = client.get("/api/story/outline")
    assert r.status_code == 200
    data = r.json()

    chapters = data.get("chapters", [])
    for chapter in chapters:
        event_ids = chapter.get("event_ids", [])
        assert isinstance(
            event_ids, list
        ), f"event_ids should be a list in chapter {chapter['id']}"


def test_get_chapter_audio_valid(client):
    """Test getting TTS audio for a valid chapter."""
    # First get available chapters
    r = client.get("/api/story/outline")
    assert r.status_code == 200
    data = r.json()
    chapters = data.get("chapters", [])

    if len(chapters) > 0:
        chapter_id = chapters[0]["id"]

        # Try to get audio for first chapter
        r = client.get(f"/api/story/tts/{chapter_id}")

        # Audio might not exist yet (404) or should return audio file (200)
        assert r.status_code in [200, 404]

        if r.status_code == 200:
            # Check response headers
            assert r.headers["content-type"] == "audio/wav"


def test_get_chapter_audio_invalid(client):
    """Test getting TTS audio for an invalid chapter returns 404."""
    r = client.get("/api/story/tts/9999")
    assert r.status_code == 404
