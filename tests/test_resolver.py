"""Tests for Agent Intent Protocol."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_intent_protocol import AIPClient, IntentResolver
from agent_intent_protocol.models import Intent, Constraint, Preference, OptimizeFor


def test_basic_resolve():
    """Test basic intent resolution."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion")
    assert result.success
    assert result.best_match is not None
    assert result.best_match.provider_id


def test_cost_optimization():
    """Test that cost optimization returns cheapest provider."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion", optimize_for="cost")
    assert result.success
    # DeepSeek is cheapest at $0.001
    assert result.best_match.provider_id == "deepseek-v3"


def test_quality_optimization():
    """Test that quality optimization returns highest quality."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion", optimize_for="quality")
    assert result.success
    assert result.best_match.quality_score >= 0.9


def test_speed_optimization():
    """Test that speed optimization returns fastest provider."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion", optimize_for="speed")
    assert result.success
    # Google Gemini has lowest latency at 500ms
    assert result.best_match.provider_id == "google-gemini"


def test_price_constraint():
    """Test price constraint filtering."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion", max_price_usd=0.002)
    assert result.success
    assert result.best_match.price_usd <= 0.002


def test_feature_constraint():
    """Test feature requirement filtering."""
    client = AIPClient()
    result = client.resolve(intent="image_generation", features=["photorealistic", "4k"])
    assert result.success
    assert "photorealistic" in result.best_match.features
    assert "4k" in result.best_match.features


def test_no_match():
    """Test when no provider matches constraints."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion", max_price_usd=0.0001)
    assert not result.success
    assert result.best_match is None


def test_unknown_intent():
    """Test resolution with unknown intent type."""
    client = AIPClient()
    result = client.resolve(intent="teleportation")
    assert not result.success


def test_exclusion():
    """Test provider exclusion."""
    client = AIPClient()
    result = client.resolve(
        intent="chat_completion",
        optimize_for="cost",
        excluded_providers=["deepseek-v3"]
    )
    assert result.success
    assert result.best_match.provider_id != "deepseek-v3"


def test_list_intents():
    """Test listing supported intents."""
    client = AIPClient()
    intents = client.list_intents()
    assert "chat_completion" in intents
    assert "image_generation" in intents


def test_list_providers():
    """Test listing providers."""
    client = AIPClient()
    providers = client.list_providers(intent="chat_completion")
    assert len(providers) >= 3


def test_resolve_time():
    """Test that resolution is fast (sub-millisecond)."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion")
    assert result.resolve_time_ms < 10  # Should be well under 1ms


def test_alternatives():
    """Test that alternatives are returned."""
    client = AIPClient()
    result = client.resolve(intent="chat_completion")
    assert result.success
    assert len(result.alternatives) > 0


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__} - {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
