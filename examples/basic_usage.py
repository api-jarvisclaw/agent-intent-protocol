"""
Example: Basic intent resolution
"""
from agent_intent_protocol import AIPClient

def main():
    # Create a client (defaults to https://api.jarvisclaw.ai)
    client = AIPClient()

    # Example 1: Find cheapest chat completion
    print("=== Cheapest Chat Completion ===")
    result = client.resolve(
        intent="chat_completion",
        max_price_usd=0.01,
        optimize_for="cost"
    )
    if result.success:
        print(f"  Provider: {result.best_match.provider_name}")
        print(f"  Model:    {result.best_match.model}")
        print(f"  Price:    ${result.best_match.price_usd}")
        print(f"  Latency:  {result.best_match.latency_ms}ms")
        print(f"  Resolved in {result.resolve_time_ms:.3f}ms")

    # Example 2: Highest quality image generation
    print("\n=== Best Quality Image Generation ===")
    result = client.resolve(
        intent="image_generation",
        features=["photorealistic"],
        optimize_for="quality"
    )
    if result.success:
        print(f"  Provider: {result.best_match.provider_name}")
        print(f"  Model:    {result.best_match.model}")
        print(f"  Price:    ${result.best_match.price_usd}")
        print(f"  Score:    {result.best_match.score}")

    # Example 3: Fast code generation
    print("\n=== Fastest Code Generation ===")
    result = client.resolve(
        intent="code_generation",
        optimize_for="speed"
    )
    if result.success:
        print(f"  Provider: {result.best_match.provider_name}")
        print(f"  Model:    {result.best_match.model}")
        print(f"  Latency:  {result.best_match.latency_ms}ms")

    # Example 4: Chat with long context requirement
    print("\n=== Long Context Chat (>100k tokens) ===")
    result = client.resolve(
        intent="chat_completion",
        min_quality_score=0.9,
        optimize_for="quality",
    )
    if result.success:
        print(f"  Provider: {result.best_match.provider_name}")
        print(f"  Model:    {result.best_match.model}")
        print(f"  Quality:  {result.best_match.quality_score}")
        print(f"  Alternatives: {len(result.alternatives)}")
        for alt in result.alternatives[:3]:
            print(f"    - {alt.provider_name} (score: {alt.score})")

    # Example 5: List all available intents
    print("\n=== Supported Intents ===")
    for intent in client.list_intents():
        providers = client.list_providers(intent)
        print(f"  {intent}: {len(providers)} providers")


if __name__ == "__main__":
    main()
