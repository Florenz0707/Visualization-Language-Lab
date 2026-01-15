"""Example script demonstrating LLM service usage."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Load .env file before importing any modules
def load_dotenv():
    """Load environment variables from .env file."""
    dotenv_path = Path(__file__).parent.parent / ".env"
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


def example_basic_chat():
    """Basic chat example."""
    print("=== Basic Chat Example ===\n")

    factory = LLMFactory()
    provider = factory.get_provider()

    if not provider:
        print("Failed to initialize LLM provider")
        return

    messages = [
        {"role": "system", "content": "你是一位精通1812年拿破仑俄法战争的历史学家。"},
        {"role": "user", "content": "请简要介绍1812年拿破仑远征俄国的背景。"},
    ]

    try:
        response = provider.chat(messages)
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_streaming_chat():
    """Streaming chat example."""
    print("=== Streaming Chat Example ===\n")

    factory = LLMFactory()
    provider = factory.get_provider()

    if not provider:
        print("Failed to initialize LLM provider")
        return

    messages = [{"role": "user", "content": "用一句话描述拿破仑战争的结局。"}]

    try:
        print("Response: ", end="", flush=True)
        for chunk in provider.chat(messages, stream=True):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\nError: {e}\n")


def example_different_models():
    """Example using different models."""
    print("=== Different Models Example ===\n")

    factory = LLMFactory()

    # List available models
    available_models = factory.get_available_models()
    print(f"Available models: {available_models}\n")

    # Try different models
    for model_name in ["qwen-max", "qwen-plus"]:
        print(f"--- Using {model_name} ---")
        provider = factory.get_provider(model_name)

        if not provider:
            print(f"Failed to initialize {model_name}\n")
            continue

        messages = [{"role": "user", "content": "用10个字概括拿破仑战争。"}]

        try:
            response = provider.chat(messages)
            print(f"Response: {response}\n")
        except Exception as e:
            print(f"Error: {e}\n")


def example_custom_parameters():
    """Example with custom parameters."""
    print("=== Custom Parameters Example ===\n")

    factory = LLMFactory()
    provider = factory.get_provider()

    if not provider:
        print("Failed to initialize LLM provider")
        return

    messages = [{"role": "user", "content": "列举3个拿破仑战争的关键战役。"}]

    try:
        response = provider.chat(messages, temperature=0.5, max_tokens=500, top_p=0.8)
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == "__main__":
    print("LLM Service Examples\n")
    print("=" * 50 + "\n")

    # Run examples
    example_basic_chat()
    example_streaming_chat()
    example_different_models()
    example_custom_parameters()

    print("=" * 50)
    print("Examples completed!")
