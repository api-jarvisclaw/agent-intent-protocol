# Agent Intent Protocol (AIP)

> A protocol for AI agents to declare intents and automatically discover the best-matching service providers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## The Problem

x402 solved "how agents pay." But it didn't solve **"how agents choose who to pay."**

When an AI agent needs a service (LLM, image generation, TTS, etc.), it currently must hardcode provider choices. Agent Intent Protocol solves this by letting agents declare *what they need* and automatically matching them to the optimal provider.

## How It Works

```
Agent                    AIP Engine                 Providers
  |                         |                          |
  |-- Intent + Constraints →|                          |
  |                         |-- Filter & Score -----→  |
  |                         |←- Ranked matches --------|
  |←-- Best match ---------|                          |
  |                         |                          |
```

1. Agent declares an **intent** (e.g., `chat_completion`, `image_generation`)
2. Agent sets **constraints** (max price, max latency, required features)
3. Agent sets **preferences** (optimize for cost/speed/quality)
4. AIP engine returns the best-matching provider in sub-millisecond time

## Quick Start

### Install

```bash
pip install agent-intent-protocol
```

Or from source:

```bash
git clone https://github.com/api-jarvisclaw/agent-intent-protocol.git
cd agent-intent-protocol
pip install -e .
```

### Basic Usage (Python)

```python
from agent_intent_protocol import AIPClient

# Create client (defaults to https://api.jarvisclaw.ai)
client = AIPClient()

# Find the cheapest chat completion provider
result = client.resolve(
    intent="chat_completion",
    max_price_usd=0.01,
    optimize_for="cost"
)

print(f"Best: {result.best_match.provider_name}")
print(f"Model: {result.best_match.model}")
print(f"Price: ${result.best_match.price_usd}")
```

### With Constraints

```python
result = client.resolve(
    intent="image_generation",
    max_price_usd=0.05,
    max_latency_ms=10000,
    features=["photorealistic", "4k"],
    optimize_for="quality"
)
```

### Remote Mode (Live Provider Data)

```python
client = AIPClient(
    api_key="sk-your-jarvisclaw-key",
    mode="remote"  # Calls https://api.jarvisclaw.ai for live data
)
```

## REST API

Start the server:

```bash
pip install agent-intent-protocol[server]
uvicorn agent_intent_protocol.server:app --port 8900
```

### POST /v1/intent/resolve

```bash
curl -X POST http://localhost:8900/v1/intent/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "chat_completion",
    "constraints": {
      "max_price_usd": 0.01,
      "min_quality_score": 0.85
    },
    "preferences": {
      "optimize_for": "cost"
    }
  }'
```

Response:
```json
{
  "success": true,
  "intent": "chat_completion",
  "best_match": {
    "provider_id": "deepseek-v3",
    "provider_name": "DeepSeek V3",
    "model": "deepseek-chat",
    "price_usd": 0.001,
    "latency_ms": 600,
    "quality_score": 0.88,
    "features": ["function_calling", "json_mode"],
    "score": 0.9267
  },
  "alternatives": [...],
  "resolve_time_ms": 0.05
}
```

### GET /v1/intent/types

List all supported intent types.

### GET /v1/providers?intent=chat_completion

List available providers, optionally filtered by intent.

## Supported Intents

| Intent | Description | Providers |
|--------|-------------|-----------|
| `chat_completion` | Text generation / chat | GPT-4o, Claude 4, DeepSeek, Gemini |
| `image_generation` | Image creation | Ideogram 3, Flux Pro, DALL-E 3 |
| `text_to_speech` | Voice synthesis | OpenAI TTS, ElevenLabs |
| `speech_to_text` | Transcription | OpenAI Whisper |
| `embedding` | Vector embeddings | OpenAI Embed, Voyage 3 |
| `code_generation` | Code writing | Claude Code, Codex, DeepSeek Coder |
| `web_search` | Web search | Tavily, Exa |

## Constraints Reference

| Field | Type | Description |
|-------|------|-------------|
| `max_price_usd` | float | Maximum price per request |
| `max_latency_ms` | int | Maximum acceptable latency |
| `min_quality_score` | float | Minimum quality (0-1) |
| `features` | list | Required features |
| `min_context_tokens` | int | Minimum context window |

## Optimization Strategies

| Strategy | Description |
|----------|-------------|
| `balanced` | Equal weight to cost, speed, quality (default) |
| `quality` | Prioritize output quality |
| `speed` | Prioritize low latency |
| `cost` | Prioritize low price |

## Platform

This project is designed to work with [JarvisClaw](https://api.jarvisclaw.ai) — an AI API gateway with 40+ providers, x402 payment protocol, and MCP integration.

In **local mode**, AIP uses a built-in provider registry for offline resolution. In **remote mode**, it fetches live provider data from the JarvisClaw platform.

## Architecture

```
agent_intent_protocol/
├── __init__.py      # Package entry, exports
├── models.py        # Data models (Intent, Constraint, Preference, etc.)
├── resolver.py      # Core matching engine
├── client.py        # Python SDK client
└── server.py        # FastAPI REST server
```

## Contributing

Contributions are welcome! Please open an issue or submit a PR.

```bash
# Dev setup
git clone https://github.com/api-jarvisclaw/agent-intent-protocol.git
cd agent-intent-protocol
pip install -e ".[dev]"
pytest
```

## License

MIT © [JarvisClaw](https://api.jarvisclaw.ai)
