# reliability and request behavior

mercapy calls undocumented services owned by third parties. the client makes
failures explicit, but it cannot guarantee that those services remain available
or retain the same response shapes.

## timeouts

the default timeout is 10 seconds. pass a positive finite number to apply one
timeout value, or pass `httpx.Timeout` to configure connect, read, write, and pool
timeouts separately.

```python
import httpx

from mercapy import Mercadona

timeout = httpx.Timeout(connect=3.0, read=8.0, write=8.0, pool=3.0)
with Mercadona("mad3", timeout=timeout) as mercadona:
    categories = mercadona.get_categories()
```

connect failures and connect timeouts are eligible for retry. other request
errors, including read timeouts, raise `TransportError` after the first failure.

## rate limits and retries

the client does not delay normal requests by default. set `min_request_interval`
to place a minimum gap between request starts made by one client. the same limit
applies to retries.

```python
from mercapy import Mercadona

with Mercadona("mad3", min_request_interval=0.25) as mercadona:
    categories = mercadona.get_categories()
```

the interval limits start times, not concurrency or total request duration. a
value of 0.25 keeps successive request starts at least 0.25 seconds apart.

the default `RetryPolicy` allows three attempts. retries apply to:

- connection errors and connect timeouts
- http `429`
- http `500`, `502`, `503`, and `504`

ordinary `4xx` responses and other `5xx` responses are not retried.

without a `Retry-After` header, the base delay before retry number `n` is
`backoff_factor * 2 ** n`, starting with `n = 0`. `max_delay` caps every delay.
`jitter_ratio` adds a random value between zero and that fraction of the base
delay. the cap still applies. default retry delays are therefore 0.25 through
0.275 seconds and 0.5 through 0.55 seconds before the second and third attempts.

for http `429`, the client accepts `Retry-After` as seconds or an http date. the
same `max_delay` cap applies. an invalid header falls back to exponential backoff.
if the retry budget ends on a `429`, the client raises `RateLimitError`.

```python
from mercapy import Mercadona, RateLimitError, RetryPolicy

retry = RetryPolicy(
    max_attempts=2,
    backoff_factor=0.2,
    max_delay=2.0,
    jitter_ratio=0.1,
)

try:
    with Mercadona("mad3", timeout=5.0, retry_policy=retry) as mercadona:
        categories = mercadona.get_categories()
except RateLimitError as error:
    print("rate limit persisted", error.retry_after)
```

`retry_after` is the parsed and capped final header value, or `None` when the
server did not supply a usable value.

## error model

client-operation failures inherit from `MercapyError`.

| exception | meaning | useful attribute |
| --- | --- | --- |
| `ConfigurationError` | a client option, identifier, postcode, or method argument is invalid | none |
| `TransportError` | a request failed or returned an unhandled error status | `status_code` |
| `RateLimitError` | the retry budget ended on http `429` | `status_code`, `retry_after` |
| `NotFoundError` | the server returned http `404` | `status_code` |
| `InvalidResponseError` | json is invalid or the response lacks required structure | none |

`RateLimitError` and `NotFoundError` also inherit from `TransportError`. catch a
narrow exception first when different failures need different handling.

the pure `Photo` constructor and `Photo.url()` method raise `ValueError` for an
invalid filename, size, or fit value. they perform no network operation.

```python
from mercapy import (
    Mercadona,
    NotFoundError,
    RateLimitError,
    TransportError,
)

try:
    with Mercadona("mad3") as mercadona:
        product = mercadona.get_product("missing-id")
except NotFoundError:
    print("no such product")
except RateLimitError:
    print("request limit reached")
except TransportError as error:
    print("request failed", error.status_code)
```

## response parsing

parsers ignore unknown fields and accept absent optional fields. they raise
`InvalidResponseError` when the response is not a json object, a required
collection has the wrong type, or a record lacks a usable identity such as a
product id and name.

public models never retain the raw response dictionary. applications should not
depend on undocumented fields that mercapy does not expose.

## photo writes

`download_photo()` creates the destination directory when needed. it streams into
a temporary sibling file, closes the response, then replaces the destination.
failed status codes and interrupted streams remove the temporary file. an
existing destination remains intact unless the full download succeeds.

## request counts

| operation | requests before retries |
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
| `get_catalog()` | 1 category-tree request plus 1 request per direct child category |
| reading a returned model attribute | 0 |

retries increase these counts after eligible failures. avoid calling
`get_product()` for every catalog item unless complete product data is required.
`min_request_interval` changes timing but not request counts.

## verification

the offline test suite uses committed json fixtures and `httpx.MockTransport`.
it covers every public client operation, exact urls and parameters, immutable
models, parser edge cases, retries, rate limits, timeouts, and atomic photo
downloads. ci runs it on cpython 3.11 through 3.14 and enforces at least 90%
branch coverage.

a separate weekly and manually triggered smoke workflow checks four live calls:
postcode resolution, search, product detail, and categories. a passing run
confirms that those four response shapes matched the client during that run. it
does not guarantee future service availability.
