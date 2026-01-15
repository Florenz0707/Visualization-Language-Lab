"""DashScope LLM provider implementation."""

import os
from typing import Any, Dict, Generator

from loguru import logger
from openai import OpenAI

from .base import BaseLLMProvider


class DashScopeLLMProvider(BaseLLMProvider):
    """DashScope (Aliyun) LLM provider using OpenAI-compatible API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize DashScope provider.

        Args:
            config: Provider configuration dictionary
        """
        super().__init__(config)
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = None
        self.enable_thinking = config.get("enable_thinking", False)

    def initialize(self) -> bool:
        """Initialize the DashScope client.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("DASHSCOPE_API_KEY not found in environment variables")
                return False

            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            logger.info(f"Initialized DashScope provider with model: {self.model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DashScope provider: {e}")
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
                raise RuntimeError("Failed to initialize DashScope client")

        # Merge config with kwargs
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "top_p": kwargs.get("top_p", self.top_p),
            "stream": stream,
        }

        # Add thinking mode for DeepSeek R1
        if self.enable_thinking:
            params["extra_body"] = {"enable_thinking": True}

        if stream:
            params["stream_options"] = {"include_usage": True}

        try:
            completion = self.client.chat.completions.create(**params)

            if stream:
                return self._handle_stream(completion)
            else:
                return completion.choices[0].message.content

        except Exception as e:
            logger.error(f"DashScope API call failed: {e}")
            raise

    def _handle_stream(self, completion) -> Generator[str, None, None]:
        """Handle streaming response.

        Args:
            completion: Streaming completion object

        Yields:
            Response content chunks
        """
        reasoning_content = ""
        answer_content = ""

        for chunk in completion:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Handle thinking content (DeepSeek R1)
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                reasoning_content += delta.reasoning_content
                logger.debug(f"Reasoning: {delta.reasoning_content}")

            # Handle regular content
            if hasattr(delta, "content") and delta.content:
                answer_content += delta.content
                yield delta.content

    def get_provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name string
        """
        return "dashscope"
