# Migrating from Mercapy V1 to V2

Version 2 is a clean break. It has no compatibility aliases, and V1 code should
be updated before changing the dependency constraint.

## API changes

| V1 | V2 |
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

## Explicit requests

V1 models fetched missing data when properties were read. V2 model attributes
never perform I/O. Listing methods return `ProductSummary`; use `get_product()`
for complete product data.

```python
from mercapy import Mercadona

with Mercadona.from_postal_code("28001") as mercadona:
    search = mercadona.search_products("arroz", page=0, page_size=20)
    summary = search.products[0]
    product = mercadona.get_product(summary.id)
```

This change also removes the hidden N+1 request pattern from normal attribute
access. Calls that intentionally aggregate data, chiefly `get_catalog()`, state
their request behavior in the README.

## Values and errors

- Lists returned by V1 are tuples in V2.
- Prices and numeric quantities are `Decimal`, not `float`.
- IDs are strings even when the API sends a number.
- Models are frozen and have no writable `__dict__`.
- Request failures raise a `MercapyError` subclass. No method prints an error or
  returns a fabricated error dictionary.
- `search_products()` returns `SearchResult`, including page metadata.
- Home sections remain ordered records. Sections with matching layouts are not
  merged.

## Client lifetime

V2 keeps an HTTP connection pool. Close clients explicitly or use a context
manager:

```python
from mercapy import Mercadona

with Mercadona("mad3") as mercadona:
    product = mercadona.get_product("5044")
```
