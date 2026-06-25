// AIP Multi-Intent — Chain search → summarize → image → TTS in one workflow.
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

	// Step 1: Web search
	fmt.Println("─── Step 1: Web Search ───")
	search, err := client.Search(ctx, "Agent Intent Protocol specification", nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  Found results in %.0fms\n", search.LatencyMs)

	// Step 2: Summarize with chat
	fmt.Println("\n─── Step 2: Summarize ───")
	summary, err := client.Chat(ctx, &aip.ChatRequest{
		Messages: []aip.Message{
			{Role: "system", Content: "Summarize concisely."},
			{Role: "user", Content: fmt.Sprintf("Summarize: %v", search.Result)},
		},
		MaxTokens: intPtr(200),
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  Summary: %s\n", summary.Choices[0].Message.Content[:80])

	// Step 3: Generate image
	fmt.Println("\n─── Step 3: Image Generation ───")
	img, err := client.GenerateImage(ctx, summary.Choices[0].Message.Content[:100], nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  Image URL: %v\n", img.Result["url"])

	// Step 4: Text to speech
	fmt.Println("\n─── Step 4: TTS ───")
	tts, err := client.TextToSpeech(ctx, summary.Choices[0].Message.Content, map[string]any{"voice": "alloy"})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  Audio format: %v\n", tts.Result["format"])
}

func intPtr(i int) *int { return &i }
