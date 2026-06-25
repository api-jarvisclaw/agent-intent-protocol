// Example usage of the AIP Go SDK.
package main

import (
	"context"
	"fmt"
	"log"

	aip "github.com/jarvisclaw/aip-go"
)

func main() {
	client := aip.NewClient("your-api-key-here")
	ctx := context.Background()

	// ─── Health Check ────────────────────────────────────────
	health, err := client.Health(ctx)
	if err != nil {
		log.Fatalf("health check failed: %v", err)
	}
	fmt.Printf("Platform status: %s (v%s)\n", health.Status, health.Version)

	// ─── Discover available services ─────────────────────────
	catalog, err := client.Discover(ctx, "")
	if err != nil {
		log.Fatalf("discover failed: %v", err)
	}
	fmt.Printf("Available intents: %d\n", len(catalog.Intents))

	// ─── Resolve an intent (without executing) ───────────────
	resolved, err := client.Resolve(ctx, &aip.IntentRequest{
		Intent: "chat",
		Constraints: &aip.Constraints{
			MaxPriceUSD:  0.01,
			MaxLatencyMs: 2000,
		},
		Preferences: &aip.Preferences{
			OptimizeFor: "quality",
		},
	})
	if err != nil {
		log.Fatalf("resolve failed: %v", err)
	}
	fmt.Printf("Best match: %s (%s) — score %.2f\n",
		resolved.BestMatch.ProviderName,
		resolved.BestMatch.Model,
		resolved.BestMatch.Score,
	)

	// ─── Chat (convenience method) ───────────────────────────
	chatResp, err := client.Chat(ctx, &aip.ChatRequest{
		Messages: []aip.ChatMessage{
			{Role: "user", Content: "Explain AIP in one sentence."},
		},
	})
	if err != nil {
		log.Fatalf("chat failed: %v", err)
	}
	fmt.Printf("Reply: %s\n", chatResp.Choices[0].Message.Content)

	// ─── Image generation ────────────────────────────────────
	imgResp, err := client.GenerateImage(ctx, "a futuristic city at sunset", map[string]any{
		"size": "1024x1024",
	})
	if err != nil {
		log.Fatalf("image gen failed: %v", err)
	}
	fmt.Printf("Image URL: %v\n", imgResp["url"])

	// ─── Search ──────────────────────────────────────────────
	searchResp, err := client.Search(ctx, "Agent Intent Protocol", nil)
	if err != nil {
		log.Fatalf("search failed: %v", err)
	}
	fmt.Printf("Search results: %v\n", searchResp["results"])
}
