#!/usr/bin/env python3
"""Test proxy configuration for HuggingFace access.

This script tests if the proxy is correctly configured and can access HuggingFace.

Usage:
    uv run scripts/test_proxy.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from loguru import logger


def test_proxy():
    """Test proxy configuration."""
    import requests

    # Get proxy from environment
    proxy = os.getenv("PROXY")

    if not proxy:
        logger.warning("No PROXY environment variable set")
        logger.info("Add PROXY=http://127.0.0.1:7077 to your .env file")
        return False

    logger.info(f"Testing proxy: {proxy}")

    # Set up proxies
    proxies = {"http": proxy, "https": proxy}

    # Test connection to HuggingFace
    try:
        logger.info("Testing connection to HuggingFace...")
        response = requests.get("https://huggingface.co", proxies=proxies, timeout=10)

        if response.status_code == 200:
            logger.success("✓ Successfully connected to HuggingFace via proxy")
            return True
        else:
            logger.warning(f"Connected but got status code: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"✗ Failed to connect to HuggingFace: {e}")
        logger.info("Please check:")
        logger.info("  1. Proxy is running (e.g., Clash, V2Ray)")
        logger.info("  2. Proxy address is correct in .env")
        logger.info("  3. Firewall settings")
        return False


def main():
    """Main function."""
    logger.info("=== Proxy Configuration Test ===")

    # Load .env file
    from src.main import _load_dotenv_from_repo_root

    _load_dotenv_from_repo_root()

    # Test proxy
    success = test_proxy()

    if success:
        logger.success("\n✓ Proxy configuration is working correctly!")
        logger.info("You can now run: uv run scripts/generate_tts_audio.py")
    else:
        logger.error("\n✗ Proxy configuration test failed")
        logger.info("Please fix the issues above before generating TTS audio")
        sys.exit(1)


if __name__ == "__main__":
    main()
