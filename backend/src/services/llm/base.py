"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.model_name = config.get("model_name", "")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        self.top_p = config.get("top_p", 0.9)

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the LLM service.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def chat(
        self, messages: list[Dict[str, str]], stream: bool = False, **kwargs
    ) -> str | Generator[str, None, None]:
        """Send chat messages and get response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Response text or generator for streaming
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name string (e.g., 'dashscope', 'openai')
        """
        pass

    def is_available(self) -> bool:
        """Check if provider is available and enabled.

        Returns:
            True if provider can be used, False otherwise
        """
        return self.enabled
