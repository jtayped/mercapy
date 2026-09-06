# migrating from mercapy v1 to v2

version 2 is a clean break. it has no compatibility aliases. update application
code before changing the dependency constraint.

## api replacements

| v1 | v2 |
| --- | --- |
| `Mercadona(postcode)` | `Mercadona.from_postal_code(postcode)` |
| `Mercadona(warehouse_or_postcode)` | `Mercadona(warehouse)` for a known warehouse |
| `mercadona.search(query)` | `mercadona.search_products(query).products` |
| `mercadona.get_home_recommendations()` | `mercadona.get_home()` |
| `Product(product_id)` | `mercadona.get_product(product_id)` |
| `Category(category_id, ...)` | `mercadona.get_category(category_id)` |
| `Season(season_id, ...)` | `mercadona.get_season(season_id)` |
| `product.unit_price` | `product.price.unit` |
| `product.bulk_price` | `product.price.bulk` |
| `product.previos_price` or `product.previous_price` | `product.price.previous` |
| `product.age_check` | `product.requires_age_check` |
| `product.alcohol_by_volume` | `product.details.alcohol_by_volume` |
| `product.description` | `product.details.description` |
| `product.images` | `product.photos` |
| `photo.get_size(w, h)` | `photo.url(width=w, height=h)` |
| `photo.save(path, ...)` | `mercadona.download_photo(photo, path, ...)` |
| `product.__dict__()` | `dataclasses.asdict(product)` when a dictionary is required |

## explicit requests

v1 models could fetch data when an attribute was read. v2 model attributes never
perform i/o. listing methods return `ProductSummary`; call `get_product()` when
complete product data is required.

```python
from mercapy import Mercadona

with Mercadona.from_postal_code("28001") as mercadona:
    search = mercadona.search_products("arroz", page=0, page_size=20)
    summary = search.products[0]
    product = mercadona.get_product(summary.id)
```

the example performs three requests: postcode resolution, search, and product
detail. v2 no longer hides the last request behind attribute access. see the
[request table](docs/reliability.md#request-counts) before processing a full
catalog.

## value changes

- v1 lists are tuples in v2.
- prices and numeric quantities use `Decimal`, not `float`.
- ids are strings even when the upstream api sends a number.
- models are frozen and do not have a writable `__dict__`.
- `search_products()` returns `SearchResult` with pagination metadata.
- home sections preserve their source order. sections with the same layout stay
  separate.

## error changes

request failures raise a `MercapyError` subclass. methods no longer print errors
or return fabricated error dictionaries. catch the narrowest exception that an
application can handle. the [reliability guide](docs/reliability.md#error-model)
defines the exception hierarchy.

## client lifetime

v2 keeps an http connection pool. use a context manager or call `close()` when
the client is no longer needed.

```python
from mercapy import Mercadona

with Mercadona("mad3") as mercadona:
    product = mercadona.get_product("5044")
```
