"""Base Claude agent wrapper with caching-aware message construction."""
from __future__ import annotations

import json
from typing import Any

import anthropic

from scanner.config import config


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def call_agent(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> str:
    """Single-turn agent call. Returns the text response."""
    client = _client()
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def format_data_for_prompt(data: dict[str, Any]) -> str:
    """Serialize a data dict to a clean JSON string for injection into prompts."""
    return json.dumps(data, indent=2, default=str)
