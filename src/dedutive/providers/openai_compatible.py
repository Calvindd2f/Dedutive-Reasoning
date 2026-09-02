from __future__ import annotations

import os
from typing import Any

import httpx

from .base import GenerationResult


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("OPENAI_COMPATIBLE_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY")
        self.timeout_seconds = timeout_seconds
        if not self.base_url:
            raise ValueError("OPENAI_COMPATIBLE_BASE_URL is required")
        if not self.api_key:
            raise ValueError("OPENAI_COMPATIBLE_API_KEY is required")

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> GenerationResult:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        choice = body["choices"][0]
        text = choice["message"]["content"]
        return GenerationResult(
            text=text,
            metadata={
                "provider": "openai_compatible",
                "model": model,
                "usage": body.get("usage", {}),
                "finish_reason": choice.get("finish_reason"),
            },
        )
