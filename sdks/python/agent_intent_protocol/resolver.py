"""
Intent Resolver — the core matching engine.

Resolves agent intents to the best-matching provider based on
constraints, preferences, and provider capabilities.
"""

import time
from .models import (
    Intent, Constraint, Preference, ProviderMatch, MatchResult, OptimizeFor
)


# Default provider registry (simulates JarvisClaw's 40+ providers)
DEFAULT_PROVIDERS = [
    {"id": "openai-gpt4o", "name": "OpenAI GPT-4o", "model": "gpt-4o", "intent": "chat_completion", "price_usd": 0.005, "latency_ms": 800, "quality_score": 0.95, "features": ["function_calling", "vision", "json_mode"], "context_tokens": 128000},
    {"id": "anthropic-claude4", "name": "Anthropic Claude 4", "model": "claude-sonnet-4-20250514", "intent": "chat_completion", "price_usd": 0.006, "latency_ms": 1000, "quality_score": 0.96, "features": ["function_calling", "vision", "long_context"], "context_tokens": 200000},
    {"id": "deepseek-v3", "name": "DeepSeek V3", "model": "deepseek-chat", "intent": "chat_completion", "price_usd": 0.001, "latency_ms": 600, "quality_score": 0.88, "features": ["function_calling", "json_mode"], "context_tokens": 64000},
    {"id": "google-gemini", "name": "Google Gemini 2.5", "model": "gemini-2.5-flash", "intent": "chat_completion", "price_usd": 0.003, "latency_ms": 500, "quality_score": 0.92, "features": ["function_calling", "vision", "grounding"], "context_tokens": 1000000},
    {"id": "ideogram-3", "name": "Ideogram 3", "model": "ideogram-3", "intent": "image_generation", "price_usd": 0.03, "latency_ms": 5000, "quality_score": 0.90, "features": ["photorealistic", "text_rendering", "4k"], "context_tokens": 0},
    {"id": "flux-pro", "name": "Black Forest Flux Pro", "model": "flux-pro", "intent": "image_generation", "price_usd": 0.05, "latency_ms": 8000, "quality_score": 0.92, "features": ["photorealistic", "artistic", "4k"], "context_tokens": 0},
    {"id": "dall-e-3", "name": "DALL-E 3", "model": "dall-e-3", "intent": "image_generation", "price_usd": 0.04, "latency_ms": 7000, "quality_score": 0.88, "features": ["photorealistic", "text_rendering"], "context_tokens": 0},
    {"id": "openai-tts", "name": "OpenAI TTS", "model": "tts-1-hd", "intent": "text_to_speech", "price_usd": 0.015, "latency_ms": 1500, "quality_score": 0.90, "features": ["multilingual", "hd"], "context_tokens": 0},
    {"id": "elevenlabs", "name": "ElevenLabs", "model": "eleven-turbo-v2", "intent": "text_to_speech", "price_usd": 0.018, "latency_ms": 800, "quality_score": 0.95, "features": ["multilingual", "voice_cloning", "hd"], "context_tokens": 0},
    {"id": "openai-whisper", "name": "OpenAI Whisper", "model": "whisper-1", "intent": "speech_to_text", "price_usd": 0.006, "latency_ms": 3000, "quality_score": 0.92, "features": ["multilingual", "timestamps"], "context_tokens": 0},
    {"id": "openai-embed", "name": "OpenAI Embedding", "model": "text-embedding-3-large", "intent": "embedding", "price_usd": 0.00013, "latency_ms": 200, "quality_score": 0.93, "features": ["multilingual", "3072d"], "context_tokens": 8192},
    {"id": "voyage-3", "name": "Voyage AI 3", "model": "voyage-3", "intent": "embedding", "price_usd": 0.00012, "latency_ms": 300, "quality_score": 0.91, "features": ["multilingual", "code"], "context_tokens": 32000},
    {"id": "claude-code", "name": "Claude Code", "model": "claude-sonnet-4-20250514", "intent": "code_generation", "price_usd": 0.006, "latency_ms": 1200, "quality_score": 0.95, "features": ["multi_file", "refactor", "tests"], "context_tokens": 200000},
    {"id": "codex-mini", "name": "OpenAI Codex Mini", "model": "o4-mini", "intent": "code_generation", "price_usd": 0.003, "latency_ms": 900, "quality_score": 0.90, "features": ["multi_file", "fast"], "context_tokens": 128000},
    {"id": "deepseek-coder", "name": "DeepSeek Coder", "model": "deepseek-coder", "intent": "code_generation", "price_usd": 0.001, "latency_ms": 700, "quality_score": 0.87, "features": ["multi_file", "fast"], "context_tokens": 64000},
    {"id": "tavily-search", "name": "Tavily Search", "model": "tavily-search", "intent": "web_search", "price_usd": 0.001, "latency_ms": 1000, "quality_score": 0.85, "features": ["realtime", "structured"], "context_tokens": 0},
    {"id": "exa-search", "name": "Exa Search", "model": "exa-search", "intent": "web_search", "price_usd": 0.002, "latency_ms": 1200, "quality_score": 0.88, "features": ["realtime", "semantic", "structured"], "context_tokens": 0},
]


class IntentResolver:
    """
    Resolves agent intents to the best-matching provider.
    
    Uses a multi-dimensional scoring algorithm:
    - Hard constraints filter (price, latency, quality, features)
    - Soft preference ranking (optimize_for strategy)
    """

    def __init__(self, providers: list[dict] | None = None):
        self.providers = providers or DEFAULT_PROVIDERS

    def resolve(self, intent: Intent) -> MatchResult:
        """Resolve an intent to the best matching provider."""
        start = time.perf_counter()
        
        constraints = intent.constraints or Constraint()
        preferences = intent.preferences or Preference()
        
        # Step 1: Filter by intent type
        candidates = [p for p in self.providers if p["intent"] == intent.intent]
        
        # Step 2: Apply hard constraints
        candidates = self._apply_constraints(candidates, constraints)
        
        # Step 3: Apply exclusions
        if preferences.excluded_providers:
            candidates = [p for p in candidates
                         if p["id"] not in preferences.excluded_providers]
        
        # Step 4: Score and rank
        scored = self._score_candidates(candidates, preferences)
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        if not scored:
            return MatchResult(
                success=False,
                intent=intent.intent,
                resolve_time_ms=elapsed_ms,
                message="No providers match the given constraints. Try relaxing constraints."
            )
        
        best = scored[0]
        alternatives = scored[1:5]  # Top 4 alternatives
        
        return MatchResult(
            success=True,
            intent=intent.intent,
            best_match=best,
            alternatives=alternatives,
            resolve_time_ms=elapsed_ms,
            message=f"Matched {len(scored)} providers. Best: {best.provider_name}"
        )

    def _apply_constraints(self, candidates: list[dict], c: Constraint) -> list[dict]:
        """Filter providers by hard constraints."""
        result = []
        for p in candidates:
            if c.max_price_usd is not None and p["price_usd"] > c.max_price_usd:
                continue
            if c.max_latency_ms is not None and p["latency_ms"] > c.max_latency_ms:
                continue
            if c.min_quality_score is not None and p["quality_score"] < c.min_quality_score:
                continue
            if c.features:
                if not all(f in p.get("features", []) for f in c.features):
                    continue
            if c.min_context_tokens is not None:
                if p.get("context_tokens", 0) < c.min_context_tokens:
                    continue
            result.append(p)
        return result

    def _score_candidates(self, candidates: list[dict], pref: Preference) -> list[ProviderMatch]:
        """Score and rank candidates based on preferences."""
        if not candidates:
            return []
        
        # Normalize metrics
        max_price = max(p["price_usd"] for p in candidates) or 1
        max_latency = max(p["latency_ms"] for p in candidates) or 1
        
        # Weight profiles
        weights = {
            OptimizeFor.BALANCED: (0.33, 0.33, 0.34),
            OptimizeFor.QUALITY: (0.1, 0.1, 0.8),
            OptimizeFor.SPEED: (0.1, 0.7, 0.2),
            OptimizeFor.COST: (0.7, 0.1, 0.2),
        }
        w_cost, w_speed, w_quality = weights.get(pref.optimize_for, (0.33, 0.33, 0.34))
        
        scored = []
        for p in candidates:
            cost_score = 1 - (p["price_usd"] / max_price) if max_price > 0 else 1
            speed_score = 1 - (p["latency_ms"] / max_latency) if max_latency > 0 else 1
            quality_score = p["quality_score"]
            
            # Preference bonus
            bonus = 0.05 if p["id"] in pref.preferred_providers else 0
            
            total = (w_cost * cost_score + w_speed * speed_score + w_quality * quality_score) + bonus
            
            scored.append(ProviderMatch(
                provider_id=p["id"],
                provider_name=p["name"],
                model=p["model"],
                price_usd=p["price_usd"],
                latency_ms=p["latency_ms"],
                quality_score=p["quality_score"],
                features=p.get("features", []),
                score=round(total, 4)
            ))
        
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored
