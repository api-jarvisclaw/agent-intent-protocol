package main

import (
	"fmt"
	"github.com/api-jarvisclaw/agent-intent-protocol/sdks/go/aip"
)

func main() {
	// Create client (defaults to https://api.jarvisclaw.ai)
	client := aip.NewClient()

	// Resolve: find cheapest chat completion
	result, err := client.Resolve(aip.IntentRequest{
		Intent: aip.ChatCompletion,
		Constraints: &aip.Constraints{
			MaxPriceUSD: aip.Float64(0.01),
		},
		Preferences: &aip.Preferences{
			OptimizeFor: aip.OptimizeCost,
		},
	})
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	if result.Success && result.BestMatch != nil {
		fmt.Printf("Best match: %s (%s)\n", result.BestMatch.ProviderName, result.BestMatch.Model)
		fmt.Printf("Price: $%.4f | Latency: %dms | Quality: %.2f\n",
			result.BestMatch.PriceUSD,
			result.BestMatch.LatencyMs,
			result.BestMatch.QualityScore)
		fmt.Printf("Score: %.4f\n", result.BestMatch.Score)
	}
}
