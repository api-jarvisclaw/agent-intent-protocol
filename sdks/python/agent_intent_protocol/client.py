"""
Agent Intent Protocol — Python SDK v2.0

A thin HTTP client for the AIP backend at api.jarvisclaw.ai.
One interface for all platform capabilities: the Agent describes *what* it wants,
the platform decides *how* to fulfill it.

Usage:
    from agent_intent_protocol import AIPClient

    client = AIPClient(api_key="sk-xxx")

    # One-shot: describe intent, get result directly
    result = client.execute("chat_completion", {
        "messages": [{"role": "user", "content": "Hello"}]
    })

    # Two-step: resolve best provider, then call it yourself
    resolution = client.resolve("chat_completion", optimize_for="cost")
    # resolution["model"], resolution["endpoint"], resolution["price"]...

    # Discover all available capabilities
    capabilities = client.discover()
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

import httpx


__version__ = "2.0.0"

DEFAULT_ENDPOINT = "https://api.jarvisclaw.ai"


class AIPError(Exception):
    """Error returned by the AIP backend."""

    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AIPClient:
    """
    Agent Intent Protocol client.

    Provides a single interface to all JarvisClaw platform capabilities.
    The Agent expresses intent; the platform handles routing, optimization,
    and execution.

    Three core operations:
        - resolve(): Find the best provider for an intent (without executing)
        - execute(): Resolve + execute in one step (recommended)
        - discover(): List all available intents and services
    """

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        timeout: float = 60.0,
    ):
        """
        Initialize the AIP client.

        Args:
            api_key: API key for authentication. Falls back to AIP_API_KEY env var.
            endpoint: Platform URL. Defaults to https://api.jarvisclaw.ai
            timeout: Request timeout in seconds.
        """
        self.endpoint = (endpoint or os.getenv("AIP_ENDPOINT", DEFAULT_ENDPOINT)).rstrip("/")
        self.api_key = api_key or os.getenv("AIP_API_KEY", "")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.endpoint,
            timeout=timeout,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "User-Agent": f"aip-python/{__version__}",
            "Content-Type": "application/json",
        }
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    # ─── Core: Resolve ─────────────────────────────────────────────────────

    def resolve(
        self,
        intent: str,
        *,
        optimize_for: str = "balanced",
        constraints: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Resolve an intent to the optimal provider without executing.

        The platform evaluates all available models/services and returns
        the best match based on your optimization preference and constraints.

        Args:
            intent: What you want to do. Examples:
                    "chat_completion", "image_generation", "video_generation",
                    "text_to_speech", "web_search", "code_generation",
                    "dex_trading", "prediction_market", "compute", etc.
            optimize_for: Strategy — "balanced", "cost", "speed", or "quality"
            constraints: Optional filters, e.g.:
                    {"max_price_per_1m_tokens": 5.0, "max_latency_ms": 1000,
                     "min_quality": 0.9, "tier": "premium",
                     "exclude_providers": ["openai"]}
            context: Optional context hints, e.g.:
                    {"task_description": "summarize a legal document",
                     "estimated_tokens": 50000, "priority": "high"}

        Returns:
            Resolution dict with keys:
                model, endpoint, score, reason, alternatives, price, latency_ms
        """
        body: dict[str, Any] = {
            "intent": intent,
            "optimize_for": optimize_for,
        }
        if constraints:
            body["constraints"] = constraints
        if context:
            body["context"] = context

        return self._post("/v1/aip/resolve", body)

    # ─── Core: Execute ─────────────────────────────────────────────────────

    def execute(
        self,
        intent: str,
        payload: dict[str, Any],
        *,
        optimize_for: str = "balanced",
        constraints: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any] | httpx.Response:
        """
        Resolve + execute in one step. This is the recommended method.

        The platform picks the best provider for your intent and immediately
        executes the request, returning the result.

        Args:
            intent: What you want to do (same as resolve).
            payload: The actual request payload. Structure depends on intent:
                     - chat_completion: {"messages": [...], "temperature": 0.7}
                     - image_generation: {"prompt": "a cat", "size": "1024x1024"}
                     - text_to_speech: {"input": "Hello", "voice": "alloy"}
                     - web_search: {"query": "latest news"}
                     - video_generation: {"prompt": "..."}
                     - dex_trading: {"action": "swap", "token_in": "USDC", ...}
            optimize_for: Strategy — "balanced", "cost", "speed", or "quality"
            constraints: Optional filters (same as resolve).
            stream: If True, returns raw httpx.Response for streaming.

        Returns:
            The execution result (JSON dict), or raw Response if stream=True.
        """
        body: dict[str, Any] = {
            "intent": intent,
            "payload": payload,
            "optimize_for": optimize_for,
        }
        if constraints:
            body["constraints"] = constraints
        if stream:
            body["stream"] = True

        if stream:
            return self._post_stream("/v1/aip/execute", body)
        return self._post("/v1/aip/execute", body)

    # ─── Core: Discover ────────────────────────────────────────────────────

    def discover(self, category: str | None = None) -> dict[str, Any]:
        """
        Discover all available intents and services on the platform.

        Returns a structured catalog of everything the platform can do,
        including available models, services, pricing, and capabilities.

        Args:
            category: Optional filter. E.g. "ai", "marketplace", "media"

        Returns:
            Dict with intents, services, models, and their metadata.
        """
        params = {}
        if category:
            params["category"] = category
        return self._get("/v1/aip/discover", params=params)

    # ─── Convenience: Chat ─────────────────────────────────────────────────

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        optimize_for: str = "balanced",
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | httpx.Response:
        """
        Chat completion — the most common operation.

        If model is specified, calls the model directly (OpenAI-compatible).
        If model is None, uses AIP routing to pick the best model.

        Args:
            messages: [{"role": "user", "content": "..."}]
            model: Specific model ID, or None for auto-routing.
            optimize_for: Routing strategy when model is None.
            stream: Stream the response.
            **kwargs: temperature, max_tokens, top_p, etc.
        """
        if model:
            # Direct call, bypass AIP routing
            payload = {"model": model, "messages": messages, **kwargs}
            if stream:
                payload["stream"] = True
                return self._post_stream("/v1/chat/completions", payload)
            return self._post("/v1/chat/completions", payload)

        # AIP-routed
        payload = {"messages": messages, **kwargs}
        return self.execute(
            "chat_completion", payload,
            optimize_for=optimize_for, stream=stream,
        )

    # ─── Convenience: Image ────────────────────────────────────────────────

    def generate_image(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Generate an image from a text prompt."""
        return self.execute("image_generation", {"prompt": prompt, **kwargs})

    # ─── Convenience: Video ────────────────────────────────────────────────

    def generate_video(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Generate a video from a text prompt."""
        return self.execute("video_generation", {"prompt": prompt, **kwargs})

    # ─── Convenience: TTS ──────────────────────────────────────────────────

    def text_to_speech(self, text: str, voice: str = "alloy", **kwargs: Any) -> bytes:
        """Convert text to speech. Returns audio bytes."""
        resp = self._post_stream("/v1/aip/execute", {
            "intent": "text_to_speech",
            "payload": {"input": text, "voice": voice, **kwargs},
        })
        return resp.content

    # ─── Convenience: Search ───────────────────────────────────────────────

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Web search."""
        return self.execute("web_search", {"query": query, **kwargs})

    # ─── Convenience: Marketplace ──────────────────────────────────────────

    def marketplace(self, service: str, action: str, **kwargs: Any) -> dict[str, Any]:
        """
        Call a marketplace service.

        Args:
            service: Service name (prediction, dex, compute, surf, phone, etc.)
            action: Action within the service
            **kwargs: Action-specific parameters
        """
        return self.execute(f"marketplace_{service}", {"action": action, **kwargs})

    # ─── Utility ───────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """Check platform health and API version."""
        return self._get("/v1/aip/health")

    def models(self, intent: str | None = None) -> list[dict[str, Any]]:
        """List available models, optionally filtered by intent."""
        params = {}
        if intent:
            params["intent"] = intent
        resp = self._get("/v1/aip/discover", params=params)
        return resp.get("models", [])

    # ─── HTTP Layer ────────────────────────────────────────────────────────

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.post(path, json=body)
        return self._handle_response(resp)

    def _post_stream(self, path: str, body: dict[str, Any]) -> httpx.Response:
        resp = self._client.post(path, json=body)
        if resp.status_code >= 400:
            self._raise_error(resp)
        return resp

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        resp = self._client.get(path, params=params)
        return self._handle_response(resp)

    def _handle_response(self, resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code >= 400:
            self._raise_error(resp)
        return resp.json()

    def _raise_error(self, resp: httpx.Response) -> None:
        try:
            body = resp.json()
            msg = body.get("error", {}).get("message", resp.text)
        except Exception:
            msg = resp.text
            body = None
        raise AIPError(
            f"[{resp.status_code}] {msg}",
            status_code=resp.status_code,
            body=body,
        )

    # ─── Lifecycle ─────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "AIPClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"AIPClient(endpoint={self.endpoint!r})"
