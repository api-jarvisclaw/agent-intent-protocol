# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-08-19

### Added
- **API marketplace access**: `search_apis`, `get_api`, and `call_api` (sync and
  async), plus the `MarketplaceAPI` and `MarketplacePage` models. The gateway
  serves 2,720 individually priced endpoints at
  `GET /api/marketplace/apis` and `POST /v1/marketplace/api/{ref}`; until now the
  client had no way to reach any of them, so callers holding only this SDK saw
  the 21 intent types and nothing else. Searching and reading prices are free;
  only invocation is billed.
- `MarketplaceAPI.path` derives the invocation path from the slug, which
  outlives an upstream renaming its resource, rather than the numeric id.
- `call_api` accepts a `MarketplaceAPI` and then uses the HTTP verb the
  catalogue published for that entry. About 45% of the catalogue is `GET`, and
  the gateway tolerates `POST` on those routes, so a hardcoded `POST` fails
  quietly rather than loudly. On a `GET` the payload is sent as the query
  string. `method=` overrides.

### Fixed
- **`IntentType` was missing eight members** the gateway advertises:
  `audio_generation`, `blockchain`, `dns`, `email`, `general`, `geo`, `storage`,
  and `web`. An absent member is a route callers cannot name, so the enum is now
  pinned to `GET /v1/intent/types` by a test rather than extended by hand.

### Changed
- Pinned `ruff<0.13` in the dev extra. It was unbounded, so newly added
  modernization rules (`UP045`, `UP037`) began failing CI on pre-existing style
  across the package — unrelated to any change under review.

## [0.3.0] - 2026-07-16

### Changed
- **Renamed the distribution to `agent-intent-protocol`** (import module
  `agent_intent_protocol`). The protocol name reflects the full scope: x402 is
  the payment rail it rides, not the whole protocol. The former
  `agent-intent-x402` name is retired; a redirect release points existing users
  here.

### Added
- AIR/1 offline-verifiable settlement receipts: `build_receipt`,
  `sign_receipt`, `verify_receipt`, plus `canonicalize` and `hash_object`.
- Dual signature suites: `EvmSigner` (`secp256k1`/EIP-191) for Base and other
  EVM chains, and `SolanaSigner` (`ed25519`) for Solana.
- `AsyncAIPClient` for async workflows.
- Runnable `examples/` covering discovery, resolve, wallet-paid execution, and
  offline receipt verification.
- Project scaffolding: `CONTRIBUTING.md`, `SECURITY.md`, this changelog, and
  GitHub issue/PR templates.
- README badges, a feature overview, and an offline-verifiable receipts section.

## [0.2.0]

### Added
- Wallet-based x402 payments: the client answers `402` challenges by signing an
  EIP-3009 authorization and retrying transparently.
- Intent resolution and execution over the Agent Intent Protocol:
  `resolve`, `resolve_natural`, `execute`, `discover`, `list_intent_types`,
  and `list_providers`.

## [0.1.0]

### Added
- Initial release of the `agent-intent-protocol` client.

[Unreleased]: https://github.com/api-jarvisclaw/agent-intent-protocol/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/api-jarvisclaw/agent-intent-protocol/releases/tag/v0.4.0
[0.3.0]: https://github.com/api-jarvisclaw/agent-intent-protocol/releases/tag/v0.3.0
[0.2.0]: https://github.com/api-jarvisclaw/agent-intent-protocol/releases/tag/v0.2.0
[0.1.0]: https://github.com/api-jarvisclaw/agent-intent-protocol/releases/tag/v0.1.0
