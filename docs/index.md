# mercapy documentation

mercapy provides synchronous, read-only access to product and storefront data
used by mercadona's online shop. the client does not manage carts, accounts,
orders, or payment data.

## documents

| document | purpose |
| --- | --- |
| [usage guide](usage.md) | installation patterns and complete examples |
| [api reference](api.md) | client signatures, return models, and public names |
| [generated api](reference.md) | signatures and docstrings read from the package |
| [reliability and request behavior](reliability.md) | timeouts, retries, rate limits, errors, and request counts |
| [v1 to v2 migration guide](https://github.com/jtayped/mercapy/blob/main/MIGRATION.md) | replacements for removed v1 behavior |
| [contribution guide](https://github.com/jtayped/mercapy/blob/main/CONTRIBUTING.md) | local setup, tests, style, and pull requests |
| [release process](https://github.com/jtayped/mercapy/blob/main/RELEASING.md) | versioning, verification, and trusted publishing |
| [changelog](https://github.com/jtayped/mercapy/blob/main/CHANGELOG.md) | released and pending user-visible changes |

## support policy

the current major version supports cpython 3.11 through 3.14. the public api is
the set of names exported by the top-level `mercapy` package. changes that remove
or rename those names require a new major version.

the client depends on undocumented upstream apis. a mercapy release records the
response shapes covered by its fixtures and live smoke test, not a promise that
the upstream service will remain unchanged.

## project status

the project is unofficial and has no affiliation with mercadona. report mercapy
defects through the [github issue tracker](https://github.com/jtayped/mercapy/issues).
do not send third-party service incidents or account questions to this project.
