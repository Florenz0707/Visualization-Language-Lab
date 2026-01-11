"""Base TTS provider interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize TTS provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.sample_rate = config.get("sample_rate", 24000)

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the TTS model/service.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def generate_audio(self, text: str, output_path: Path, **kwargs) -> bool:
        """Generate audio from text.

        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file
            **kwargs: Additional provider-specific parameters

        Returns:
            True if generation successful, False otherwise
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name for directory organization.

        Returns:
            Model name string (e.g., 'kokoro', 'edge_tts')
        """
        pass

    def is_available(self) -> bool:
        """Check if provider is available and enabled.

        Returns:
            True if provider can be used, False otherwise
        """
        return self.enabled
