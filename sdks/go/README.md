# Agent Intent Protocol — Go SDK

> Declare intents, discover optimal AI providers.

## Installation

```bash
go get github.com/api-jarvisclaw/agent-intent-protocol/sdks/go/aip
```

## Usage

```go
package main

import (
    "fmt"
    "github.com/api-jarvisclaw/agent-intent-protocol/sdks/go/aip"
)

func main() {
    // Defaults to https://api.jarvisclaw.ai
    client := aip.NewClient()

    result, err := client.Resolve(aip.IntentRequest{
        Intent: aip.ChatCompletion,
        Constraints: &aip.Constraints{
            MaxPriceUSD: aip.Float64(0.01),
            Features:    []string{"function_calling"},
        },
        Preferences: &aip.Preferences{
            OptimizeFor: aip.OptimizeQuality,
        },
    })
    if err != nil {
        panic(err)
    }

    fmt.Printf("Best: %s (%s)\n", result.BestMatch.ProviderName, result.BestMatch.Model)
    fmt.Printf("Score: %.4f\n", result.BestMatch.Score)
}
```

## Custom Endpoint

```go
client := aip.NewClient(
    aip.WithEndpoint("https://your-deployment.example.com"),
    aip.WithAPIKey("your-key"),
    aip.WithTimeout(10 * time.Second),
)
```

## API

### `NewClient(opts ...ClientOption) *Client`

Creates a new AIP client.

### `Client.Resolve(req IntentRequest) (*IntentResponse, error)`

Resolves an intent to the best matching provider.

### `Client.ListIntents() ([]IntentType, error)`

Returns all supported intent types.

### `Client.ListProviders(intent IntentType) ([]ProviderMatch, error)`

Returns available providers.

## License

MIT © [JarvisClaw](https://api.jarvisclaw.ai)
