# Agent Intent Protocol — TypeScript SDK

> Declare intents, discover optimal AI providers.

## Installation

```bash
npm install @jarvisclaw/agent-intent-protocol
# or
pnpm add @jarvisclaw/agent-intent-protocol
```

## Usage

```typescript
import { AIPClient } from '@jarvisclaw/agent-intent-protocol';

// Defaults to https://api.jarvisclaw.ai
const client = new AIPClient();

const result = await client.resolve({
  intent: 'chat_completion',
  constraints: {
    maxPriceUsd: 0.01,
    features: ['function_calling'],
  },
  preferences: {
    optimizeFor: 'quality',
  },
});

if (result.success && result.bestMatch) {
  console.log(`Best: ${result.bestMatch.providerName}`);
  console.log(`Model: ${result.bestMatch.model}`);
  console.log(`Score: ${result.bestMatch.score}`);
}
```

## Custom Endpoint

```typescript
const client = new AIPClient({
  endpoint: 'https://your-deployment.example.com',
  apiKey: 'your-key',
  timeout: 10000,
});
```

## API

### `new AIPClient(options?)`

| Option | Type | Default |
|--------|------|---------|
| `endpoint` | `string` | `https://api.jarvisclaw.ai` |
| `apiKey` | `string` | — |
| `timeout` | `number` | `30000` |
| `fetch` | `typeof fetch` | `globalThis.fetch` |

### `client.resolve(request): Promise<IntentResponse>`

Resolve an intent to the best matching provider.

### `client.listIntents(): Promise<IntentType[]>`

Returns all supported intent types.

### `client.listProviders(intent?): Promise<ProviderMatch[]>`

Returns available providers.

### `client.health(): Promise<{ status, version }>`

Health check.

## Development

```bash
cd sdks/typescript
npm install
npm test
npm run build
```

## Requirements

- Node.js >= 18.0.0 (uses native fetch)

## License

MIT © [JarvisClaw](https://api.jarvisclaw.ai)
