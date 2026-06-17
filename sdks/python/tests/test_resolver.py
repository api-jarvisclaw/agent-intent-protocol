"""Tests for the AIP client with real JarvisClaw API integration."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_intent_protocol import AIPClient, IntentResult, Constraints


def test_resolve_chat_balanced():
    client = AIPClient()
    result = client.resolve("chat_completion", optimize_for="balanced")
    assert result.success
    assert result.model in [m["id"] for m in client.list_models()]
    assert "api.jarvisclaw.ai" in result.endpoint
    print(f"  PASS: balanced -> {result.model} (score={result.score})")


def test_resolve_cost_optimized():
    client = AIPClient()
    result = client.resolve("chat_completion", optimize_for="cost")
    assert result.success
    # Cost-optimized should prefer free models
    model_info = [m for m in client.list_models() if m["id"] == result.model][0]
    assert model_info["price_output"] == 0, f"Cost-optimized picked paid model: {result.model}"
    print(f"  PASS: cost -> {result.model} (free tier)")


def test_resolve_quality_optimized():
    client = AIPClient()
    result = client.resolve("chat_completion", optimize_for="quality")
    assert result.success
    model_info = [m for m in client.list_models() if m["id"] == result.model][0]
    assert model_info["quality"] >= 0.9, f"Quality-optimized picked low-quality: {result.model}"
    print(f"  PASS: quality -> {result.model} (quality={model_info['quality']})")


def test_resolve_speed_optimized():
    client = AIPClient()
    result = client.resolve("chat_completion", optimize_for="speed")
    assert result.success
    model_info = [m for m in client.list_models() if m["id"] == result.model][0]
    assert model_info["latency_ms"] <= 500, f"Speed-optimized picked slow model: {result.model}"
    print(f"  PASS: speed -> {result.model} (latency={model_info['latency_ms']}ms)")


def test_constraints_free_only():
    client = AIPClient()
    constraints = Constraints(tier="free")
    result = client.resolve("chat_completion", constraints=constraints)
    assert result.success
    model_info = [m for m in client.list_models() if m["id"] == result.model][0]
    assert model_info["tier"] == "free"
    print(f"  PASS: free-only -> {result.model}")


def test_constraints_max_price():
    client = AIPClient()
    constraints = Constraints(max_price_output=2.0)
    result = client.resolve("chat_completion", constraints=constraints)
    assert result.success
    model_info = [m for m in client.list_models() if m["id"] == result.model][0]
    assert model_info["price_output"] <= 2.0
    print(f"  PASS: max_price_output<=2.0 -> {result.model} (${model_info['price_output']})")


def test_constraints_min_quality():
    client = AIPClient()
    constraints = Constraints(min_quality=0.95)
    result = client.resolve("chat_completion", constraints=constraints)
    assert result.success
    model_info = [m for m in client.list_models() if m["id"] == result.model][0]
    assert model_info["quality"] >= 0.95
    print(f"  PASS: min_quality>=0.95 -> {result.model}")


def test_constraints_exclude():
    client = AIPClient()
    constraints = Constraints(exclude_models=["openai/gpt-5.5", "anthropic/claude-opus-4.7"])
    result = client.resolve("chat_completion", optimize_for="quality", constraints=constraints)
    assert result.success
    assert result.model not in constraints.exclude_models
    print(f"  PASS: excluded gpt-5.5/opus -> {result.model}")


def test_constraints_no_match():
    client = AIPClient()
    constraints = Constraints(max_latency_ms=10)  # Impossible
    result = client.resolve("chat_completion", constraints=constraints)
    assert not result.success
    print(f"  PASS: no match returns success=False")


def test_unknown_intent():
    client = AIPClient()
    result = client.resolve("teleportation")
    assert not result.success
    assert "Unknown intent" in result.reason
    print(f"  PASS: unknown intent handled")


def test_image_generation_intent():
    client = AIPClient()
    result = client.resolve("image_generation")
    assert result.success
    assert "/v1/images/generations" in result.endpoint
    print(f"  PASS: image_generation -> {result.endpoint}")


def test_video_generation_intent():
    client = AIPClient()
    result = client.resolve("video_generation")
    assert result.success
    assert "/v1/videos/generations" in result.endpoint
    print(f"  PASS: video_generation -> {result.endpoint}")


def test_web_search_intent():
    client = AIPClient()
    result = client.resolve("web_search")
    assert result.success
    assert "/v1/search" in result.endpoint
    print(f"  PASS: web_search -> {result.endpoint}")


def test_marketplace_intent():
    client = AIPClient()
    result = client.resolve("prediction_market")
    assert result.success
    assert "/v1/marketplace/prediction" in result.endpoint
    print(f"  PASS: prediction_market -> {result.endpoint}")


def test_list_models():
    client = AIPClient()
    all_models = client.list_models()
    free_models = client.list_models(tier="free")
    paid_models = client.list_models(tier="premium")
    assert len(all_models) >= 14
    assert len(free_models) >= 6
    assert len(paid_models) >= 5
    print(f"  PASS: list_models -> {len(all_models)} total, {len(free_models)} free, {len(paid_models)} premium")


def test_list_services():
    client = AIPClient()
    services = client.list_services()
    assert "chat_completion" in services
    assert "image_generation" in services
    assert "web_search" in services
    assert "prediction_market" in services
    assert all("api.jarvisclaw.ai" in v for v in services.values())
    print(f"  PASS: list_services -> {len(services)} services")


def test_alternatives():
    client = AIPClient()
    result = client.resolve("chat_completion", top_k=5)
    assert result.success
    assert len(result.alternatives) >= 2
    # Alternatives should be sorted by score
    scores = [result.score] + [a["score"] for a in result.alternatives]
    assert scores == sorted(scores, reverse=True)
    print(f"  PASS: alternatives -> {len(result.alternatives)} alternatives, sorted by score")


def test_resolve_time():
    client = AIPClient()
    result = client.resolve("chat_completion")
    assert result.resolve_time_ms < 10  # Should be sub-millisecond (local computation)
    print(f"  PASS: resolve_time={result.resolve_time_ms:.3f}ms (sub-10ms)")


def test_custom_endpoint():
    client = AIPClient(endpoint="https://custom.example.com")
    result = client.resolve("chat_completion")
    assert "custom.example.com" in result.endpoint
    print(f"  PASS: custom endpoint -> {result.endpoint}")


if __name__ == "__main__":
    tests = [
        test_resolve_chat_balanced,
        test_resolve_cost_optimized,
        test_resolve_quality_optimized,
        test_resolve_speed_optimized,
        test_constraints_free_only,
        test_constraints_max_price,
        test_constraints_min_quality,
        test_constraints_exclude,
        test_constraints_no_match,
        test_unknown_intent,
        test_image_generation_intent,
        test_video_generation_intent,
        test_web_search_intent,
        test_marketplace_intent,
        test_list_models,
        test_list_services,
        test_alternatives,
        test_resolve_time,
        test_custom_endpoint,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__} — {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__} — {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
