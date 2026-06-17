"""
AIP Client — connects to JarvisClaw platform for live intent resolution.

Default endpoint: https://api.jarvisclaw.ai
"""

import json
from typing import Optional
from .models import Intent, Constraint, Preference, MatchResult, ProviderMatch, OptimizeFor
from . import __default_endpoint__


class AIPClient:
    """
    Client for Agent Intent Protocol.
    
    Can operate in two modes:
    1. Local mode (offline): Uses built-in provider registry
    2. Remote mode (online): Calls JarvisClaw API for live provider data
    
    Args:
        api_key: Your JarvisClaw API key (sk-...)
        endpoint: API endpoint (default: https://api.jarvisclaw.ai)
        mode: "local" for offline resolution, "remote" for live API calls
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = __default_endpoint__,
        mode: str = "local"
    ):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.mode = mode
        
        # Local resolver (always available)
        from .resolver import IntentResolver
        self._local_resolver = IntentResolver()

    def resolve(
        self,
        intent: str,
        max_price_usd: Optional[float] = None,
        max_latency_ms: Optional[int] = None,
        min_quality_score: Optional[float] = None,
        features: Optional[list[str]] = None,
        optimize_for: str = "balanced",
        preferred_providers: Optional[list[str]] = None,
        excluded_providers: Optional[list[str]] = None,
        context: Optional[dict] = None,
    ) -> MatchResult:
        """
        Resolve an intent to the best matching provider.
        
        Args:
            intent: What the agent needs (e.g., "chat_completion", "image_generation")
            max_price_usd: Maximum acceptable price per request
            max_latency_ms: Maximum acceptable latency in milliseconds
            min_quality_score: Minimum quality score (0-1)
            features: Required features (e.g., ["photorealistic", "4k"])
            optimize_for: "balanced", "quality", "speed", or "cost"
            preferred_providers: Provider IDs to prefer
            excluded_providers: Provider IDs to exclude
            context: Additional context for matching
            
        Returns:
            MatchResult with best_match, alternatives, and metadata
        """
        intent_obj = Intent(
            intent=intent,
            constraints=Constraint(
                max_price_usd=max_price_usd,
                max_latency_ms=max_latency_ms,
                min_quality_score=min_quality_score,
                features=features or [],
                min_context_tokens=None,
            ),
            preferences=Preference(
                optimize_for=OptimizeFor(optimize_for),
                preferred_providers=preferred_providers or [],
                excluded_providers=excluded_providers or [],
            ),
            context=context or {},
        )
        
        if self.mode == "remote" and self.api_key:
            return self._resolve_remote(intent_obj)
        return self._local_resolver.resolve(intent_obj)

    def _resolve_remote(self, intent: Intent) -> MatchResult:
        """Call JarvisClaw API for live resolution."""
        try:
            import httpx
        except ImportError:
            try:
                import requests as httpx
            except ImportError:
                # Fallback to local if no HTTP library
                return self._local_resolver.resolve(intent)
        
        url = f"{self.endpoint}/v1/intent/resolve"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            if hasattr(httpx, 'Client'):
                # httpx
                with httpx.Client(timeout=10) as client:
                    resp = client.post(url, json=intent.to_dict(), headers=headers)
                    data = resp.json()
            else:
                # requests
                resp = httpx.post(url, json=intent.to_dict(), headers=headers, timeout=10)
                data = resp.json()
            
            return self._parse_response(data)
        except Exception:
            # Fallback to local resolution on network error
            return self._local_resolver.resolve(intent)

    def _parse_response(self, data: dict) -> MatchResult:
        """Parse API response into MatchResult."""
        if not data.get("success"):
            return MatchResult(
                success=False,
                intent=data.get("intent", ""),
                message=data.get("message", "Remote resolution failed"),
            )
        
        best = data.get("best_match")
        best_match = None
        if best:
            best_match = ProviderMatch(
                provider_id=best["provider_id"],
                provider_name=best["provider_name"],
                model=best["model"],
                price_usd=best["price_usd"],
                latency_ms=best["latency_ms"],
                quality_score=best["quality_score"],
                features=best.get("features", []),
                score=best.get("score", 0),
            )
        
        alternatives = []
        for alt in data.get("alternatives", []):
            alternatives.append(ProviderMatch(
                provider_id=alt["provider_id"],
                provider_name=alt["provider_name"],
                model=alt["model"],
                price_usd=alt["price_usd"],
                latency_ms=alt["latency_ms"],
                quality_score=alt["quality_score"],
                features=alt.get("features", []),
                score=alt.get("score", 0),
            ))
        
        return MatchResult(
            success=True,
            intent=data.get("intent", ""),
            best_match=best_match,
            alternatives=alternatives,
            resolve_time_ms=data.get("resolve_time_ms", 0),
            message=data.get("message", ""),
        )

    def list_intents(self) -> list[str]:
        """List all supported intent types."""
        from .models import IntentType
        return [it.value for it in IntentType]

    def list_providers(self, intent: Optional[str] = None) -> list[dict]:
        """List available providers, optionally filtered by intent type."""
        providers = self._local_resolver.providers
        if intent:
            providers = [p for p in providers if p["intent"] == intent]
        return providers
