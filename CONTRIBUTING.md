# contributing

mercapy uses undocumented third-party services. normal tests must stay offline,
and every supported response shape needs a committed fixture.

## development setup

use cpython 3.11 through 3.14:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

run the same checks as ci:

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest
.venv/bin/python -m build
.venv/bin/twine check dist/*
```

run `.venv/bin/ruff format .` to apply python formatting.

## tests

tests use `httpx.MockTransport`. do not add routine tests that contact mercadona
or algolia. add small, scrubbed json files under `tests/fixtures` for new response
shapes. changes to client behavior should test exact request paths, parameters,
and request counts.

the suite requires at least 90% branch coverage. tests must also confirm that
model access performs no i/o and that absent optional fields or unknown fields do
not break an otherwise usable response.

the live smoke workflow is the only routine upstream check. it makes four calls
once a week or when started manually.

## documentation

write headings and prose in lowercase. preserve the exact spelling of code,
identifiers, commands, paths, urls, and quoted output. use short examples that
can run as written. state request counts for examples that make more than one
request.

update the api reference and migration guide when public behavior changes. add a
changelog entry for every user-visible change.

## supported python policy

mercapy supports cpython 3.11, 3.12, 3.13, and 3.14. ci runs the test suite on all
four versions. removing a supported version requires a new major mercapy release.
a minor release may add a stable cpython version after its tests and clean-wheel
import check pass.

## pull requests

keep each pull request focused. include tests for behavior changes and do not
commit build output, virtual environments, credentials, or live api responses
that contain unnecessary data.
