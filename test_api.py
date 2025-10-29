#!/usr/bin/env python3
"""Quick test of Anthropic API"""

import os
from anthropic import Anthropic

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API Key present: {bool(api_key)}")
print(f"API Key prefix: {api_key[:15] if api_key else 'None'}...")

client = Anthropic(api_key=api_key)

# Try different model names
models_to_try = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
]

for model in models_to_try:
    try:
        print(f"\nTrying model: {model}")
        response = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": "Say hello"}]
        )
        print(f"  ✓ SUCCESS! Response: {response.content[0].text[:50]}")
        break
    except Exception as e:
        print(f"  ✗ Failed: {str(e)[:100]}")
