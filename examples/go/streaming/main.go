// AIP Streaming — Subscribe to SSE stream for chat completion.
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

	fmt.Println("─── Streaming chat completion ───")
	stream, err := client.Subscribe(ctx, &aip.SubscribeRequest{
		Intent: "chat_completion",
		Payload: map[string]any{
			"messages": []map[string]string{
				{"role": "user", "content": "Write a haiku about distributed systems."},
			},
			"stream": true,
		},
		Preferences: &aip.Preferences{OptimizeFor: "speed"},
	})
	if err != nil {
		log.Fatal(err)
	}
	defer stream.Close()

	fmt.Print("  Response: ")
	for stream.Next() {
		chunk := stream.Current()
		if chunk.Delta != "" {
			fmt.Print(chunk.Delta)
		}
	}
	if err := stream.Err(); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\n  Total tokens: %d\n", stream.Usage().TotalTokens)
	fmt.Printf("  Cost: $%.6f\n", stream.CostUSD())
}
