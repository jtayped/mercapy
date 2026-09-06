# api reference

mercapy exposes its supported public names from the top-level `mercapy` package.
the package also ships `py.typed` for type checkers.

## client

### `Mercadona`

```text
Mercadona(
    warehouse,
    *,
    language="es",
    timeout=10.0,
    retry_policy=None,
    min_request_interval=0.0,
    transport=None,
)
```

creates a synchronous client scoped to one warehouse. warehouse codes contain 2
to 16 letters or digits and are normalized to lowercase. construction performs
no request.

`language` accepts `Language.SPANISH`, `Language.ENGLISH`, `"es"`, or `"en"`.
`timeout` accepts a positive finite number or `httpx.Timeout`. `transport` accepts
an `httpx.BaseTransport` and is mainly useful for tests. a positive
`min_request_interval` sets the minimum time between request starts for that
client.

the client supports `with`, `close()`, and these read-only properties:

| property | type | meaning |
| --- | --- | --- |
| `warehouse` | `str` | normalized warehouse code |
| `language` | `Language` | selected response language |
| `min_request_interval` | `float` | minimum seconds between request starts |
| `is_closed` | `bool` | whether `close()` has run |

### `Mercadona.from_postal_code()`

```text
Mercadona.from_postal_code(
    postal_code,
    *,
    language="es",
    timeout=10.0,
    retry_policy=None,
    min_request_interval=0.0,
    transport=None,
)
```

validates a five-digit spanish postcode, resolves its current warehouse with one
request, and returns a configured `Mercadona` client.

### product methods

| method | return type | requests |
| --- | --- | ---: |
| `search_products(query, *, page=0, page_size=20)` | `SearchResult` | 1 |
| `get_product(product_id)` | `Product` | 1 |
| `get_new_arrivals()` | `tuple[ProductSummary, ...]` | 1 |

search pages start at zero. `page_size` must be between 1 and 1000. product ids
may be strings or integers and become strings in returned models.

### category methods

| method | return type | requests |
| --- | --- | ---: |
| `get_categories()` | `tuple[Category, ...]` | 1 |
| `get_category(category_id)` | `Category` | 1 |
| `get_catalog()` | `tuple[ProductSummary, ...]` | variable |

`get_catalog()` makes one category-tree request and one request for each direct
child in the returned top-level category tree. it deduplicates products by id.

### home methods

| method | return type | requests |
| --- | --- | ---: |
| `get_home()` | `tuple[HomeSection, ...]` | 1 |
| `get_season(season_id)` | `Season` | 1 |

### photo method

```text
download_photo(
    photo,
    destination,
    *,
    width=None,
    height=None,
    fit="crop",
) -> Path
```

downloads one `Photo` to a local file. `destination` accepts a string or
`os.PathLike[str]`. `fit` accepts `PhotoFit.CROP`, `PhotoFit.FIT`, `"crop"`, or
`"fit"`.

## retry policy

```python
RetryPolicy(
    max_attempts=3,
    backoff_factor=0.25,
    max_delay=5.0,
    jitter_ratio=0.1,
)
```

`max_attempts` includes the first request and must be at least 1. delay values
must be non-negative. `jitter_ratio` must be between 0 and 1. see [reliability
and request behavior](reliability.md) for the retry rules.

## result models

all result models are frozen, slotted dataclasses. every collection field is a
tuple. ids use `str`, and numeric prices and quantities use `Decimal`.

### products

| model | fields |
| --- | --- |
| `ProductSummary` | `id`, `name`, `slug`, `brand`, `packaging`, `main_feature`, `share_url`, `thumbnail`, `price`, `availability`, `categories`, `requires_age_check`, `is_water`, `is_new_arrival` |
| `Product` | `id`, `name`, `ean`, `slug`, `brand`, `packaging`, `main_feature`, `share_url`, `photos`, `price`, `availability`, `categories`, `details`, `nutrition`, `requires_age_check`, `is_water`, `is_bulk`, `is_variable_weight`, `is_new_arrival` |
| `ProductDetails` | `legal_name`, `description`, `origin`, `suppliers`, `counter_info`, `danger_mentions`, `mandatory_mentions`, `production_variant`, `usage_instructions`, `storage_instructions`, `alcohol_by_volume`, `prepared_by_mercadona` |
| `Nutrition` | `allergens`, `ingredients` |

### price and availability

| model | fields |
| --- | --- |
| `Price` | `unit`, `bulk`, `previous`, `reference`, `tax_percentage`, `unit_size`, `pack_size`, `total_units`, `drained_weight`, `minimum_amount`, `increment_amount`, `unit_name`, `size_format`, `reference_format`, `is_discounted`, `is_new`, `is_pack`, `approximate_size` |
| `Availability` | `published`, `status`, `limit`, `unavailable_from`, `unavailable_weekdays` |

### categories, home, and search

| model | fields |
| --- | --- |
| `Category` | `id`, `name`, `order`, `level`, `layout`, `published`, `is_extended`, `image_url`, `subtitle`, `children`, `products` |
| `HomeSection` | `layout`, `title`, `subtitle`, `id`, `source`, `source_code`, `show_more`, `items` |
| `HomeNotification` | `title`, `kind`, `action`, `event_key` |
| `SeasonSummary` | `id`, `title`, `banner_id`, `campaign_id`, `image_url`, `text_color`, `background_colors`, `button_color` |
| `Season` | `id`, `title`, `layout`, `source`, `source_code`, `products` |
| `SearchResult` | `query`, `page`, `page_size`, `total_hits`, `total_pages`, `processing_time_ms`, `products` |

`HomeSection.items` may contain `ProductSummary`, `SeasonSummary`, or
`HomeNotification` values.

### photos and enums

`Photo` contains `file_name` and optional `perspective` fields. its
`url(*, width=None, height=None, fit="crop")` method returns a string and performs
no i/o. invalid dimensions, fit values, and filenames raise `ValueError`.

`Language` is a string enum with `SPANISH = "es"` and `ENGLISH = "en"`.
`PhotoFit` is a string enum with `CROP = "crop"` and `FIT = "fit"`.

## exceptions

the top-level package exports `MercapyError`, `ConfigurationError`,
`TransportError`, `RateLimitError`, `NotFoundError`, and
`InvalidResponseError`. see the [error model](reliability.md#error-model) for
their meanings and attributes.

## version

`mercapy.__version__` contains the installed package version.
