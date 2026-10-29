from __future__ import annotations

import os
import time
from typing import Any

import httpx

from app.schemas import ProviderStatus


class BaseProviderClient:
    name = "base"

    def invoke(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockProviderClient(BaseProviderClient):
    name = "mock"

    def invoke(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response_text = (
            f"Mock response for model '{model}' with prompt: {prompt[:120]}"
            + (" (system prompt included)" if system_prompt else "")
        )
        return {
            "content": response_text,
            "finish_reason": "stop",
            "latency_ms": 42,
            "usage": {
                "prompt_tokens": max(1, len(prompt.split())),
                "completion_tokens": max(1, len(response_text.split())),
                "total_tokens": max(1, len(prompt.split()) + len(response_text.split())),
            },
            "cost_usd": 0.0,
            "provider_response": {
                "provider": self.name,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "metadata": metadata or {},
            },
            "trace_id": "mock-trace-id",
        }


class OpenAICompatibleClient(BaseProviderClient):
    name = "openai"

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")

    def invoke(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        started_at = time.perf_counter()
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60.0,
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000)

        if response.status_code >= 400:
            raise ValueError(f"OpenAI request failed: {response.text}")

        data = response.json()
        message = data["choices"][0]["message"]
        content = message.get("content") or ""
        usage = data.get("usage") or {}

        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
            "finish_reason": data["choices"][0].get("finish_reason"),
            "latency_ms": elapsed_ms,
            "cost_usd": None,
            "provider_response": data,
            "trace_id": data.get("id"),
        }


class AnthropicCompatibleClient(BaseProviderClient):
    name = "anthropic"

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/")

    def invoke(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens or 256,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
        payload = {k: v for k, v in payload.items() if v is not None}

        started_at = time.perf_counter()
        response = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json=payload,
            timeout=60.0,
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000)

        if response.status_code >= 400:
            raise ValueError(f"Anthropic request failed: {response.text}")

        data = response.json()
        content = data["content"][0]["text"] if data.get("content") else ""
        usage = data.get("usage") or {}

        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("input_tokens"),
                "completion_tokens": usage.get("output_tokens"),
                "total_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
            },
            "finish_reason": data.get("stop_reason"),
            "latency_ms": elapsed_ms,
            "cost_usd": None,
            "provider_response": data,
            "trace_id": data.get("id"),
        }


class OllamaClient(BaseProviderClient):
    name = "ollama"

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")

    def invoke(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {},
        }
        if system_prompt:
            payload["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        if temperature is not None:
            payload["options"]["temperature"] = temperature
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        started_at = time.perf_counter()
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=60.0,
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000)

        if response.status_code >= 400:
            raise ValueError(f"Ollama request failed: {response.text}")

        data = response.json()
        message = data.get("message") or {}
        content = message.get("content") or ""
        usage = data.get("usage") or {}

        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
            "finish_reason": data.get("done_reason"),
            "latency_ms": elapsed_ms,
            "cost_usd": None,
            "provider_response": data,
            "trace_id": data.get("id"),
        }


def get_supported_providers() -> list[ProviderStatus]:
    return [
        ProviderStatus(
            name="mock",
            configured=True,
            base_url=None,
            description="Built-in mock provider for localhost testing and demos.",
        ),
        ProviderStatus(
            name="openai",
            configured=bool(os.getenv("OPENAI_API_KEY")),
            base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            description="OpenAI-compatible chat-completions API.",
        ),
        ProviderStatus(
            name="anthropic",
            configured=bool(os.getenv("ANTHROPIC_API_KEY")),
            base_url=os.getenv("ANTHROPIC_BASE_URL") or "https://api.anthropic.com",
            description="Anthropic Messages API.",
        ),
        ProviderStatus(
            name="ollama",
            configured=bool(os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or True),
            base_url=os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434",
            description="Local Ollama server for self-hosted inference.",
        ),
    ]


def get_provider_client(provider: str) -> BaseProviderClient:
    normalized = (provider or "mock").strip().lower()

    mapping: dict[str, BaseProviderClient] = {
        "mock": MockProviderClient(),
        "openai": OpenAICompatibleClient(),
        "anthropic": AnthropicCompatibleClient(),
        "ollama": OllamaClient(),
    }

    if normalized in mapping:
        return mapping[normalized]

    raise ValueError(f"Unsupported provider: {provider}. Supported providers: {', '.join(sorted(mapping))}")


__all__ = [
    "BaseProviderClient",
    "MockProviderClient",
    "OpenAICompatibleClient",
    "AnthropicCompatibleClient",
    "OllamaClient",
    "get_provider_client",
    "get_supported_providers",
]
