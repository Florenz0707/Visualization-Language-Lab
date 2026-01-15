"""LLM factory for creating provider instances."""

from typing import Dict, Optional

from loguru import logger

from .base import BaseLLMProvider
from .config_loader import LLMConfigLoader
from .dashscope_provider import DashScopeLLMProvider
from .deepseek_provider import DeepSeekLLMProvider


class LLMFactory:
    """Factory for creating LLM provider instances."""

    _providers = {
        "dashscope": DashScopeLLMProvider,
        "deepseek": DeepSeekLLMProvider,
    }

    def __init__(self, config_path: str = "config/llm.yaml"):
        """Initialize LLM factory.

        Args:
            config_path: Path to LLM config file
        """
        self.config_loader = LLMConfigLoader(config_path)
        self._instances: Dict[str, BaseLLMProvider] = {}

    @classmethod
    def register_provider(cls, name: str, provider_class):
        """Register a new LLM provider.

        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered LLM provider: {name}")

    def get_provider(self, model_name: str = None) -> Optional[BaseLLMProvider]:
        """Get LLM provider instance.

        Args:
            model_name: Model name, or None for default

        Returns:
            LLM provider instance or None
        """
        # Use default if not specified
        if model_name is None:
            config = self.config_loader.load()
            model_name = config.get("default_model", "qwen-max")

        # Return cached instance if exists
        if model_name in self._instances:
            return self._instances[model_name]

        # Load model config
        model_config = self.config_loader.get_model_config(model_name)
        if not model_config:
            logger.error(f"Model config not found: {model_name}")
            return None

        # Check if enabled
        if not model_config.get("enabled", True):
            logger.warning(f"Model disabled: {model_name}")
            return None

        # Get provider class
        provider_type = model_config.get("provider", "dashscope")
        provider_class = self._providers.get(provider_type)

        if not provider_class:
            logger.error(f"Provider not found: {provider_type}")
            return None

        # Create and cache instance
        try:
            provider = provider_class(model_config)
            if provider.initialize():
                self._instances[model_name] = provider
                logger.info(f"Created LLM provider: {model_name}")
                return provider
            else:
                logger.error(f"Failed to initialize provider: {model_name}")
                return None
        except Exception as e:
            logger.error(f"Failed to create provider {model_name}: {e}")
            return None

    def get_available_models(self):
        """Get list of available model names."""
        config = self.config_loader.load()
        models = config.get("models", {})
        return [name for name, cfg in models.items() if cfg.get("enabled", True)]
