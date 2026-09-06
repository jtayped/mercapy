<h1 align="center">
  <img src="https://github.com/jtayped/mercapy/blob/main/images/logo.png?raw=true" alt="mercapy" width="180">
  <br>
  mercapy
</h1>

mercapy is a synchronous, typed python client for the public storefront apis used
by mercadona's online shop. it returns immutable data and makes network requests
only through explicit client methods.

this is an unofficial project. it is not affiliated with, endorsed by, or
maintained by mercadona. the upstream apis are undocumented and may change
without notice.

## installation

mercapy supports cpython 3.11 through 3.14.

```bash
python -m pip install mercapy
```

## quick start

resolve a warehouse from a spanish postcode, search for a product, then request
the complete product record:

```python
from mercapy import Mercadona

with Mercadona.from_postal_code("28001") as mercadona:
    result = mercadona.search_products("leche sin lactosa", page_size=10)

    for summary in result.products:
        print(summary.name, summary.price.unit)

    if result.products:
        product = mercadona.get_product(result.products[0].id)
        print(product.ean)
        print(product.nutrition.ingredients)
```

`from_postal_code()` performs one request before it returns the client. if the
warehouse code is already known, construct the client without network access:

```python
from mercapy import Mercadona

with Mercadona("mad3", language="es", timeout=8.0) as mercadona:
    categories = mercadona.get_categories()
```

the client reuses its connections. use a `with` block to close it after use.

## behavior

- client methods make the requests. reading a returned model never performs i/o.
- listing calls return `ProductSummary`; `get_product()` returns a complete
  `Product`.
- public models are frozen, slotted dataclasses. collections are tuples, ids are
  strings, and numeric prices and quantities use `Decimal`.
- unknown response fields are ignored. missing optional values become `None` or
  an empty tuple.
- request failures raise a `MercapyError` subclass. library code does not print.
- connection failures, http `429`, and selected `5xx` responses use a bounded
  retry policy.
- optional request pacing limits how quickly one client starts requests.

## documentation

- [documentation index](docs/index.md)
- [usage guide](docs/usage.md)
- [api reference](docs/api.md)
- [generated api reference](docs/reference.md)
- [reliability and request behavior](docs/reliability.md)
- [v1 to v2 migration guide](MIGRATION.md)
- [contribution guide](CONTRIBUTING.md)
- [release process](RELEASING.md)
- [changelog](CHANGELOG.md)

mercapy is distributed under the [mit license](LICENSE).
