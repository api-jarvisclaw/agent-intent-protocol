# Agent Intent Protocol (AIP)

> **A protocol for AI agents to declare intents and automatically discover the best-matching service providers.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-api.jarvisclaw.ai-blue)](https://api.jarvisclaw.ai)

---

## The Problem

**x402** solved "how agents pay." But who do they pay? When there are 40+ AI providers — each with different pricing, latency, quality, and capabilities — how does an agent choose?

**Agent Intent Protocol** is the answer: agents declare **what** they need, and the protocol resolves **who** best provides it.

## How It Works

```
┌─────────────┐          ┌──────────────────┐          ┌──────────────────┐
│   AI Agent  │──intent──>│   AIP Resolver   │──query──>│ Provider Registry│
│             │<─match────│                  │<─caps────│  (40+ providers) │
└─────────────┘          └──────────────────┘          └──────────────────┘
```

1. Agent declares an **intent** (e.g., "I need chat completion, under $0.01, with function calling")
2. AIP **filters** providers by hard constraints
3. AIP **scores** remaining providers by optimization preference
4. Agent receives the **best match** + ranked alternatives

## Quick Start

### Python

```bash
pip install agent-intent-protocol
```

```python
from agent_intent_protocol import AIPClient

client = AIPClient()  # → api.jarvisclaw.ai
result = client.resolve(
    intent="chat_completion",
    max_price_usd=0.01,
    optimize_for="cost"
)
print(result.best_match.provider_name)  # "DeepSeek V3"
```

### TypeScript

```bash
npm install @jarvisclaw/agent-intent-protocol
```

```typescript
import { AIPClient } from '@jarvisclaw/agent-intent-protocol';

const client = new AIPClient(); // → api.jarvisclaw.ai
const result = await client.resolve({
  intent: 'chat_completion',
  constraints: { maxPriceUsd: 0.01 },
  preferences: { optimizeFor: 'cost' },
});
console.log(result.bestMatch?.providerName); // "DeepSeek V3"
```

### Go

```go
import "github.com/api-jarvisclaw/agent-intent-protocol/sdks/go/aip"

client := aip.NewClient() // → api.jarvisclaw.ai
result, _ := client.Resolve(aip.IntentRequest{
    Intent:      aip.ChatCompletion,
    Constraints: &aip.Constraints{MaxPriceUSD: aip.Float64(0.01)},
    Preferences: &aip.Preferences{OptimizeFor: aip.OptimizeCost},
})
fmt.Println(result.BestMatch.ProviderName) // "DeepSeek V3"
```

## Supported Intent Types

| Intent | Description | Providers |
|--------|-------------|-----------|
| `chat_completion` | Text generation / chat | OpenAI, Anthropic, Google, DeepSeek, Mistral |
| `image_generation` | Image creation | DALL·E, Midjourney, Stable Diffusion |
| `text_to_speech` | Voice synthesis | ElevenLabs, OpenAI TTS |
| `speech_to_text` | Transcription | Whisper, Deepgram |
| `embedding` | Vector embeddings | OpenAI, Voyage, Cohere |
| `code_generation` | Code assistance | Codex, Claude, DeepSeek Coder |
| `web_search` | Internet search | Perplexity, Tavily, Brave |
| `moderation` | Content safety | OpenAI Moderation, Perspective |
| `translation` | Language translation | DeepL, Google Translate |

## Optimization Strategies

| Strategy | Best For |
|----------|----------|
| `balanced` | General purpose (default) |
| `quality` | Critical tasks requiring highest accuracy |
| `speed` | Real-time applications |
| `cost` | High-volume batch processing |

## Protocol Specification

See [`spec/PROTOCOL.md`](spec/PROTOCOL.md) for the full protocol specification and JSON Schema.

## Architecture

```
agent-intent-protocol/
├── spec/                    # Protocol specification & JSON Schema
│   ├── PROTOCOL.md
│   └── intent-schema-v1.json
├── sdks/
│   ├── python/             # Python SDK (pip install)
│   ├── go/                 # Go SDK (go get)
│   └── typescript/         # TypeScript SDK (npm install)
├── server/                 # Reference server implementation
├── LICENSE                 # MIT
└── README.md
```

## Default Platform

All SDKs connect to **https://api.jarvisclaw.ai** by default. Every client accepts an endpoint parameter to target custom deployments.

## Why AIP?

| Feature | AIP | Manual Selection | LLM Router |
|---------|-----|-----------------|------------|
| Declarative intents | ✅ | ❌ | ❌ |
| Multi-dimensional scoring | ✅ | ❌ | Partial |
| Hard constraint filtering | ✅ | ❌ | ❌ |
| Provider-agnostic | ✅ | ❌ | ❌ |
| Sub-millisecond resolution | ✅ | N/A | ❌ |
| Open protocol | ✅ | N/A | ❌ |

## Contributing

Contributions are welcome! See each SDK's README for development setup.

```bash
git clone https://github.com/api-jarvisclaw/agent-intent-protocol.git
cd agent-intent-protocol
```

## License

MIT © [JarvisClaw](https://api.jarvisclaw.ai)
