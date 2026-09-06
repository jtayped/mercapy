# usage guide

this guide covers the normal client workflow. every example uses a context
manager so the underlying http connection pool closes at the end of the block.

## choose a warehouse

most applications should resolve a five-digit spanish postcode. the lookup costs
one request and uses the warehouse assigned by mercadona at that moment.

```python
from mercapy import Mercadona

with Mercadona.from_postal_code("28001") as mercadona:
    print(mercadona.warehouse)
```

applications that already have a warehouse code can avoid that lookup.
construction itself performs no i/o.

```python
from mercapy import Mercadona

with Mercadona(
    "mad3",
    language="es",
    timeout=8.0,
    min_request_interval=0.25,
) as mercadona:
    print(mercadona.language)
```

supported language values are `"es"` and `"en"`. this example also keeps at
least 0.25 seconds between request starts made by the client.

## search products

search pages start at zero. `page_size` accepts values from 1 through 1000.

```python
from mercapy import Mercadona

with Mercadona.from_postal_code("28001") as mercadona:
    result = mercadona.search_products("café", page=0, page_size=20)

    print(result.page, result.total_pages, result.total_hits)
    for product in result.products:
        print(product.id, product.name, product.price.unit)
```

the call returns `SearchResult`. its `products` tuple contains `ProductSummary`
records. pagination metadata comes from the search service.

## fetch product details

summaries contain listing data. request a complete `Product` when ingredients,
allergens, photos, supplier data, or the full product details are needed.

```python
from mercapy import Mercadona

with Mercadona("mad3") as mercadona:
    search = mercadona.search_products("arroz", page_size=1)
    if search.products:
        product = mercadona.get_product(search.products[0].id)
        print(product.name)
        print(product.price.unit)
        print(product.details.legal_name)
        print(product.nutrition.ingredients)
```

this example makes two requests. accessing `product.price` or another model
attribute does not make another request.

## browse categories and the catalog

`get_categories()` returns the category tree from one request.
`get_category()` requests one category by id.

```python
from mercapy import Mercadona

with Mercadona("mad3") as mercadona:
    categories = mercadona.get_categories()
    for category in categories:
        print(category.id, category.name)

    category = mercadona.get_category("72")
    for product in category.products:
        print(product.name)
```

`get_catalog()` combines the category tree and each listed category group. it
deduplicates products by id and returns `ProductSummary` records. it does not call
the product-detail endpoint, but it can still make many category requests.

```python
from mercapy import Mercadona

with Mercadona("mad3") as mercadona:
    catalog = mercadona.get_catalog()
```

## read home sections and seasons

home sections keep their upstream order. sections with the same layout remain
separate.

```python
from mercapy import Mercadona, SeasonSummary

with Mercadona("mad3") as mercadona:
    for section in mercadona.get_home():
        print(section.layout, section.title)
        for item in section.items:
            if isinstance(item, SeasonSummary):
                season = mercadona.get_season(item.id)
                print(season.title, len(season.products))
```

`get_new_arrivals()` returns a tuple of `ProductSummary`. `get_season()` returns a
`Season`, whose `products` field also contains summaries.

## download a photo

`Photo.url()` creates an image url without network access. width and height are
optional positive integers. `fit` accepts `"crop"` or `"fit"`.

```python
from mercapy import Mercadona

with Mercadona("mad3") as mercadona:
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

the download streams into a temporary file beside the destination. after a
successful transfer, mercapy replaces the destination atomically. a failed or
interrupted transfer leaves an existing destination unchanged.

## work with model values

prices and numeric quantities use `Decimal`, which retains decimal precision.
models are frozen and cannot be changed in place. use `dataclasses.asdict()` when
a mutable dictionary is required for serialization.

```python
from dataclasses import asdict
from decimal import Decimal

from mercapy import Price

price = Price(unit=Decimal("1.15"))
assert price.unit == Decimal("1.15")
payload = asdict(price)
```

model fields reflect what the upstream service supplied. optional fields may be
`None`, and optional collections may be empty.
