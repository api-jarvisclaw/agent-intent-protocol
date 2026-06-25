"""
AIP Multi-Intent — Chain multiple intents in a single workflow.

Demonstrates using AIP as a universal router: one client, many capabilities.

Usage:
    export AIP_API_KEY="sk-your-key"
    python multi_intent.py
"""
import os
from agent_intent_protocol import AIPClient


def main():
    client = AIPClient(api_key=os.environ.get("AIP_API_KEY"))

    # Step 1: Web search
    print("─── Step 1: Web Search ───")
    search = client.execute(
        intent="web_search",
        payload={"query": "Agent Intent Protocol specification"},
    )
    print(f"  Found {len(search.result.get('results', []))} results")

    # Step 2: Summarize search results with chat
    print("\n─── Step 2: Summarize with Chat ───")
    snippets = "\n".join(
        r.get("snippet", "") for r in search.result.get("results", [])[:3]
    )
    summary = client.execute(
        intent="chat_completion",
        payload={
            "messages": [
                {"role": "system", "content": "Summarize the following search results concisely."},
                {"role": "user", "content": snippets},
            ],
            "max_tokens": 200,
        },
        optimize_for="quality",
    )
    print(f"  Summary: {summary.result['choices'][0]['message']['content']}")

    # Step 3: Generate an image based on the summary
    print("\n─── Step 3: Generate Image ───")
    image = client.execute(
        intent="image_generation",
        payload={
            "prompt": f"A conceptual diagram of: {summary.result['choices'][0]['message']['content'][:100]}",
            "size": "1024x1024",
        },
    )
    print(f"  Image URL: {image.result.get('url', 'N/A')}")

    # Step 4: Text-to-speech of the summary
    print("\n─── Step 4: Text to Speech ───")
    tts = client.execute(
        intent="text_to_speech",
        payload={
            "text": summary.result["choices"][0]["message"]["content"],
            "voice": "alloy",
        },
    )
    print(f"  Audio format: {tts.result.get('format', 'mp3')}")
    print(f"  Audio size: {tts.result.get('size_bytes', 'N/A')} bytes")

    # Total cost summary
    total = sum(r.cost_usd for r in [search, summary, image, tts] if r.cost_usd)
    print(f"\n─── Total cost: ${total:.6f} ───")


if __name__ == "__main__":
    main()
