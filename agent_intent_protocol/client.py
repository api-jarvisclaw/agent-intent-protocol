"""Agent Intent client with built-in x402 payment.

Declare an intent, discover a provider, and pay for the request on-chain
over the open `x402 <https://x402.org>`_ protocol. When the client is
given a :class:`~agent_intent_protocol.wallet.Wallet`, any HTTP 402 challenge
is answered automatically: the wallet signs the payment and the request
is retried with a ``PAYMENT-SIGNATURE`` header — no accounts, no API keys.

The client is vendor-neutral. ``endpoint`` defaults to a hosted gateway
for convenience but can point at any compliant x402 service.

Example::

    from agent_intent_protocol import AIPClient, IntentType, OptimizeFor, Wallet

    wallet = Wallet(private_key="0x...")
    client = AIPClient(wallet=wallet)
    result = client.resolve(
        IntentType.CHAT_COMPLETION,
        constraints={"max_price_usd": 0.01},
        preferences={"optimize_for": OptimizeFor.COST},
    )
    print(result.best_match.provider_id, result.best_match.model)
"""

from __future__ import annotations

import os
from typing import Any, Optional, Union

import httpx

from .errors import (
    AIPAPIError,
    AIPAuthError,
    AIPConnectionError,
    AIPPaymentRequiredError,
)
from .models import (
    Constraints,
    IntentType,
    MarketplaceAPI,
    MarketplacePage,
    Preferences,
    Provider,
    ResolveResult,
)
from .wallet import Wallet

DEFAULT_ENDPOINT = "https://api.jarvisclaw.ai"
__version__ = "0.4.0"

_ConstraintsArg = Union[Constraints, dict[str, Any], None]
_PreferencesArg = Union[Preferences, dict[str, Any], None]


def _coerce_constraints(value: _ConstraintsArg) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Constraints):
        return value.to_dict()
    return dict(value)


def _coerce_preferences(value: _PreferencesArg) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Preferences):
        return value.to_dict()
    out = dict(value)
    # normalize enum values so they serialize as plain strings
    if "optimize_for" in out and out["optimize_for"] is not None:
        out["optimize_for"] = str(out["optimize_for"])
    return out


class AIPClient:
    """Synchronous client with built-in x402 payment.

    Args:
        api_key: Optional bearer token for gateways that still use API-key
            auth. Falls back to the ``JARVISCLAW_API_KEY`` environment
            variable. Not required when paying with a wallet.
        wallet: A :class:`~agent_intent_protocol.wallet.Wallet`. When set, HTTP
            402 responses are answered automatically by signing the payment
            and retrying with a ``PAYMENT-SIGNATURE`` header.
        endpoint: Base URL of the gateway. Defaults to a hosted service;
            override to target any compliant x402 deployment.
        timeout: Request timeout in seconds.
        http_client: Optional preconfigured ``httpx.Client`` (for custom
            transports, proxies, or connection pooling).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        wallet: Optional[Wallet] = None,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = 30.0,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("JARVISCLAW_API_KEY")
        self.wallet = wallet
        self.endpoint = endpoint.rstrip("/")
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)

    # ── context manager ────────────────────────────────────────────────
    def __enter__(self) -> "AIPClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client (only if this client owns it)."""
        if self._owns_client:
            self._http.close()

    # ── internal request helper ────────────────────────────────────────
    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"agent-intent-protocol/{__version__}",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.endpoint}{path}"
        try:
            resp = self._http.request(
                method, url, json=json, params=params, headers=self._headers()
            )
        except httpx.RequestError as exc:
            raise AIPConnectionError(f"request to {url} failed: {exc}") from exc

        # x402: answer a payment challenge by signing it and retrying once.
        if resp.status_code == 402 and self.wallet is not None:
            resp = self._pay_and_retry(
                resp, method, url, json=json, params=params
            )

        if resp.status_code >= 400:
            self._raise_for_status(resp)

        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError as exc:
            raise AIPAPIError(
                f"invalid JSON in response from {url}",
                status_code=resp.status_code,
                body=resp.text,
            ) from exc

    def _pay_and_retry(
        self,
        resp: httpx.Response,
        method: str,
        url: str,
        *,
        json: Optional[dict[str, Any]],
        params: Optional[dict[str, Any]],
    ) -> httpx.Response:
        """Sign the 402 challenge and retry the request once.

        Returns the retried response, or the original 402 response if the
        challenge body could not be parsed (so normal error handling runs).
        """
        try:
            challenge = resp.json()
        except ValueError:
            return resp

        signature = self.wallet.sign_challenge(challenge)
        headers = self._headers()
        headers["PAYMENT-SIGNATURE"] = signature
        try:
            return self._http.request(
                method, url, json=json, params=params, headers=headers
            )
        except httpx.RequestError as exc:
            raise AIPConnectionError(f"request to {url} failed: {exc}") from exc

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        detail: Optional[str] = None
        body: Any = None
        try:
            body = resp.json()
            if isinstance(body, dict):
                detail = body.get("detail") or body.get("error") or body.get("message")
        except ValueError:
            body = resp.text
            detail = resp.text or None

        message = f"AIP server returned {resp.status_code}"
        if detail:
            message = f"{message}: {detail}"

        code = resp.status_code
        if code in (401, 403):
            raise AIPAuthError(message, status_code=code, detail=detail, body=body)
        if code == 402:
            raise AIPPaymentRequiredError(
                message, status_code=code, detail=detail, body=body
            )
        raise AIPAPIError(message, status_code=code, detail=detail, body=body)

    # ── protocol methods ───────────────────────────────────────────────
    def resolve(
        self,
        intent: Union[IntentType, str],
        *,
        constraints: _ConstraintsArg = None,
        preferences: _PreferencesArg = None,
    ) -> ResolveResult:
        """Resolve an intent to ranked provider matches.

        Args:
            intent: The intent type, e.g. ``IntentType.CHAT_COMPLETION``.
            constraints: Hard requirements a provider must satisfy. Accepts a
                :class:`Constraints` instance or a plain dict, e.g.
                ``{"max_price_usd": 0.01, "features": ["function_calling"]}``.
            preferences: Soft ranking directives. Accepts a
                :class:`Preferences` instance or a plain dict, e.g.
                ``{"optimize_for": "cost", "limit": 5}``.

        Returns:
            A :class:`ResolveResult`. Use ``.best_match`` for the top provider
            or ``.matches`` for the full ranked list.

        Endpoint: ``POST /v1/intent/resolve`` (requires authentication).
        """
        body: dict[str, Any] = {"intent": str(intent)}
        c = _coerce_constraints(constraints)
        if c:
            body["constraints"] = c
        p = _coerce_preferences(preferences)
        if p:
            body["preferences"] = p
        data = self._request("POST", "/v1/intent/resolve", json=body)
        return ResolveResult.from_dict(data or {})

    def resolve_natural(
        self,
        query: str,
        *,
        session_id: Optional[str] = None,
        constraints: _ConstraintsArg = None,
    ) -> dict[str, Any]:
        """Resolve a natural-language query to providers or a clarification.

        Unlike :meth:`resolve`, the gateway may respond with a follow-up
        question instead of matches, so the raw response dict is returned.

        Endpoint: ``POST /v1/intent/resolve/natural`` (requires authentication).
        """
        body: dict[str, Any] = {"query": query}
        if session_id is not None:
            body["session_id"] = session_id
        c = _coerce_constraints(constraints)
        if c:
            body["constraints"] = c
        return self._request("POST", "/v1/intent/resolve/natural", json=body) or {}

    def discover(
        self,
        *,
        intent_type: Union[IntentType, str, None] = None,
    ) -> list[Provider]:
        """Discover providers, optionally filtered by intent type.

        Endpoint: ``GET /v1/intent/discover`` (no authentication required).
        """
        params: dict[str, Any] = {}
        if intent_type is not None:
            params["intent_type"] = str(intent_type)
        data = self._request("GET", "/v1/intent/discover", params=params or None)
        return _extract_providers(data)

    def execute(
        self,
        intent: Union[IntentType, str],
        payload: dict[str, Any],
        *,
        constraints: _ConstraintsArg = None,
        preferences: _PreferencesArg = None,
    ) -> Any:
        """Resolve an intent and execute it against the selected provider.

        Args:
            intent: The intent type to execute.
            payload: The provider-facing request body (e.g. chat messages).
            constraints: Hard requirements for provider selection.
            preferences: Soft ranking directives for provider selection.

        Returns:
            The raw provider response, proxied through the gateway.

        Endpoint: ``POST /v1/intent/execute`` (requires authentication).
        """
        body: dict[str, Any] = {"intent": str(intent), "payload": payload}
        c = _coerce_constraints(constraints)
        if c:
            body["constraints"] = c
        p = _coerce_preferences(preferences)
        if p:
            body["preferences"] = p
        return self._request("POST", "/v1/intent/execute", json=body)

    def list_intent_types(self) -> list[str]:
        """List the intent types the gateway supports.

        Endpoint: ``GET /v1/intent/types`` (no authentication required).
        """
        data = self._request("GET", "/v1/intent/types")
        if isinstance(data, dict):
            return data.get("intent_types", [])
        return data or []

    def list_providers(self) -> list[Provider]:
        """List all registered providers.

        Endpoint: ``GET /v1/providers`` (no authentication required).
        """
        data = self._request("GET", "/v1/providers")
        return _extract_providers(data)

    # ── API marketplace ────────────────────────────────────────────────
    #
    # The intent methods above route a task to whichever provider ranks best.
    # These three address the same catalogue from the other end: search it,
    # read one entry's price, call that exact endpoint. Before 0.4.0 the client
    # had no way to reach it, so 2,720 priced endpoints were invisible to
    # callers who only had this SDK.

    def search_apis(
        self,
        query: Optional[str] = None,
        *,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> MarketplacePage:
        """Search the API marketplace.

        Args:
            query: Free-text match over name, description and tags. Omit to
                page through the whole catalogue.
            category: Restrict to one category (``search``, ``blockchain``,
                ``code``, ``image``, ``dns``, ``document``, ``email``, ``geo``,
                ``ocr``, ``audio``, ``tts``, ``video``, ``storage``,
                ``utility``, ``qr``, ``web``, ``llm``, ``general``). The
                returned page carries the live category counts.
            page: 1-indexed page number.
            page_size: Results per page.

        Returns:
            A :class:`MarketplacePage`; iterate it for the entries, read
            ``.total`` for the size of the filtered catalogue.

        Endpoint: ``GET /api/marketplace/apis`` (free, no authentication).
        """
        # The gateway's free-text parameter is `q`; `search` is accepted but
        # ignored, which silently returns the unfiltered catalogue.
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        data = self._request("GET", "/api/marketplace/apis", params=params)
        return MarketplacePage.from_dict(_unwrap(data))

    def get_api(self, ref: Union[str, int]) -> MarketplaceAPI:
        """Fetch one marketplace entry by slug or numeric resource id.

        Args:
            ref: The ``slug`` (preferred — it survives an upstream rename) or
                the ``resource_id``.

        Endpoint: ``GET /api/marketplace/apis/{ref}`` (free, no authentication).
        """
        data = self._request("GET", f"/api/marketplace/apis/{ref}")
        return MarketplaceAPI.from_dict(_unwrap(data))

    def call_api(
        self,
        ref: Union[str, int],
        payload: Optional[dict[str, Any]] = None,
        *,
        method: Optional[str] = None,
    ) -> Any:
        """Call one marketplace endpoint directly and return its response.

        This is a paid call. With a wallet configured, the ``402`` challenge is
        signed and the request retried transparently, exactly as for
        :meth:`execute`. Without one, an :class:`AIPPaymentRequiredError`
        carries the quote so a caller can decide and retry.

        Args:
            ref: The entry's ``slug`` or ``resource_id``. Passing the
                :class:`MarketplaceAPI` itself is also accepted, and is the
                only form that gets the verb right without a lookup.
            payload: Parameters forwarded verbatim upstream. Accepted fields
                differ per endpoint — read them from :meth:`get_api`. Sending
                nothing returns a quote rather than a result.
            method: Override the HTTP verb. Rarely needed: passing a
                ``MarketplaceAPI`` uses the verb the catalogue publishes for it.

        Endpoint: ``{method} /v1/marketplace/api/{ref}``.

        Roughly 45% of the catalogue is ``GET``, so the verb cannot be assumed.
        On a ``GET`` the payload is sent as the query string, because a GET body
        is not something every upstream reads.
        """
        verb, target = _resolve_call_target(ref, method)
        path = f"/v1/marketplace/api/{target}"
        if verb == "GET":
            return self._request("GET", path, params=payload or None)
        return self._request(verb, path, json=payload or {})


def _resolve_call_target(
    ref: Any, method: Optional[str]
) -> tuple[str, Union[str, int]]:
    """Work out the verb and path segment for a marketplace call.

    A bare slug or id carries no verb, so it defaults to POST; a
    ``MarketplaceAPI`` carries the one the catalogue published. An explicit
    ``method`` wins over both.
    """
    target: Union[str, int]
    verb = "POST"
    if isinstance(ref, MarketplaceAPI):
        target = ref.slug or ref.resource_id
        if ref.method:
            verb = ref.method.upper()
    else:
        target = ref
    if method:
        verb = method.upper()
    return verb, target


def _unwrap(data: Any) -> dict[str, Any]:
    """Return the payload of a ``{"success": true, "data": {...}}`` envelope.

    The marketplace routes wrap their payload; the intent routes do not. Rather
    than assume either, unwrap only when the envelope is actually present, so a
    gateway that drops it later keeps working.
    """
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, dict) and "success" in data:
            return inner
        return data
    return {}


def _extract_providers(data: Any) -> list[Provider]:
    """Normalize the various provider list shapes into ``list[Provider]``."""
    if data is None:
        return []
    if isinstance(data, dict):
        items = data.get("providers", data.get("matches", []))
    else:
        items = data
    return [Provider.from_dict(item) for item in items if isinstance(item, dict)]
