"""Tests for the API marketplace methods.

Mocked payloads are copied from live responses of the gateway
(GET /api/marketplace/apis, GET /api/marketplace/apis/{ref}) so these double as
a contract check: the envelope shape, the `q` parameter name, and the
slug-based invocation path are all things the SDK got wrong or missed before.
"""

from __future__ import annotations

import httpx
import pytest

from agent_intent_protocol import (
    AIPClient,
    AsyncAIPClient,
    IntentType,
    MarketplaceAPI,
    MarketplacePage,
)

# One page as the gateway actually returns it: payload under "data", alongside
# a "success" flag, with catalogue-wide totals next to the page's items.
PAGE_BODY = {
    "success": True,
    "data": {
        "items": [
            {
                "service_id": "federation/3570",
                "name": "Audio To Text",
                "category": "audio",
                "price_unit": "call",
                "display_price": 0.0115,
                "resource_id": 3570,
                "slug": "audio-to-text",
                "server_name": "",
                "method": "POST",
                "description": "",
                "tags": "",
                "source": "federation",
                "call_count": 0,
                "popular": False,
            }
        ],
        "total": 2720,
        "page": 1,
        "page_size": 50,
        "categories": [
            {"category": "general", "count": 1312},
            {"category": "audio", "count": 9},
        ],
    },
}


def make_client(handler) -> AIPClient:
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    return AIPClient(api_key="sk-test", http_client=http, endpoint="https://api.test")


def test_search_apis_unwraps_envelope_and_keeps_catalogue_total():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=PAGE_BODY)

    page = make_client(handler).search_apis("audio")

    assert isinstance(page, MarketplacePage)
    # total is the filtered catalogue size, deliberately not len(items) — a
    # caller needs to tell "2,720 exist" from "1 was returned on this page".
    assert page.total == 2720
    assert len(page) == 1
    assert page.items[0].name == "Audio To Text"
    assert page.categories[0]["count"] == 1312


def test_search_apis_sends_q_not_search():
    """The gateway's free-text parameter is `q`.

    `search=` is accepted but ignored, which silently returns the unfiltered
    catalogue — a wrong-but-successful call, so only a parameter-name
    assertion catches it.
    """
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json=PAGE_BODY)

    make_client(handler).search_apis("weather", category="geo", page=2, page_size=10)

    assert "q=weather" in captured["url"]
    assert "search=" not in captured["url"]
    assert "category=geo" in captured["url"]
    assert "page=2" in captured["url"]
    assert "page_size=10" in captured["url"]


def test_search_apis_omits_query_when_absent():
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json=PAGE_BODY)

    make_client(handler).search_apis()

    assert "q=" not in captured["url"]


def test_get_api_accepts_slug_and_id():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, json={"success": True, "data": PAGE_BODY["data"]["items"][0]})

    client = make_client(handler)
    by_slug = client.get_api("audio-to-text")
    by_id = client.get_api(3570)

    assert seen == [
        "/api/marketplace/apis/audio-to-text",
        "/api/marketplace/apis/3570",
    ]
    assert isinstance(by_slug, MarketplaceAPI)
    assert by_slug.resource_id == by_id.resource_id == 3570
    assert by_slug.display_price == 0.0115


def test_invocation_path_prefers_slug():
    """The slug outlives an upstream renaming its resource; the id may not."""
    entry = MarketplaceAPI.from_dict(PAGE_BODY["data"]["items"][0])
    assert entry.path == "/v1/marketplace/api/audio-to-text"

    # Without a slug the numeric id is the only addressable form.
    no_slug = MarketplaceAPI.from_dict({"resource_id": 42, "name": "X"})
    assert no_slug.path == "/v1/marketplace/api/42"


def test_call_api_posts_payload_to_the_resource():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["method"] = request.method
        captured["body"] = request.content
        return httpx.Response(200, json={"result": "ok"})

    result = make_client(handler).call_api("audio-to-text", {"url": "https://a.wav"})

    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/marketplace/api/audio-to-text"
    assert b"https://a.wav" in captured["body"]  # type: ignore[operator]
    assert result == {"result": "ok"}


def test_call_api_sends_empty_object_when_payload_omitted():
    """An empty body is how the gateway is asked to quote rather than execute."""
    captured: dict[str, bytes] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content
        return httpx.Response(200, json={})

    make_client(handler).call_api(3570)

    assert captured["body"] == b"{}"


def test_call_api_uses_the_verb_the_catalogue_published():
    """~45% of the catalogue is GET, so POST cannot be assumed.

    Passing the entry itself is the only form that knows the verb without a
    second lookup. The gateway currently tolerates POST on a GET route, so a
    status assertion would not catch this — only the recorded method does.
    """
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"ok": True})

    get_entry = MarketplaceAPI.from_dict(
        {"resource_id": 91, "name": "Aviation Metar", "slug": "aviation-metar", "method": "GET"}
    )
    make_client(handler).call_api(get_entry, {"station": "RJTT"})

    assert captured["method"] == "GET"
    # On a GET the payload rides the query string: not every upstream reads a
    # GET body.
    assert "station=RJTT" in captured["url"]


def test_call_api_defaults_to_post_for_a_bare_reference():
    """A bare slug carries no verb, so POST stays the default."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        return httpx.Response(200, json={})

    make_client(handler).call_api("city-weather", {"city": "Tokyo"})

    assert captured["method"] == "POST"


def test_call_api_explicit_method_overrides_the_entry():
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        return httpx.Response(200, json={})

    entry = MarketplaceAPI.from_dict(
        {"resource_id": 91, "name": "X", "slug": "x", "method": "GET"}
    )
    make_client(handler).call_api(entry, {"a": 1}, method="post")

    assert captured["method"] == "POST"


def test_intent_types_cover_every_type_the_gateway_advertises():
    """The enum lagged the gateway by eight members before 0.4.0.

    An intent missing from the enum is a route a caller cannot name, so the
    full set is pinned here rather than trusted to stay in sync.
    """
    expected = {
        "audio_generation", "blockchain", "chat_completion", "code_execution",
        "code_generation", "data_analysis", "dns", "document_processing",
        "email", "general", "geo", "image_generation", "knowledge_search",
        "prompt_optimization", "storage", "text_to_speech", "translation",
        "utility", "video_generation", "web", "web_search",
    }
    assert {t.value for t in IntentType} == expected
    assert len(expected) == 21


@pytest.mark.asyncio
async def test_async_search_apis_matches_sync_behaviour():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "q=audio" in str(request.url)
        return httpx.Response(200, json=PAGE_BODY)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AsyncAIPClient(
            api_key="sk-test", http_client=http, endpoint="https://api.test"
        )
        page = await client.search_apis("audio")

    assert page.total == 2720
    assert page.items[0].slug == "audio-to-text"
