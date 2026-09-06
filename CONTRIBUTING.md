# Contributing

Mercapy talks to an undocumented third-party service. Keep normal tests offline
and use committed fixtures for every upstream response shape.

## Development setup

Use any supported CPython version from 3.11 through 3.14:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Run the same checks as CI:

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest
.venv/bin/python -m build
.venv/bin/twine check dist/*
```

Ruff can apply formatting with `.venv/bin/ruff format .`.

## Tests

Tests use `httpx.MockTransport`. Do not add routine tests that contact Mercadona
or Algolia. Add small, scrubbed JSON files under `tests/fixtures` for new response
shapes. Test exact request paths, query parameters, and call counts when changing
client behavior.

The suite requires at least 90% branch coverage. It must also prove that model
attribute access causes no I/O and that optional or unknown fields do not break
otherwise usable responses.

## Supported Python policy

Mercapy supports CPython 3.11, 3.12, 3.13, and 3.14. CI runs tests on all four.
A release may drop a Python version only in a new major Mercapy release. Support
for a new stable CPython version can be added in a minor release after CI and the
built-wheel import check pass on that version.

## Pull requests

Keep changes focused. Update the README and migration guide when public behavior
changes, add a changelog entry, and include tests. The live smoke workflow is for
small manual or weekly checks, not feature development.
