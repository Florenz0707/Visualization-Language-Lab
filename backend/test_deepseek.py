"""Test script for DeepSeek provider."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


# Load .env file
def load_dotenv():
    """Load environment variables from .env file."""
    dotenv_path = Path(__file__).parent / ".env"
    if not dotenv_path.exists():
        print(f"Warning: .env file not found at {dotenv_path}")
        return

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


load_dotenv()

from src.services.llm import LLMFactory

print("=== DeepSeek Provider Test ===\n")

# Check API key
api_key = os.getenv("DEEPSEEK_API_KEY")
if api_key:
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"✓ DEEPSEEK_API_KEY loaded: {masked_key}\n")
else:
    print("✗ DEEPSEEK_API_KEY not found\n")
    sys.exit(1)

# Test 1: Initialize DeepSeek provider
print("--- Test 1: Initialize Provider ---")
try:
    factory = LLMFactory()
    provider = factory.get_provider("deepseek-chat")

    if provider:
        print(f"✓ Provider initialized successfully")
        print(f"  Provider: {provider.get_provider_name()}")
        print(f"  Model: {provider.model_name}\n")
    else:
        print("✗ Failed to initialize provider\n")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}\n")
    sys.exit(1)

# Test 2: Basic chat
print("--- Test 2: Basic Chat ---")
try:
    messages = [{"role": "user", "content": "用一句话介绍DeepSeek。"}]

    response = provider.chat(messages)
    print(f"Response: {response}\n")
except Exception as e:
    print(f"✗ Error: {e}\n")
    sys.exit(1)

# Test 3: Streaming chat
print("--- Test 3: Streaming Chat ---")
try:
    messages = [{"role": "user", "content": "列举3个AI的应用场景。"}]

    print("Response: ", end="", flush=True)
    for chunk in provider.chat(messages, stream=True):
        print(chunk, end="", flush=True)
    print("\n")
except Exception as e:
    print(f"\n✗ Error: {e}\n")
    sys.exit(1)

print("=" * 50)
print("All tests passed! ✓")
