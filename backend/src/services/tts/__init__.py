"""TTS service package with factory pattern support."""

from .base import BaseTTSProvider
from .factory import TTSFactory

__all__ = ["TTSFactory", "BaseTTSProvider"]
