"""TTS configuration loader."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from loguru import logger


class TTSConfigLoader:
    """Load and manage TTS configuration."""

    def __init__(self, config_path: str = "config/tts.yaml"):
        """Initialize config loader.

        Args:
            config_path: Path to TTS config file
        """
        self.config_path = Path(config_path)
        self._config = None

    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        if self._config is not None:
            return self._config

        try:
            if not self.config_path.exists():
                logger.error(f"Config file not found: {self.config_path}")
                return self._get_default_config()

            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)

            logger.info(f"Loaded TTS config from {self.config_path}")
            return self._config

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "default_model": "kokoro",
            "models": {
                "kokoro": {
                    "enabled": True,
                    "provider": "kokoro",
                    "repo_id": "hexgrad/Kokoro-82M",
                    "lang_code": "z",
                    "voice": "af_heart",
                    "sample_rate": 24000,
                    "speed": 1.0,
                }
            },
            "settings": {
                "use_proxy": True,
                "output_dir": "data/story/tts/{model}",
                "max_retries": 3,
                "retry_delay": 5,
            },
        }

    def get_model_config(self, model_name: str = None) -> Dict[str, Any]:
        """Get configuration for specific model.

        Args:
            model_name: Model name, or None for default

        Returns:
            Model configuration dictionary
        """
        config = self.load()

        if model_name is None:
            model_name = config.get("default_model", "kokoro")

        models = config.get("models", {})
        return models.get(model_name, {})

    def get_output_dir(self, model_name: str) -> Path:
        """Get output directory for model.

        Args:
            model_name: Model name

        Returns:
            Output directory path
        """
        config = self.load()
        settings = config.get("settings", {})
        pattern = settings.get("output_dir", "data/story/tts/{model}")
        return Path(pattern.format(model=model_name))
