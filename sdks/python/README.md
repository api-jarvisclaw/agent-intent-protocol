# Agent Intent Protocol — Python SDK

> Declare intents, discover optimal AI providers.

## Installation

```bash
pip install agent-intent-protocol
```

## Usage

```python
from agent_intent_protocol import AIPClient

# Defaults to https://api.jarvisclaw.ai
client = AIPClient()

# Find the best provider for your needs
result = client.resolve(
    intent="chat_completion",
    max_price_usd=0.01,
    min_quality_score=0.8,
    features=["function_calling"],
    optimize_for="balanced"
)

if result.success:
    print(f"Best: {result.best_match.provider_name}")
    print(f"Model: {result.best_match.model}")
    print(f"Score: {result.best_match.score}")
```

## Custom Endpoint

```python
client = AIPClient(endpoint="https://your-deployment.example.com")
```

## API

### `AIPClient.resolve(intent, **kwargs) -> MatchResult`

Resolve an intent to the best provider.

**Parameters:**
- `intent` — Intent type (e.g., `"chat_completion"`)
- `max_price_usd` — Maximum price constraint
- `max_latency_ms` — Maximum latency constraint
- `min_quality_score` — Minimum quality threshold
- `features` — Required features list
- `exclude_providers` — Providers to exclude
- `optimize_for` — Optimization strategy: `"balanced"`, `"quality"`, `"speed"`, `"cost"`

### `AIPClient.list_intents() -> list[str]`

Returns all supported intent types.

### `AIPClient.list_providers(intent?) -> list[dict]`

Returns available providers, optionally filtered.

## Development

```bash
cd sdks/python
pip install -e ".[dev]"
pytest
```

## License

MIT © [JarvisClaw](https://api.jarvisclaw.ai)
