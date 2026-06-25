# Agent Intent Protocol (AIP)

> **One interface for AI agents to use all platform capabilities — routing, execution, and discovery.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-api.jarvisclaw.ai-blue)](https://api.jarvisclaw.ai)
[![Version](https://img.shields.io/badge/protocol-v2.0-green)](spec/PROTOCOL.md)

---

## The Idea

An AI agent shouldn't need to know about 40+ providers, their APIs, pricing models, or capabilities. It should just say what it wants and get results.

**Agent Intent Protocol** is that single interface: declare an intent, optionally set constraints, and the platform handles provider selection, execution, and billing.

## How It Works

```
┌─────────────┐          ┌──────────────────┐          ┌──────────────────┐
│   AI Agent  │──intent──>│   AIP Platform   │──route──>│  40+ Providers   │
│             │<─result───│  (resolve+exec)  │<─data────│  (AI/Media/Web)  │
└─────────────┘          └──────────────────┘          └──────────────────┘
```

1. Agent sends an **intent** + **payload** (e.g., "chat completion with these messages")
2. Platform **resolves** the best provider based on constraints and optimization strategy
3. Platform **executes** the request and returns the result
4. Agent gets the response + metadata (model used, cost, latency)

## Quick Start

### Python

```bash
pip install agent-intent-protocol
```

```python
from agent_intent_protocol import AIPClient

client = AIPClient(api_key="sk-xxx")

# Execute: one call does everything
result = client.execute(
    intent="chat_completion",
    payload={
        "messages": [{"role": "user", "content": "Hello!"}],
        "temperature": 0.7,
    },
    optimize_for="balanced",
)
print(result["data"]["choices"][0]["message"]["content"])
print(result["meta"]["model"])  # e.g. "gpt-4o-mini"
print(result["meta"]["cost_usd"])  # e.g. 0.000185

# Discover: see what's available
catalog = client.discover()
print([i["name"] for i in catalog["intents"]])

# Resolve only (no execution)
resolution = client.resolve(intent="image_generation", optimize_for="quality")
print(resolution["resolution"]["model"])  # e.g. "dall-e-3"
```

### TypeScript

```bash
npm install @jarvisclaw/agent-intent-protocol
```

```typescript
import { AIPClient } from '@jarvisclaw/agent-intent-protocol';

const client = new AIPClient({ apiKey: 'sk-xxx' });

// Execute: one call does everything
const result = await client.execute({
  intent: 'chat_completion',
  payload: {
    messages: [{ role: 'user', content: 'Hello!' }],
  },
  optimizeFor: 'balanced',
});
console.log(result.data.choices[0].message.content);
console.log(result.meta.model); // "gpt-4o-mini"

// Discover available capabilities
const catalog = await client.discover();
console.log(catalog.intents.map(i => i.name));

// Streaming
const stream = client.stream({
  intent: 'chat_completion',
  payload: { messages: [{ role: 'user', content: 'Tell me a story' }] },
});
for await (const chunk of stream) {
  process.stdout.write(chunk);
}
```

## Supported Intents

| Intent | Description | Example Providers |
|--------|-------------|-------------------|
| `chat_completion` | Text generation / chat | OpenAI, Anthropic, Google, DeepSeek, Mistral |
| `image_generation` | Image creation | DALL·E 3, Stable Diffusion XL, Midjourney |
| `video_generation` | Video from text | Runway, Pika, Kling |
| `text_to_speech` | Voice synthesis | ElevenLabs, OpenAI TTS |
| `speech_to_text` | Transcription | Whisper, Deepgram |
| `embedding` | Vector embeddings | OpenAI, Voyage, Cohere |
| `web_search` | Internet search | Perplexity, Tavily, Brave |
| `code_generation` | Code assistance | Claude, DeepSeek Coder |
| `translation` | Language translation | DeepL, Google Translate |
| `moderation` | Content safety | OpenAI Moderation |

Use `client.discover()` to get the live catalog with all available intents.

## Optimization Strategies

| Strategy | Best For |
|----------|----------|
| `balanced` | General purpose (default) |
| `quality` | Critical tasks, highest accuracy |
| `speed` | Real-time / low-latency applications |
| `cost` | High-volume batch processing |

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/aip/execute` | Resolve + execute in one call |
| POST | `/v1/aip/resolve` | Resolve only (inspect best match) |
| GET | `/v1/aip/discover` | List all intents, models, services |
| GET | `/v1/aip/health` | Platform health check |

See [`spec/PROTOCOL.md`](spec/PROTOCOL.md) for the full specification.

## Examples

Runnable examples for every SDK and raw HTTP — see [`examples/`](examples/):

```bash
# Python
pip install agent-intent-protocol
python examples/python/quickstart.py

# Go
cd examples/go/quickstart && go run main.go

# TypeScript
npx tsx examples/typescript/quickstart.ts

# curl
export AIP_API_KEY="sk-your-key"
bash examples/curl/execute.sh
```

Each language includes quickstart, streaming, and multi-intent workflow demos.

## Architecture

```
agent-intent-protocol/
├── spec/                    # Protocol specification & JSON Schema
│   ├── PROTOCOL.md         # v2.0 spec
│   └── intent-schema-v2.json
├── sdks/
│   ├── python/             # Python SDK (pip install)
│   ├── go/                 # Go SDK (go get)
│   └── typescript/         # TypeScript SDK (npm install)
├── examples/               # Runnable examples (Python, Go, TS, curl)
├── LICENSE                 # MIT
└── README.md
```

## Why AIP?

| | Without AIP | With AIP |
|---|---|---|
| Provider selection | Manual research per task | Automatic, constraint-based |
| API integration | N different SDKs | One SDK, one interface |
| Cost optimization | Manual price comparison | Built-in optimization strategies |
| New providers | Code changes required | Instantly available |
| Billing | N billing relationships | Single platform billing |

## Default Platform

All SDKs connect to **https://api.jarvisclaw.ai** by default. Every client accepts an `endpoint` parameter for custom deployments.

## Contributing

```bash
git clone https://github.com/api-jarvisclaw/agent-intent-protocol.git
cd agent-intent-protocol
```

See each SDK's directory for development setup.

## License

MIT © [JarvisClaw](https://api.jarvisclaw.ai)
