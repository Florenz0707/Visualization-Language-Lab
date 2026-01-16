"""Test script for LLM API endpoint."""

import json

import requests

BASE_URL = "http://127.0.0.1:9000"

print("=== LLM API Endpoint Test ===\n")

# Test 1: Basic chat without system prompt
print("--- Test 1: Basic Chat ---")
try:
    response = requests.post(
        f"{BASE_URL}/api/llm/chat", json={"message": "用一句话介绍1812年拿破仑战争。"}, timeout=60
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Model: {data['model']}")
        print(f"✓ Response: {data['response']}\n")
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"  {response.text}\n")
except Exception as e:
    print(f"✗ Exception: {e}\n")

# Test 2: Chat with system prompt
print("--- Test 2: Chat with System Prompt ---")
try:
    response = requests.post(
        f"{BASE_URL}/api/llm/chat",
        json={
            "message": "分析法军在俄国遭遇的主要困难。",
            "system_prompt": "你是一位精通1812年拿破仑俄法战争的军事历史学家。",
        },
        timeout=60,
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Model: {data['model']}")
        print(f"✓ Response: {data['response']}\n")
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"  {response.text}\n")
except Exception as e:
    print(f"✗ Exception: {e}\n")
# Test 3: Error handling - empty message
print("--- Test 3: Error Handling (Empty Message) ---")
try:
    response = requests.post(
        f"{BASE_URL}/api/llm/chat", json={"message": ""}, timeout=60
    )

    if response.status_code == 422:
        print(f"✓ Correctly rejected empty message: {response.status_code}\n")
    else:
        print(f"✗ Unexpected status: {response.status_code}\n")
except Exception as e:
    print(f"✗ Exception: {e}\n")

print("=" * 50)
print("All tests completed!")
