# AIP Examples

Runnable examples for every supported SDK and raw HTTP (curl).

## Structure

```
examples/
├── python/          # Python SDK examples
│   ├── quickstart.py
│   ├── streaming.py
│   └── multi_intent.py
├── go/              # Go SDK examples
│   ├── quickstart/main.go
│   ├── streaming/main.go
│   └── multi_intent/main.go
├── typescript/      # TypeScript SDK examples
│   ├── quickstart.ts
│   ├── streaming.ts
│   └── multi_intent.ts
└── curl/            # Raw HTTP examples
    ├── resolve.sh
    ├── execute.sh
    └── discover.sh
```

## Prerequisites

- An API key from [api.jarvisclaw.ai](https://api.jarvisclaw.ai)
- Set `AIP_API_KEY` environment variable (or pass directly in code)

## Running

### Python
```bash
pip install agent-intent-protocol
cd examples/python
python quickstart.py
```

### Go
```bash
cd examples/go/quickstart
go run main.go
```

### TypeScript
```bash
npm install @jarvisclaw/agent-intent-protocol
cd examples/typescript
npx tsx quickstart.ts
```

### curl
```bash
export AIP_API_KEY="sk-your-key"
cd examples/curl
bash resolve.sh
```
