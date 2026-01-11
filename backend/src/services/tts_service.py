"""Main TTS service using factory pattern."""

import json
from pathlib import Path
from typing import Optional

from loguru import logger

from .tts.config_loader import TTSConfigLoader
from .tts.factory import TTSFactory

# Global factory instance
_tts_factory: Optional[TTSFactory] = None


def get_tts_factory() -> TTSFactory:
    """Get or create TTS factory instance."""
    global _tts_factory

    if _tts_factory is None:
        _tts_factory = TTSFactory()

    return _tts_factory


def generate_audio(
    text: str, output_path: Path, model_name: str = None, **kwargs
) -> bool:
    """Generate audio using specified TTS model.

    Args:
        text: Text to convert to speech
        output_path: Path to save audio file
        model_name: Model name (None for default)
        **kwargs: Additional model-specific parameters

    Returns:
        True if successful, False otherwise
    """
    try:
        factory = get_tts_factory()
        provider = factory.get_provider(model_name)

        if provider is None:
            logger.error(f"Failed to get TTS provider: {model_name}")
            return False

        return provider.generate_audio(text, output_path, **kwargs)

    except Exception as e:
        logger.error(f"Failed to generate audio: {e}")
        return False


def check_and_generate_tts_files(
    chapters_json_path: Path, model_name: str = None, force_regenerate: bool = False
) -> dict[int, Path]:
    """Check and generate TTS files for all chapters.

    Args:
        chapters_json_path: Path to chapters.json
        model_name: Model name (None for default)
        force_regenerate: Force regenerate all files

    Returns:
        Dictionary mapping chapter_id to audio file path
    """
    try:
        # Get factory and provider
        factory = get_tts_factory()
        provider = factory.get_provider(model_name)

        if provider is None:
            logger.error("Failed to get TTS provider")
            return {}

        # Get output directory for this model
        config_loader = TTSConfigLoader()
        model_name_str = provider.get_model_name()
        tts_dir = config_loader.get_output_dir(model_name_str)

        logger.info(f"Using model: {model_name_str}")
        logger.info(f"Output directory: {tts_dir}")

        # Load chapters data
        with open(chapters_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chapters = data.get("chapters", [])
        audio_files = {}
        missing_count = 0

        # Check which files are missing
        for chapter in chapters:
            chapter_id = chapter.get("id")
            narrative = chapter.get("narrative", "")

            if not chapter_id or not narrative:
                logger.warning("Skipping chapter with missing id or narrative")
                continue

            audio_path = tts_dir / f"{chapter_id}.wav"
            audio_files[chapter_id] = audio_path

            if force_regenerate or not audio_path.exists():
                missing_count += 1

        logger.info(f"Found {missing_count} missing TTS audio files")

        # Generate missing files
        if missing_count > 0:
            logger.info("Generating missing audio files...")

            for chapter in chapters:
                chapter_id = chapter.get("id")
                narrative = chapter.get("narrative", "")

                if not chapter_id or not narrative:
                    continue

                audio_path = audio_files[chapter_id]

                if force_regenerate or not audio_path.exists():
                    logger.info(
                        f"Generating TTS for chapter {chapter_id}: "
                        f"{chapter.get('title', '')}"
                    )
                    success = provider.generate_audio(narrative, audio_path)

                    if not success:
                        logger.error(
                            f"Failed to generate audio for chapter {chapter_id}"
                        )
        else:
            logger.info("All TTS audio files already exist")

        return audio_files

    except Exception as e:
        logger.error(f"Failed to check/generate TTS files: {e}")
        return {}
