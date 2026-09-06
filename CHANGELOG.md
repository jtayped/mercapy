# changelog

this project follows [semantic versioning](https://semver.org/).

## [unreleased]

### added

- a documentation index and separate usage, api, and reliability references,
  with checks for lowercase prose, local links, and python snippet syntax.
- ci coverage for the minimum supported python and httpx versions.
- a clean-wheel request test and dependency consistency check.
- security linting for library and maintenance code.
- opt-in per-client request pacing and jittered retry delays.
- a generated api reference and a github pages documentation workflow.

### changed

- rewrote project documentation in lowercase, direct prose.
- made the wheel import check compare package metadata instead of a hard-coded
  version.
- configured dependabot to preserve compatible runtime dependency ranges.
- added lowercase package metadata and documentation links.

## [2.0.0] - 2026-09-06

### changed

- replaced network-backed model properties with explicit synchronous client
  methods.
- replaced mutable response wrappers with frozen, slotted dataclasses and typed
  price, availability, category, detail, nutrition, home, and season data.
- changed prices and numeric quantities to `Decimal`, collections to tuples, and
  ids to strings.
- moved packaging to `pyproject.toml`, hatchling, and a `src` layout.
- set cpython 3.11 as the minimum version and added support through cpython 3.14.
- replaced `requests` with a reusable `httpx.Client` and explicit timeouts.

### added

- search pagination metadata.
- explicit product, category, season, and streamed photo methods.
- bounded retries for connection failures, rate limits, and selected server
  errors.
- typed exceptions and the `py.typed` marker.
- fixture-based tests, strict linting and typing, branch coverage, ci, a live
  smoke workflow, and trusted publishing.
- a guarded, concurrent warehouse-discovery maintenance script.

### removed

- the runtime warehouse constant, lazy i/o, wildcard exports, and `setup.py`.
- model `__dict__()` methods and printed error handling.
- all v1 aliases. see [the migration guide](MIGRATION.md) for replacements.

## [1.0.3] - 2024-01-05

- last v1 release before the api redesign.
