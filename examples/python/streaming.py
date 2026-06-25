"""
AIP Streaming — Subscribe to a streaming intent (SSE).

Usage:
    export AIP_API_KEY="sk-your-key"
    python streaming.py
"""
import os
from agent_intent_protocol import AIPClient


def main():
    client = AIPClient(api_key=os.environ.get("AIP_API_KEY"))

    print("─── Streaming chat completion ───")
    stream = client.subscribe(
        intent="chat_completion",
        payload={
            "messages": [
                {"role": "user", "content": "Write a haiku about distributed systems."}
            ],
            "stream": True,
        },
        optimize_for="speed",
    )

    print("  Response: ", end="", flush=True)
    for chunk in stream:
        if chunk.delta:
            print(chunk.delta, end="", flush=True)
    print(f"\n  Total tokens: {stream.usage.total_tokens}")
    print(f"  Cost: ${stream.cost_usd}")


if __name__ == "__main__":
    main()
