"""DeepSeek LLM provider implementation."""

import os
from typing import Any, Dict, Generator

from loguru import logger
from openai import OpenAI

from .base import BaseLLMProvider


class DeepSeekLLMProvider(BaseLLMProvider):
    """DeepSeek LLM provider using OpenAI-compatible API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize DeepSeek provider.

        Args:
            config: Provider configuration dictionary
        """
        super().__init__(config)
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com"
        self.client = None

    def initialize(self) -> bool:
        """Initialize the DeepSeek client.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("DEEPSEEK_API_KEY not found in environment variables")
                return False

            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            logger.info(f"Initialized DeepSeek provider with model: {self.model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek provider: {e}")
            return False

    def chat(
        self, messages: list[Dict[str, str]], stream: bool = False, **kwargs
    ) -> str | Generator[str, None, None]:
        """Send chat messages and get response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Response text or generator for streaming
        """
        if not self.client:
            if not self.initialize():
                raise RuntimeError("Failed to initialize DeepSeek client")

        # Merge config with kwargs
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "top_p": kwargs.get("top_p", self.top_p),
            "stream": stream,
        }

        if stream:
            params["stream_options"] = {"include_usage": True}

        try:
            completion = self.client.chat.completions.create(**params)

            if stream:
                return self._handle_stream(completion)
            else:
                return completion.choices[0].message.content

        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            raise

    def _handle_stream(self, completion) -> Generator[str, None, None]:
        """Handle streaming response.

        Args:
            completion: Streaming completion object

        Yields:
            Response content chunks
        """
        for chunk in completion:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Handle regular content
            if hasattr(delta, "content") and delta.content:
                yield delta.content

    def get_provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name string
        """
        return "deepseek"
