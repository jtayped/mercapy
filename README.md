<h1 align="center">
  <img src="https://github.com/jtayped/mercapy/blob/main/images/logo.png?raw=true" alt="Mercapy" width="180">
  <br>
  Mercapy
</h1>

Mercapy is a synchronous, typed Python client for the public storefront APIs used
by Mercadona's online shop. Version 2 returns immutable data and performs network
requests only when you call a client method.

Mercapy is an unofficial project. It is not affiliated with, endorsed by, or
maintained by Mercadona. The upstream APIs are undocumented and may change.

## Install

Mercapy 2 supports CPython 3.11 through 3.14.

```bash
python -m pip install mercapy
```

## Start with a postcode

`from_postal_code()` validates the postcode, resolves its current warehouse, and
returns a configured client. The lookup is explicit and costs one HTTP request.

```python
from mercapy import Mercadona

with Mercadona.from_postal_code("28001") as mercadona:
    result = mercadona.search_products("leche sin lactosa", page=0, page_size=10)

    for product in result.products:
        print(product.name, product.price.unit)

    if result.products:
        full_product = mercadona.get_product(result.products[0].id)
        print(full_product.ean)
        print(full_product.nutrition.ingredients)
```

Madrid postcode `28001` currently resolves to `mad3`. Warehouse assignments can
change, so applications based on a user's location should resolve the postcode
instead of storing the result forever.

If you already know the warehouse, construction performs no I/O:

```python
from mercapy import Mercadona

with Mercadona("mad3", language="es", timeout=8.0) as mercadona:
    categories = mercadona.get_categories()
```

The supported languages are `"es"` and `"en"`.

## Products and prices

Search, catalog, home, season, and new-arrival methods return `ProductSummary`
objects. A summary contains the fields available in the corresponding listing.
Fetch complete details when you need them:

```python
summary = mercadona.search_products("arroz", page_size=1).products[0]
product = mercadona.get_product(summary.id)

print(product.name)
print(product.price.unit)  # Decimal, for example Decimal("1.15")
print(product.price.previous)  # Decimal or None
print(product.details.legal_name)
print(product.photos)
```

All public result models are frozen, slotted dataclasses. Their collections are
tuples, prices and quantities use `Decimal`, and reading an attribute never makes
a request. Mercapy ignores unknown upstream fields and leaves absent optional
fields as `None` or an empty tuple.

## Home, seasons, and catalog

```python
from mercapy import SeasonSummary

sections = mercadona.get_home()
for section in sections:
    print(section.layout, section.title)
    for item in section.items:
        if isinstance(item, SeasonSummary):
            season = mercadona.get_season(item.id)
            print(season.title, len(season.products))

new_products = mercadona.get_new_arrivals()
catalog = mercadona.get_catalog()
```

`get_home()` preserves upstream order. Two carousel sections stay separate even
when they have the same layout.

`get_catalog()` first gets the category tree, then fetches each listed category
group. It can make many requests. It still returns summaries and never fetches
each product's detail endpoint.

## Download a photo

`Photo.url()` only builds a URL. `download_photo()` streams the response to a
temporary sibling and replaces the destination after the transfer succeeds.
An existing file is left untouched after a failed or interrupted download.

```python
product = mercadona.get_product("5044")
photo = product.photos[0]

print(photo.url(width=800, height=800, fit="crop"))
path = mercadona.download_photo(
    photo,
    "images/arroz.jpg",
    width=800,
    height=800,
    fit="crop",
)
```

The resize fit is either `"crop"` or `"fit"`. Width and height are optional and
must be positive when supplied.

## Errors and retries

All library errors inherit from `MercapyError`:

```python
from mercapy import Mercadona, NotFoundError, RateLimitError, TransportError

try:
    with Mercadona("mad3") as mercadona:
        product = mercadona.get_product("missing-id")
except NotFoundError:
    print("No such product")
except RateLimitError as error:
    print("Rate limit persisted", error.retry_after)
except TransportError as error:
    print("Request failed", error.status_code)
```

Mercapy retries connection failures, HTTP 429, and transient server errors with
bounded exponential backoff. It honors `Retry-After` when present. Ordinary 4xx
responses are not retried. Configure the bounds with `RetryPolicy`:

```python
from mercapy import Mercadona, RetryPolicy

retry = RetryPolicy(max_attempts=2, backoff_factor=0.2, max_delay=2.0)
with Mercadona("mad3", timeout=5.0, retry_policy=retry) as mercadona:
    categories = mercadona.get_categories()
```

`ConfigurationError`, `NotFoundError`, `RateLimitError`, `TransportError`, and
`InvalidResponseError` let callers handle each failure without parsing printed
messages. Mercapy never prints from library code.

## HTTP request counts

| Operation | Requests |
| --- | ---: |
| `Mercadona(...)` | 0 |
| `Mercadona.from_postal_code(...)` | 1 |
| `search_products(...)` | 1 |
| `get_product(...)` | 1 |
| `get_categories()` | 1 |
| `get_category(...)` | 1 |
| `get_new_arrivals()` | 1 |
| `get_home()` | 1 |
| `get_season(...)` | 1 |
| `download_photo(...)` | 1 |
| `get_catalog()` | 1 category-tree request plus one request per category group |
| Reading any returned model attribute | 0 |

Retries can increase these counts after eligible failures. Avoid calling
`get_product()` for every catalog item unless the detail data is necessary.

## Project documents

- [V1 to V2 migration guide](MIGRATION.md)
- [Changelog](CHANGELOG.md)
- [Contribution guide](CONTRIBUTING.md)
- [Release checklist](RELEASING.md)

Mercapy is distributed under the [MIT license](LICENSE).
