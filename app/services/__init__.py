from __future__ import annotations

import os
from typing import Any

import httpx


class BaseProviderClient:
    name: str = "base"
    description = "Generic provider adapter"

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
    description = "Local simulation provider for testing without external API keys"

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
        content = f"Mock response from {model}: {prompt[:120]}"
        return {
            "content": content,
            "finish_reason": "stop",
            "usage": {"prompt_tokens": len(prompt.split()), "completion_tokens": len(content.split()), "total_tokens": len(prompt.split()) + len(content.split())},
            "latency_ms": 120,
            "cost_usd": 0.0,
            "provider_response": {"provider": self.name, "model": model},
        }


class OpenAICompatibleClient(BaseProviderClient):
    name = "openai-compatible"
    description = "OpenAI-like endpoint for OpenAI, Azure OpenAI, or compatible servers"

    def __init__(self, *, base_url: str, api_key: str | None = None):
        self.base_url = base_url
        self.api_key = api_key

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
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        payload = {
            "model": model,
            "messages": [
                *( [{"role": "system", "content": system_prompt}] if system_prompt else [] ),
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature or 0.2,
            "max_tokens": max_tokens or 256,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = httpx.post(f"{self.base_url.rstrip('/')}/chat/completions", json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") or ""
        usage = data.get("usage", {})
        return {
            "content": content,
            "finish_reason": choices[0].get("finish_reason") if choices else None,
            "usage": usage,
            "latency_ms": 0,
            "cost_usd": metadata.get("cost_usd") if metadata else None,
            "provider_response": data,
        }


class AnthropicCompatibleClient(BaseProviderClient):
    name = "anthropic"
    description = "Anthropic Messages API-compatible adapter"

    def __init__(self, *, api_key: str | None = None, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url

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
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")

        payload = {
            "model": model,
            "max_tokens": max_tokens or 256,
            "temperature": temperature or 0.2,
            "messages": [{"role": "user", "content": prompt}],
            **({"system": system_prompt} if system_prompt else {}),
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        response = httpx.post(f"{self.base_url.rstrip('/')}/v1/messages", json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        content_blocks = data.get("content", [])
        response_text = "\n".join(block.get("text", "") for block in content_blocks if isinstance(block, dict))
        usage = data.get("usage", {})
        return {
            "content": response_text,
            "finish_reason": data.get("stop_reason"),
            "usage": usage,
            "latency_ms": 0,
            "cost_usd": metadata.get("cost_usd") if metadata else None,
            "provider_response": data,
        }


class OllamaClient(BaseProviderClient):
    name = "ollama"
    description = "Local Ollama runtime adapter"

    def __init__(self, *, base_url: str):
        self.base_url = base_url

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
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature or 0.2, "num_predict": max_tokens or 256},
        }
        response = httpx.post(f"{self.base_url.rstrip('/')}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return {
            "content": data.get("response", ""),
            "finish_reason": data.get("done_reason"),
            "usage": {"prompt_tokens": data.get("prompt_eval_count"), "completion_tokens": data.get("eval_count"), "total_tokens": (data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0)},
            "latency_ms": 0,
            "cost_usd": 0.0,
            "provider_response": data,
        }


def get_provider_client(provider: str) -> BaseProviderClient:
    name = (provider or "mock").lower().strip()

    if name in {"mock", "test", "simulator"}:
        return MockProviderClient()
    if name in {"openai", "azure-openai", "azure_openai"}:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAICompatibleClient(base_url=base_url, api_key=api_key)
    if name == "anthropic":
        return AnthropicCompatibleClient(api_key=os.getenv("ANTHROPIC_API_KEY"))
    if name in {"ollama", "local"}:
        return OllamaClient(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    raise ValueError(f"Unsupported provider '{provider}'. Supported providers: mock, openai, anthropic, ollama")


def get_supported_providers() -> list[dict[str, Any]]:
    providers = [
        {"name": "mock", "configured": True, "base_url": None, "description": "Local mock provider for testing and demos"},
        {"name": "openai", "configured": bool(os.getenv("OPENAI_API_KEY")), "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), "description": "OpenAI compatible chat completions API"},
        {"name": "anthropic", "configured": bool(os.getenv("ANTHROPIC_API_KEY")), "base_url": "https://api.anthropic.com", "description": "Anthropic Messages API"},
        {"name": "ollama", "configured": bool(os.getenv("OLLAMA_BASE_URL")), "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), "description": "Local Ollama runtime"},
    ]
    return providers
