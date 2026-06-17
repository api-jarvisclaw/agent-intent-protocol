# Agent Intent Protocol — Specification v1.0

## Overview

The Agent Intent Protocol (AIP) enables AI agents to declare **what** they need (intent + constraints) rather than **which** provider to use. The protocol resolves intents to optimal providers through multi-dimensional scoring.

## Core Concepts

### Intent
A declarative statement of what an agent needs to accomplish. Intents are typed and map to categories of AI services.

### Constraints
Hard requirements that providers **must** satisfy to be considered. Any provider failing a constraint is excluded.

### Preferences
Soft optimization directives that influence scoring among eligible providers.

### Resolution
The process of matching an intent to the best provider, considering constraints, preferences, and real-time provider state.

## Protocol Flow

```
Agent                          AIP Resolver                    Provider Registry
  |                                |                                |
  |── IntentRequest ──────────────>|                                |
  |                                |── Query providers ────────────>|
  |                                |<── Provider capabilities ──────|
  |                                |                                |
  |                                |   [Filter by constraints]      |
  |                                |   [Score by preferences]       |
  |                                |   [Rank candidates]            |
  |                                |                                |
  |<── IntentResponse ─────────────|                                |
  |   (best_match + alternatives)  |                                |
```

## Endpoints

### POST /v1/intent/resolve

Resolve an intent to the best matching provider.

**Request:**
```json
{
  "intent": "chat_completion",
  "constraints": {
    "max_price_usd": 0.01,
    "max_latency_ms": 2000,
    "min_quality_score": 0.8,
    "features": ["function_calling"],
    "exclude_providers": ["provider-x"]
  },
  "preferences": {
    "optimize_for": "balanced",
    "preferred_providers": ["openai", "anthropic"]
  },
  "context": {
    "task_description": "Customer support chatbot",
    "estimated_tokens": 4000,
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "intent": "chat_completion",
  "best_match": {
    "provider_id": "openai-gpt4o-mini",
    "provider_name": "OpenAI GPT-4o Mini",
    "model": "gpt-4o-mini",
    "price_usd": 0.003,
    "latency_ms": 800,
    "quality_score": 0.88,
    "features": ["function_calling", "streaming", "json_mode"],
    "score": 0.9234,
    "endpoint": "https://api.jarvisclaw.ai/v1/chat/completions"
  },
  "alternatives": [...],
  "resolve_time_ms": 0.42
}
```

### GET /v1/intents

List all supported intent types.

### GET /v1/providers?intent={type}

List available providers, optionally filtered by intent type.

### GET /v1/health

Health check endpoint.

## Scoring Algorithm

The resolver uses weighted multi-dimensional scoring:

| Optimize For | Price Weight | Latency Weight | Quality Weight |
|---|---|---|---|
| balanced | 0.33 | 0.33 | 0.34 |
| quality | 0.15 | 0.15 | 0.70 |
| speed | 0.15 | 0.70 | 0.15 |
| cost | 0.70 | 0.15 | 0.15 |

Scores are normalized to [0, 1] within each dimension before weighting.

## Default Platform

The reference implementation connects to **https://api.jarvisclaw.ai** by default. All SDK clients accept an `endpoint` parameter to override this.
