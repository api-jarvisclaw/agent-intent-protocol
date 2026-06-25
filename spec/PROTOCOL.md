# Agent Intent Protocol — Specification v2.0

## Overview

The Agent Intent Protocol (AIP) provides a **single interface** for AI agents to access all platform capabilities. Agents declare **what** they want (intent + payload), and the platform handles provider selection, execution, and billing.

**Philosophy:** One SDK call → the platform does everything.

## Core Concepts

### Intent
A declarative statement of what the agent needs. Examples: `chat_completion`, `image_generation`, `web_search`, `text_to_speech`, `video_generation`.

### Payload
The actual request data specific to each intent (messages, prompts, parameters).

### Constraints (optional)
Hard requirements for provider selection: max price, required features, excluded models, etc.

### Optimization Strategy
How to pick among eligible providers: `balanced` (default), `cost`, `speed`, `quality`.

### Resolution
The platform's internal process of selecting the optimal provider. Can be invoked standalone (`resolve`) or as part of execution (`execute`).

## Protocol Flow

```
Agent                              AIP Platform                      Providers (40+)
  │                                    │                                 │
  │── POST /v1/aip/execute ──────────>│                                 │
  │   { intent, payload, optimize }   │                                 │
  │                                    │── [resolve: filter + score] ──>│
  │                                    │<── [best provider selected] ───│
  │                                    │                                 │
  │                                    │── [execute on provider] ──────>│
  │                                    │<── [provider response] ────────│
  │                                    │                                 │
  │<── Result ─────────────────────────│                                 │
  │   { data, meta: { model, cost } } │                                 │
```

## Endpoints

### POST /v1/aip/execute

**The primary endpoint.** Resolve intent + execute in one call.

**Request:**
```json
{
  "intent": "chat_completion",
  "payload": {
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain quantum computing in one sentence."}
    ],
    "temperature": 0.7
  },
  "optimize_for": "balanced",
  "constraints": {
    "max_price_per_token": 0.00005,
    "features": ["function_calling"],
    "exclude_models": ["gpt-3.5-turbo"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "choices": [{
      "message": {"role": "assistant", "content": "Quantum computing uses..."},
      "finish_reason": "stop"
    }],
    "usage": {"prompt_tokens": 25, "completion_tokens": 12}
  },
  "meta": {
    "model": "gpt-4o-mini",
    "provider": "openai",
    "cost_usd": 0.000185,
    "latency_ms": 823,
    "resolve_time_ms": 1.2
  }
}
```

### POST /v1/aip/resolve

Resolve an intent to the best provider **without executing**. Useful for inspection, debugging, or when the agent wants to execute manually.

**Request:**
```json
{
  "intent": "image_generation",
  "optimize_for": "quality",
  "constraints": {
    "max_price_usd": 0.05
  },
  "context": {
    "description": "Product photography for e-commerce"
  }
}
```

**Response:**
```json
{
  "success": true,
  "intent": "image_generation",
  "resolution": {
    "model": "dall-e-3",
    "provider": "openai",
    "endpoint": "https://api.jarvisclaw.ai/v1/images/generations",
    "score": 0.94,
    "reason": "Highest quality score for image generation within budget",
    "price": {"per_image": 0.04},
    "latency_ms": 8000
  },
  "alternatives": [
    {"model": "stable-diffusion-xl", "provider": "stability", "score": 0.82},
    {"model": "midjourney-v6", "provider": "midjourney", "score": 0.78}
  ]
}
```

### GET /v1/aip/discover

List all available intents, models, and services.

**Query Parameters:**
- `category` (optional): Filter by category (`ai`, `marketplace`, `media`)

**Response:**
```json
{
  "intents": [
    {
      "name": "chat_completion",
      "description": "Text generation and conversation",
      "category": "ai",
      "payload_schema": {"$ref": "#/schemas/chat_completion"}
    },
    {
      "name": "image_generation",
      "description": "Generate images from text prompts",
      "category": "media"
    }
  ],
  "models": [
    {
      "id": "gpt-4o",
      "provider": "openai",
      "capabilities": ["chat", "function_calling", "vision", "json_mode"],
      "pricing": {"input": 2.50, "output": 10.00}
    }
  ],
  "services": [
    {
      "name": "web_search",
      "description": "Search the internet",
      "actions": ["search", "news", "images"]
    }
  ]
}
```

### GET /v1/aip/health

Platform health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "providers_online": 42,
  "uptime_seconds": 864000
}
```

## Supported Intents

| Intent | Description | Example Providers |
|--------|-------------|-------------------|
| `chat_completion` | Text generation / chat | OpenAI, Anthropic, Google, DeepSeek, Mistral |
| `image_generation` | Image creation from text | DALL·E 3, Stable Diffusion XL, Midjourney |
| `video_generation` | Video creation from text | Runway, Pika, Kling |
| `text_to_speech` | Voice synthesis | ElevenLabs, OpenAI TTS |
| `speech_to_text` | Audio transcription | Whisper, Deepgram |
| `embedding` | Vector embeddings | OpenAI, Voyage, Cohere |
| `web_search` | Internet search | Perplexity, Tavily, Brave |
| `code_generation` | Code assistance | Claude, DeepSeek Coder |
| `moderation` | Content safety | OpenAI Moderation |
| `translation` | Language translation | DeepL, Google Translate |
| `marketplace_*` | Platform marketplace services | Dynamic catalog |

## Optimization Strategies

| Strategy | Behavior |
|----------|----------|
| `balanced` | Equal weight across cost, speed, quality (default) |
| `quality` | Prefer highest capability models regardless of cost |
| `speed` | Prefer lowest latency providers |
| `cost` | Prefer cheapest providers that meet quality floor |

## Authentication

All requests require a Bearer token:

```
Authorization: Bearer sk-your-api-key
```

Keys are provisioned at https://api.jarvisclaw.ai.

## Error Format

```json
{
  "success": false,
  "error": {
    "code": "NO_PROVIDER_MATCH",
    "message": "No provider satisfies all constraints",
    "details": {
      "intent": "chat_completion",
      "failed_constraint": "max_price_per_token < 0.000001"
    }
  }
}
```

## Streaming

For `chat_completion` and similar intents, pass `"stream": true` in the payload. The response will be Server-Sent Events (SSE) in OpenAI-compatible format.

## Default Platform

All SDKs connect to **https://api.jarvisclaw.ai** by default. Every client accepts an `endpoint` parameter to target custom deployments.

## Versioning

The protocol uses URL versioning (`/v1/`). Breaking changes increment the version number. The current version is **v2.0**.
