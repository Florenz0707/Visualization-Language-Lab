"""Kokoro TTS provider implementation."""

import os
from pathlib import Path
from typing import Any, Dict

import numpy as np
from loguru import logger

from .base import BaseTTSProvider


class KokoroTTSProvider(BaseTTSProvider):
    """Kokoro-82M TTS provider."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Kokoro TTS provider."""
        super().__init__(config)
        self.repo_id = config.get("repo_id", "hexgrad/Kokoro-82M")
        self.lang_code = config.get("lang_code", "z")
        self.voice = config.get("voice", "af_heart")
        self.speed = config.get("speed", 1.0)
        self._pipeline = None

    def initialize(self) -> bool:
        """Initialize Kokoro pipeline."""
        if self._pipeline is not None:
            return True

        try:
            from kokoro import KPipeline

            # Set up proxy if configured
            proxy = os.getenv("PROXY")
            if proxy:
                logger.info(f"Using proxy for HuggingFace: {proxy}")
                os.environ["HTTP_PROXY"] = proxy
                os.environ["HTTPS_PROXY"] = proxy
                os.environ["http_proxy"] = proxy
                os.environ["https_proxy"] = proxy

            logger.info(f"Loading Kokoro TTS pipeline (repo: {self.repo_id})...")

            self._pipeline = KPipeline(lang_code=self.lang_code, repo_id=self.repo_id)

            logger.info("Kokoro TTS pipeline loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load Kokoro pipeline: {e}")
            return False

    def generate_audio(self, text: str, output_path: Path, **kwargs) -> bool:
        """Generate audio using Kokoro TTS."""
        try:
            import soundfile as sf

            if not self.initialize():
                logger.warning("Kokoro pipeline not available")
                return False

            # Override config with kwargs if provided
            voice = kwargs.get("voice", self.voice)
            speed = kwargs.get("speed", self.speed)

            logger.info(f"Generating audio (length: {len(text)} chars)")

            # Split long Chinese text by sentences
            import re

            sentences = []

            # Split by Chinese punctuation
            parts = re.split(r"([。！？])", text)

            # Reconstruct sentences with punctuation
            full_sentences = []
            for i in range(0, len(parts), 2):
                if i < len(parts):
                    sent = parts[i]
                    if i + 1 < len(parts):
                        sent += parts[i + 1]
                    if sent.strip():
                        full_sentences.append(sent)

            logger.info(f"Found {len(full_sentences)} sentence(s) in text")

            # Generate audio for each sentence
            all_audio = []
            for sent_idx, sentence in enumerate(full_sentences):
                logger.info(
                    f"Processing sentence {sent_idx+1}/{len(full_sentences)}: {len(sentence)} chars"
                )

                generator = self._pipeline(sentence, voice=voice, speed=speed)

                for i, (gs, ps, audio) in enumerate(generator):
                    logger.info(
                        f"Sentence {sent_idx+1}, Segment {i}: {len(audio)} samples"
                    )
                    all_audio.append(audio)

            # Concatenate all audio
            if all_audio:
                full_audio = np.concatenate(all_audio)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                sf.write(str(output_path), full_audio, self.sample_rate)

                duration = len(full_audio) / self.sample_rate
                logger.info(
                    f"Saved: {output_path} ({duration:.2f}s, {len(all_audio)} segments)"
                )
                return True
            else:
                logger.warning("No audio generated")
                return False

        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            return False

    def get_model_name(self) -> str:
        """Get model name."""
        return "kokoro"
