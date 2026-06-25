// AIP Quickstart — Resolve, Execute, and Discover intents.
//
// Usage:
//
//	export AIP_API_KEY="sk-your-key"
//	go run main.go
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	aip "github.com/api-jarvisclaw/agent-intent-protocol/sdks/go"
)

func main() {
	client := aip.NewClient(os.Getenv("AIP_API_KEY"))
	ctx := context.Background()

	// ── 1. Resolve: find the best provider ───────────────────────────
	fmt.Println("─── Resolve: cheapest chat completion ───")
	res, err := client.Resolve(ctx, &aip.IntentRequest{
		Intent:      "chat_completion",
		Preferences: &aip.Preferences{OptimizeFor: "cost", MaxPriceUSD: floatPtr(0.01)},
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  Provider : %s\n", res.BestMatch.ProviderName)
	fmt.Printf("  Model    : %s\n", res.BestMatch.Model)
	fmt.Printf("  Price    : $%.6f\n", res.BestMatch.PriceUSD)
	fmt.Printf("  Latency  : %dms\n", res.BestMatch.LatencyMs)

	// ── 2. Execute: run a chat completion ────────────────────────────
	fmt.Println("\n─── Execute: chat completion ───")
	exec, err := client.Execute(ctx, &aip.ExecuteRequest{
		Intent: "chat_completion",
		Payload: map[string]any{
			"messages":   []map[string]string{{"role": "user", "content": "Explain AIP in one sentence."}},
			"max_tokens": 100,
		},
		Preferences: &aip.Preferences{OptimizeFor: "quality"},
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  Provider : %s\n", exec.Provider)
	fmt.Printf("  Cost     : $%.6f\n", exec.CostUSD)

	// ── 3. Discover: list available intents ──────────────────────────
	fmt.Println("\n─── Discover: available intents ───")
	intents, err := client.ListIntents(ctx)
	if err != nil {
		log.Fatal(err)
	}
	for _, intent := range intents {
		fmt.Printf("  %s\n", intent)
	}
}

func floatPtr(f float64) *float64 { return &f }
