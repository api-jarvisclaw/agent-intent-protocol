# AIP Go SDK

A thin HTTP client for the **Agent Intent Protocol** platform.

Agents declare *what* they need — the platform decides *how* to fulfill it.

## Installation

```bash
go get github.com/jarvisclaw/aip-go
```

## Quick Start

```go
package main

import (
    "context"
    "fmt"
    "log"

    aip "github.com/jarvisclaw/aip-go"
)

func main() {
    client := aip.NewClient("your-api-key")
    ctx := context.Background()

    // Resolve an intent to the best provider
    resp, err := client.Resolve(ctx, &aip.IntentRequest{
        Intent: "chat",
        Preferences: &aip.Preferences{OptimizeFor: "quality"},
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Best: %s (%s)\n", resp.BestMatch.ProviderName, resp.BestMatch.Model)

    // Or execute directly
    chat, err := client.Chat(ctx, &aip.ChatRequest{
        Messages: []aip.ChatMessage{
            {Role: "user", Content: "Hello!"},
        },
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println(chat.Choices[0].Message.Content)
}
```

## API Reference

### Core Methods

| Method | Description |
|--------|-------------|
| `Resolve(ctx, req)` | Resolve intent to best provider without executing |
| `Execute(ctx, req)` | Resolve + execute in one call |
| `Discover(ctx, category)` | List available intents, services, and models |

### Convenience Methods

| Method | Description |
|--------|-------------|
| `Chat(ctx, req)` | Chat completion via AIP intent routing |
| `ChatDirect(ctx, req)` | Direct OpenAI-compatible chat endpoint |
| `GenerateImage(ctx, prompt, opts)` | Image generation |
| `GenerateVideo(ctx, prompt, opts)` | Video generation |
| `TextToSpeech(ctx, text, opts)` | Text-to-speech |
| `Search(ctx, query, opts)` | Web search |
| `Marketplace(ctx, action, params)` | Marketplace interaction |

### Utility

| Method | Description |
|--------|-------------|
| `Health(ctx)` | Platform health check |
| `Models(ctx)` | List available AI models |

## Configuration

```go
// Custom endpoint
client := aip.NewClient("key", aip.WithEndpoint("https://custom.api"))

// Custom HTTP client
client := aip.NewClient("key", aip.WithHTTPClient(myHTTPClient))

// Custom timeout
client := aip.NewClient("key", aip.WithTimeout(60 * time.Second))
```

## Error Handling

```go
resp, err := client.Resolve(ctx, req)
if err != nil {
    var apiErr *aip.Error
    if errors.As(err, &apiErr) {
        if apiErr.IsRateLimit() {
            // back off and retry
        }
        fmt.Printf("API error [%d]: %s\n", apiErr.StatusCode, apiErr.Message)
    }
}
```

## License

MIT
