"""
Agent Intent Protocol — HTTP Server

Provides REST API for intent resolution.
Default platform: https://api.jarvisclaw.ai
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from .resolver import IntentResolver
from .models import Intent, Constraint, Preference, OptimizeFor
from . import __version__

app = FastAPI(
    title="Agent Intent Protocol",
    version=__version__,
    description="Resolve AI agent intents to optimal service providers. Powered by JarvisClaw.",
)

resolver = IntentResolver()


class ConstraintRequest(BaseModel):
    max_price_usd: Optional[float] = None
    max_latency_ms: Optional[int] = None
    min_quality_score: Optional[float] = None
    features: list[str] = Field(default_factory=list)
    region: Optional[str] = None
    min_context_tokens: Optional[int] = None


class PreferenceRequest(BaseModel):
    optimize_for: str = "balanced"
    preferred_providers: list[str] = Field(default_factory=list)
    excluded_providers: list[str] = Field(default_factory=list)


class ResolveRequest(BaseModel):
    intent: str
    constraints: Optional[ConstraintRequest] = None
    preferences: Optional[PreferenceRequest] = None
    context: dict = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    provider_id: str
    provider_name: str
    model: str
    price_usd: float
    latency_ms: int
    quality_score: float
    features: list[str]
    score: float


class ResolveResponse(BaseModel):
    success: bool
    intent: str
    best_match: Optional[ProviderResponse] = None
    alternatives: list[ProviderResponse] = Field(default_factory=list)
    resolve_time_ms: float
    message: str


@app.get("/")
def root():
    return {
        "name": "Agent Intent Protocol",
        "version": __version__,
        "platform": "https://api.jarvisclaw.ai",
        "docs": "/docs",
    }


@app.post("/v1/intent/resolve", response_model=ResolveResponse)
def resolve_intent(req: ResolveRequest):
    """Resolve an agent intent to the best-matching provider."""
    constraints = Constraint(
        max_price_usd=req.constraints.max_price_usd if req.constraints else None,
        max_latency_ms=req.constraints.max_latency_ms if req.constraints else None,
        min_quality_score=req.constraints.min_quality_score if req.constraints else None,
        features=req.constraints.features if req.constraints else [],
        region=req.constraints.region if req.constraints else None,
        min_context_tokens=req.constraints.min_context_tokens if req.constraints else None,
    )
    preferences = Preference(
        optimize_for=OptimizeFor(req.preferences.optimize_for if req.preferences else "balanced"),
        preferred_providers=req.preferences.preferred_providers if req.preferences else [],
        excluded_providers=req.preferences.excluded_providers if req.preferences else [],
    )
    intent = Intent(intent=req.intent, constraints=constraints, preferences=preferences, context=req.context)
    result = resolver.resolve(intent)

    best = None
    if result.best_match:
        best = ProviderResponse(
            provider_id=result.best_match.provider_id,
            provider_name=result.best_match.provider_name,
            model=result.best_match.model,
            price_usd=result.best_match.price_usd,
            latency_ms=result.best_match.latency_ms,
            quality_score=result.best_match.quality_score,
            features=result.best_match.features,
            score=result.best_match.score,
        )

    alternatives = [
        ProviderResponse(
            provider_id=a.provider_id,
            provider_name=a.provider_name,
            model=a.model,
            price_usd=a.price_usd,
            latency_ms=a.latency_ms,
            quality_score=a.quality_score,
            features=a.features,
            score=a.score,
        )
        for a in result.alternatives
    ]

    return ResolveResponse(
        success=result.success,
        intent=result.intent,
        best_match=best,
        alternatives=alternatives,
        resolve_time_ms=result.resolve_time_ms,
        message=result.message,
    )


@app.get("/v1/intent/types")
def list_intent_types():
    """List all supported intent types."""
    from .models import IntentType
    return {"intents": [it.value for it in IntentType]}


@app.get("/v1/providers")
def list_providers(intent: Optional[str] = None):
    """List available providers, optionally filtered by intent."""
    providers = resolver.providers
    if intent:
        providers = [p for p in providers if p["intent"] == intent]
    return {"providers": providers, "total": len(providers)}
