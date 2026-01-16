"""Test script to verify LLM environment variable loading."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import main to trigger .env loading
import src.main

print("=== Environment Variable Check ===\n")

# Check if DASHSCOPE_API_KEY is loaded
api_key = os.getenv("DASHSCOPE_API_KEY")
if api_key:
    # Mask the API key for security
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"✓ DASHSCOPE_API_KEY is loaded: {masked_key}")
else:
    print("✗ DASHSCOPE_API_KEY is NOT loaded")
    print("  Please check your .env file")

print("\n=== LLM Service Initialization Test ===\n")

try:
    from src.services.llm import LLMFactory

    factory = LLMFactory()
    provider = factory.get_provider()

    if provider:
        print(f"✓ LLM Factory initialized successfully")
        print(f"  Provider: {provider.get_provider_name()}")
        print(f"  Model: {provider.model_name}")
        print(f"  Available models: {factory.get_available_models()}")
    else:
        print("✗ Failed to initialize LLM provider")

except Exception as e:
    print(f"✗ Error initializing LLM service: {e}")

print("\n" + "=" * 50)
