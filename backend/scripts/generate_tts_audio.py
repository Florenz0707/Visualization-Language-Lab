#!/usr/bin/env python3
"""Generate TTS audio files for story chapters.

This script generates text-to-speech audio files for all chapters in the story mode.
Audio files are saved to data/story/tts/ directory.

Usage:
    uv run scripts/generate_tts_audio.py [--force]

Options:
    --force    Regenerate all audio files even if they already exist
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Load .env file BEFORE importing other modules
from src.main import _load_dotenv_from_repo_root

_load_dotenv_from_repo_root()

from loguru import logger
from src.services.tts_service import check_and_generate_tts_files


def main():
    """Main function to generate TTS audio files."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Generate TTS audio files for story chapters"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate all audio files even if they already exist",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="TTS model to use (default: from config)",
    )
    args = parser.parse_args()

    # Check and display proxy configuration
    proxy = os.getenv("PROXY")
    if proxy:
        logger.info(f"Proxy configured: {proxy}")
    else:
        logger.info("Add PROXY=http://127.0.0.1:7077 to .env if needed")

    # Set up paths
    chapters_json = project_root / "data" / "story" / "outline" / "chapters.json"

    # Check if chapters.json exists
    if not chapters_json.exists():
        logger.error(f"Chapters file not found: {chapters_json}")
        logger.error("Please ensure the story data is available.")
        sys.exit(1)

    # Generate TTS audio files
    logger.info("Starting TTS audio generation...")
    logger.info(f"Chapters file: {chapters_json}")
    logger.info(f"Model: {args.model or 'default'}")
    logger.info(f"Force regenerate: {args.force}")

    audio_files = check_and_generate_tts_files(
        chapters_json, model_name=args.model, force_regenerate=args.force
    )

    if audio_files:
        logger.success(f"Successfully processed {len(audio_files)} chapters")
    else:
        logger.warning("No audio files were generated")


if __name__ == "__main__":
    main()
