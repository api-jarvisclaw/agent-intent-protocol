# AIP Error Codes Reference

All error responses follow the envelope:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

## Authentication & Authorization

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_MISSING` | 401 | No `Authorization` header provided |
| `AUTH_INVALID` | 401 | Token is malformed or expired |
| `AUTH_REVOKED` | 401 | Token has been explicitly revoked |
| `QUOTA_EXCEEDED` | 429 | Account has exhausted its balance or free tier |
| `RATE_LIMITED` | 429 | Too many requests; respect `Retry-After` header |
| `PERMISSION_DENIED` | 403 | Token lacks permission for the requested intent |

## Resolution Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NO_PROVIDER_MATCH` | 422 | No provider satisfies all constraints |
| `INTENT_NOT_FOUND` | 404 | The requested intent does not exist in the catalog |
| `INTENT_DISABLED` | 503 | Intent exists but is temporarily disabled |
| `CONSTRAINT_CONFLICT` | 422 | Constraints are mutually exclusive (e.g., cheapest + highest quality) |
| `CONTEXT_INVALID` | 400 | Context hints contain invalid or unrecognized fields |

## Execution Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PROVIDER_ERROR` | 502 | Upstream provider returned an error |
| `PROVIDER_TIMEOUT` | 504 | Upstream provider did not respond within deadline |
| `PROVIDER_OVERLOADED` | 503 | All eligible providers are at capacity |
| `PAYLOAD_INVALID` | 400 | Payload does not match the intent's schema |
| `PAYLOAD_TOO_LARGE` | 413 | Payload exceeds maximum allowed size |
| `EXECUTION_CANCELLED` | 499 | Client disconnected before execution completed |
| `CONTENT_FILTERED` | 451 | Request or response was blocked by content moderation |

## Streaming Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `STREAM_INTERRUPTED` | 502 | SSE stream was interrupted by provider |
| `STREAM_TIMEOUT` | 504 | No data received within stream keepalive window |
| `STREAM_NOT_SUPPORTED` | 422 | The resolved provider/intent does not support streaming |

## Billing Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BALANCE_INSUFFICIENT` | 402 | Account balance cannot cover estimated cost |
| `BILLING_FAILED` | 500 | Internal billing system error; request was NOT charged |
| `PRICE_CHANGED` | 409 | Provider price changed between resolve and execute |

## Platform Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unrecoverable platform error |
| `MAINTENANCE` | 503 | Platform is undergoing scheduled maintenance |
| `VERSION_UNSUPPORTED` | 410 | Requested API version is no longer supported |

## Retry Guidance

| HTTP Status | Retryable? | Strategy |
|-------------|-----------|----------|
| 429 | Yes | Exponential backoff; respect `Retry-After` |
| 500 | Maybe | Retry once after 1s; if persistent, stop |
| 502 | Yes | Retry with backoff (provider may recover) |
| 503 | Yes | Retry after `Retry-After` or 5s default |
| 504 | Yes | Retry with increased timeout or different optimization strategy |
| 4xx (other) | No | Fix the request |

## Error Response Headers

| Header | Description |
|--------|-------------|
| `Retry-After` | Seconds to wait before retrying (on 429/503) |
| `X-Request-Id` | Unique request ID for support debugging |
| `X-AIP-Provider` | Which provider failed (on 502/504) |
| `X-AIP-Resolve-Ms` | Time spent in resolution phase |
