"""LLM configuration loader."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from loguru import logger


class LLMConfigLoader:
    """Load and manage LLM configuration."""

    def __init__(self, config_path: str = "config/llm.yaml"):
        """Initialize config loader.

        Args:
            config_path: Path to LLM config file
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

            logger.info(f"Loaded LLM config from {self.config_path}")
            return self._config

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "default_model": "qwen-max",
            "models": {
                "qwen-max": {
                    "enabled": True,
                    "provider": "dashscope",
                    "model_name": "qwen-max",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "top_p": 0.9,
                }
            },
            "settings": {
                "timeout": 60,
                "max_retries": 3,
                "retry_delay": 2,
                "stream": True,
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
            model_name = config.get("default_model", "qwen-max")

        models = config.get("models", {})
        return models.get(model_name, {})

    def get_settings(self) -> Dict[str, Any]:
        """Get global settings.

        Returns:
            Settings dictionary
        """
        config = self.load()
        return config.get("settings", {})
