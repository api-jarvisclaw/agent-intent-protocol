"""Data models for Agent Intent Protocol."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class OptimizeFor(str, Enum):
    BALANCED = "balanced"
    QUALITY = "quality"
    SPEED = "speed"
    COST = "cost"


class IntentType(str, Enum):
    CHAT_COMPLETION = "chat_completion"
    IMAGE_GENERATION = "image_generation"
    TEXT_TO_SPEECH = "text_to_speech"
    SPEECH_TO_TEXT = "speech_to_text"
    EMBEDDING = "embedding"
    CODE_GENERATION = "code_generation"
    WEB_SEARCH = "web_search"
    MODERATION = "moderation"


@dataclass
class Constraint:
    """Constraints that MUST be satisfied for a match."""
    max_price_usd: Optional[float] = None
    max_latency_ms: Optional[int] = None
    min_quality_score: Optional[float] = None
    features: list[str] = field(default_factory=list)
    region: Optional[str] = None
    min_context_tokens: Optional[int] = None


@dataclass
class Preference:
    """Soft preferences for ranking matched providers."""
    optimize_for: OptimizeFor = OptimizeFor.BALANCED
    preferred_providers: list[str] = field(default_factory=list)
    excluded_providers: list[str] = field(default_factory=list)


@dataclass
class Intent:
    """An agent's declared intent for a service."""
    intent: str
    constraints: Optional[Constraint] = None
    preferences: Optional[Preference] = None
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"intent": self.intent}
        if self.constraints:
            c = {}
            if self.constraints.max_price_usd is not None:
                c["max_price_usd"] = self.constraints.max_price_usd
            if self.constraints.max_latency_ms is not None:
                c["max_latency_ms"] = self.constraints.max_latency_ms
            if self.constraints.min_quality_score is not None:
                c["min_quality_score"] = self.constraints.min_quality_score
            if self.constraints.features:
                c["features"] = self.constraints.features
            if self.constraints.region:
                c["region"] = self.constraints.region
            if self.constraints.min_context_tokens is not None:
                c["min_context_tokens"] = self.constraints.min_context_tokens
            d["constraints"] = c
        if self.preferences:
            p = {"optimize_for": self.preferences.optimize_for.value}
            if self.preferences.preferred_providers:
                p["preferred_providers"] = self.preferences.preferred_providers
            if self.preferences.excluded_providers:
                p["excluded_providers"] = self.preferences.excluded_providers
            d["preferences"] = p
        if self.context:
            d["context"] = self.context
        return d


@dataclass
class ProviderMatch:
    """A single matched provider."""
    provider_id: str
    provider_name: str
    model: str
    price_usd: float
    latency_ms: int
    quality_score: float
    features: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass
class MatchResult:
    """Result of intent resolution."""
    success: bool
    intent: str
    best_match: Optional[ProviderMatch] = None
    alternatives: list[ProviderMatch] = field(default_factory=list)
    resolve_time_ms: float = 0.0
    message: str = ""
