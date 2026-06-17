"""
Agent Intent Protocol — Python Client

A real client that integrates with JarvisClaw API (api.jarvisclaw.ai/v1).
Provides intent-based smart routing across all available models and services.
"""

import time
import httpx
from typing import Optional, Any
from dataclasses import dataclass, field


# ─── Models & Types ──────────────────────────────────────────────────────────

MODELS_REGISTRY = {
    # Free models (unlimited usage)
    "nvidia/deepseek-v4-flash": {"price_input": 0, "price_output": 0, "tier": "free", "latency_ms": 400, "quality": 0.82},
    "nvidia/deepseek-v4-pro": {"price_input": 0, "price_output": 0, "tier": "free", "latency_ms": 600, "quality": 0.87},
    "nvidia/qwen3-coder-480b": {"price_input": 0, "price_output": 0, "tier": "free", "latency_ms": 500, "quality": 0.85},
    "nvidia/nemotron-3-nano-omni-30b": {"price_input": 0, "price_output": 0, "tier": "free", "latency_ms": 300, "quality": 0.75},
    "nvidia/mistral-small-4-119b": {"price_input": 0, "price_output": 0, "tier": "free", "latency_ms": 450, "quality": 0.80},
    "nvidia/llama-4-maverick": {"price_input": 0, "price_output": 0, "tier": "free", "latency_ms": 350, "quality": 0.79},
    # Paid models (per 1M tokens)
    "openai/gpt-5.5": {"price_input": 5.0, "price_output": 30.0, "tier": "premium", "latency_ms": 1200, "quality": 0.98},
    "openai/gpt-5.4-nano": {"price_input": 0.20, "price_output": 1.25, "tier": "standard", "latency_ms": 500, "quality": 0.90},
    "openai/o3": {"price_input": 2.0, "price_output": 8.0, "tier": "premium", "latency_ms": 3000, "quality": 0.96},
    "anthropic/claude-opus-4.7": {"price_input": 5.0, "price_output": 25.0, "tier": "premium", "latency_ms": 1500, "quality": 0.97},
    "anthropic/claude-sonnet-4.6": {"price_input": 3.0, "price_output": 15.0, "tier": "premium", "latency_ms": 1000, "quality": 0.95},
    "google/gemini-3.1-pro": {"price_input": 2.0, "price_output": 12.0, "tier": "premium", "latency_ms": 900, "quality": 0.94},
    "google/gemini-2.5-flash": {"price_input": 0.30, "price_output": 2.50, "tier": "standard", "latency_ms": 400, "quality": 0.88},
    "deepseek/deepseek-reasoner": {"price_input": 0.20, "price_output": 0.40, "tier": "standard", "latency_ms": 800, "quality": 0.89},
}

SERVICES = {
    "chat_completion": "/v1/chat/completions",
    "image_generation": "/v1/images/generations",
    "video_generation": "/v1/videos/generations",
    "music_generation": "/v1/audio/generations",
    "text_to_speech": "/v1/audio/speech",
    "web_search": "/v1/search",
    "prediction_market": "/v1/marketplace/prediction",
    "dex_trading": "/v1/marketplace/dex",
    "compute": "/v1/marketplace/compute",
    "crypto_data": "/v1/marketplace/surf",
    "phone_voice": "/v1/marketplace/phone",
    "trading_markets": "/v1/marketplace/markets",
    "realface": "/v1/marketplace/realface",
}


@dataclass
class IntentResult:
    """Result of intent resolution."""
    success: bool
    model: str
    endpoint: str
    score: float
    reason: str
    alternatives: list = field(default_factory=list)
    resolve_time_ms: float = 0.0


@dataclass
class Constraints:
    max_price_input: Optional[float] = None   # Max $/1M input tokens
    max_price_output: Optional[float] = None  # Max $/1M output tokens
    max_latency_ms: Optional[int] = None
    min_quality: Optional[float] = None
    tier: Optional[str] = None                # "free", "standard", "premium"
    exclude_models: list = field(default_factory=list)


class AIPClient:
    """
    Agent Intent Protocol client for JarvisClaw.
    
    Provides intent-based smart routing across all models and services
    available at api.jarvisclaw.ai.
    
    Unlike LiteLLM (which is a format proxy), AIP resolves *what* you need
    into *which* model/service to use, optimizing for cost, speed, or quality.
    """

    DEFAULT_ENDPOINT = "https://api.jarvisclaw.ai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.endpoint = (endpoint or self.DEFAULT_ENDPOINT).rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.endpoint,
            timeout=timeout,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict:
        headers = {"User-Agent": "aip-python/0.2.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # ─── Intent Resolution (Smart Routing) ────────────────────────────────

    def resolve(
        self,
        intent: str = "chat_completion",
        optimize_for: str = "balanced",
        constraints: Optional[Constraints] = None,
        top_k: int = 3,
    ) -> IntentResult:
        """
        Resolve an intent to the optimal model/service.
        
        Args:
            intent: What you want to do (chat_completion, image_generation, etc.)
            optimize_for: "balanced", "cost", "speed", or "quality"
            constraints: Optional filtering constraints
            top_k: Number of alternatives to return
            
        Returns:
            IntentResult with best model and alternatives
        """
        start = time.perf_counter()
        
        if intent not in SERVICES:
            return IntentResult(
                success=False, model="", endpoint="",
                score=0, reason=f"Unknown intent: {intent}. Available: {list(SERVICES.keys())}"
            )

        # For non-chat intents, return the service endpoint directly
        if intent != "chat_completion":
            elapsed = (time.perf_counter() - start) * 1000
            return IntentResult(
                success=True,
                model=intent,
                endpoint=f"{self.endpoint}{SERVICES[intent]}",
                score=1.0,
                reason=f"Direct service endpoint for {intent}",
                resolve_time_ms=elapsed,
            )

        # Smart routing for chat completion
        candidates = self._score_models(optimize_for, constraints)
        
        if not candidates:
            elapsed = (time.perf_counter() - start) * 1000
            return IntentResult(
                success=False, model="", endpoint="",
                score=0, reason="No models match constraints",
                resolve_time_ms=elapsed,
            )

        best = candidates[0]
        alternatives = candidates[1:top_k]
        elapsed = (time.perf_counter() - start) * 1000

        return IntentResult(
            success=True,
            model=best["model"],
            endpoint=f"{self.endpoint}/v1/chat/completions",
            score=best["score"],
            reason=best["reason"],
            alternatives=[{"model": a["model"], "score": a["score"], "reason": a["reason"]} for a in alternatives],
            resolve_time_ms=elapsed,
        )

    def _score_models(self, optimize_for: str, constraints: Optional[Constraints]) -> list:
        """Score and rank models based on optimization strategy."""
        weights = {
            "balanced": (0.33, 0.33, 0.34),
            "cost": (0.70, 0.15, 0.15),
            "speed": (0.15, 0.70, 0.15),
            "quality": (0.15, 0.15, 0.70),
        }.get(optimize_for, (0.33, 0.33, 0.34))

        w_cost, w_speed, w_quality = weights
        results = []

        for model_id, info in MODELS_REGISTRY.items():
            # Apply constraints
            if constraints:
                if constraints.max_price_input is not None and info["price_input"] > constraints.max_price_input:
                    continue
                if constraints.max_price_output is not None and info["price_output"] > constraints.max_price_output:
                    continue
                if constraints.max_latency_ms is not None and info["latency_ms"] > constraints.max_latency_ms:
                    continue
                if constraints.min_quality is not None and info["quality"] < constraints.min_quality:
                    continue
                if constraints.tier and info["tier"] != constraints.tier:
                    continue
                if model_id in constraints.exclude_models:
                    continue

            # Normalize scores (0-1, higher is better)
            max_price = 30.0  # max output price
            cost_score = 1.0 - (info["price_output"] / max_price)
            speed_score = 1.0 - (info["latency_ms"] / 3500.0)
            quality_score = info["quality"]

            total = w_cost * cost_score + w_speed * speed_score + w_quality * quality_score
            reason = f"cost={cost_score:.2f} speed={speed_score:.2f} quality={quality_score:.2f}"

            results.append({
                "model": model_id,
                "score": round(total, 4),
                "reason": reason,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    # ─── Direct API Calls ─────────────────────────────────────────────────

    def chat(self, messages: list, model: Optional[str] = None, **kwargs) -> dict:
        """
        Send a chat completion request. If no model specified, auto-resolves best model.
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            model: Specific model, or None for auto-routing
            **kwargs: Additional params (temperature, max_tokens, etc.)
        """
        if model is None:
            result = self.resolve("chat_completion", optimize_for="balanced")
            model = result.model

        payload = {"model": model, "messages": messages, **kwargs}
        resp = self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()

    def generate_image(self, prompt: str, **kwargs) -> dict:
        """Generate an image from a text prompt."""
        payload = {"prompt": prompt, **kwargs}
        resp = self._client.post("/v1/images/generations", json=payload)
        resp.raise_for_status()
        return resp.json()

    def generate_video(self, prompt: str, **kwargs) -> dict:
        """Generate a video from a text prompt."""
        payload = {"prompt": prompt, **kwargs}
        resp = self._client.post("/v1/videos/generations", json=payload)
        resp.raise_for_status()
        return resp.json()

    def text_to_speech(self, text: str, voice: str = "alloy", **kwargs) -> bytes:
        """Convert text to speech audio."""
        payload = {"input": text, "voice": voice, **kwargs}
        resp = self._client.post("/v1/audio/speech", json=payload)
        resp.raise_for_status()
        return resp.content

    def search(self, query: str, **kwargs) -> dict:
        """Perform a web search."""
        payload = {"query": query, **kwargs}
        resp = self._client.post("/v1/search", json=payload)
        resp.raise_for_status()
        return resp.json()

    # ─── Marketplace Services ─────────────────────────────────────────────

    def marketplace(self, service: str, action: str, **kwargs) -> dict:
        """
        Call a marketplace service.
        
        Args:
            service: prediction, dex, compute, surf, phone, markets, realface
            action: Service-specific action path
        """
        path = f"/v1/marketplace/{service}/{action}"
        resp = self._client.post(path, json=kwargs)
        resp.raise_for_status()
        return resp.json()

    # ─── Utility ──────────────────────────────────────────────────────────

    def list_models(self, tier: Optional[str] = None) -> list:
        """List available models, optionally filtered by tier."""
        models = []
        for model_id, info in MODELS_REGISTRY.items():
            if tier and info["tier"] != tier:
                continue
            models.append({
                "id": model_id,
                "tier": info["tier"],
                "price_input": info["price_input"],
                "price_output": info["price_output"],
                "latency_ms": info["latency_ms"],
                "quality": info["quality"],
            })
        return models

    def list_services(self) -> dict:
        """List all available service endpoints."""
        return {k: f"{self.endpoint}{v}" for k, v in SERVICES.items()}

    def health(self) -> dict:
        """Check API health."""
        resp = self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
