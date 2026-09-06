# Changelog

This project follows [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-09-06

### Changed

- Replaced network-backed model properties with explicit synchronous client
  methods.
- Replaced mutable response wrappers with frozen, slotted dataclasses and typed
  nested price, availability, category, detail, nutrition, home, and season data.
- Changed prices and numeric quantities to `Decimal`, collections to tuples, and
  IDs to strings.
- Moved packaging to `pyproject.toml`, Hatchling, and a `src` layout. Python 3.11
  through 3.14 are supported.
- Replaced `requests` with a reusable `httpx.Client` and explicit timeouts.

### Added

- Pagination metadata for search results.
- Product, category, season, and atomic streamed photo client methods.
- Bounded retries for connection failures, rate limits, and transient server
  errors.
- Typed exceptions, `py.typed`, fixture-based tests, strict linting and typing,
  branch coverage, CI, a live smoke workflow, and trusted publishing.
- A guarded concurrent warehouse-discovery maintenance CLI.

### Removed

- The runtime warehouse constant, lazy I/O, wildcard exports, `setup.py`, model
  `__dict__()` methods, and printed error handling.
- All V1 aliases. See `MIGRATION.md` for replacements.

## [1.0.3] - 2024-01-05

- Last V1 release before the API redesign.
