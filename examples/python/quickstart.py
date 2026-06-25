"""
AIP Quickstart — Resolve, Execute, and Discover intents in one script.

Usage:
    export AIP_API_KEY="sk-your-key"
    python quickstart.py
"""
import os
from agent_intent_protocol import AIPClient


def main():
    client = AIPClient(api_key=os.environ.get("AIP_API_KEY"))

    # ── 1. Resolve: find the best provider for a chat intent ──────────
    print("─── Resolve: cheapest chat completion ───")
    result = client.resolve(
        intent="chat_completion",
        max_price_usd=0.01,
        optimize_for="cost",
    )
    if result.success:
        m = result.best_match
        print(f"  Provider : {m.provider_name}")
        print(f"  Model    : {m.model}")
        print(f"  Price    : ${m.price_usd}")
        print(f"  Latency  : {m.latency_ms}ms")

    # ── 2. Execute: run a chat completion end-to-end ──────────────────
    print("\n─── Execute: chat completion ───")
    response = client.execute(
        intent="chat_completion",
        payload={
            "messages": [{"role": "user", "content": "Explain AIP in one sentence."}],
            "max_tokens": 100,
        },
        optimize_for="quality",
    )
    if response.success:
        print(f"  Provider used : {response.provider}")
        print(f"  Response      : {response.result['choices'][0]['message']['content']}")
        print(f"  Cost          : ${response.cost_usd}")

    # ── 3. Discover: list all available intents ───────────────────────
    print("\n─── Discover: available intents ───")
    for intent in client.list_intents():
        providers = client.list_providers(intent)
        print(f"  {intent}: {len(providers)} providers")


if __name__ == "__main__":
    main()
