"""synchronous mercadona client."""

from __future__ import annotations

import os
import re
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from math import isfinite
from pathlib import Path
from random import SystemRandom
from threading import Lock
from types import TracebackType
from typing import Any, Self
from urllib.parse import quote, urlencode

import httpx

from ._constants import ALGOLIA_API_KEY, ALGOLIA_APP_ID, ALGOLIA_URL, API_URL
from ._version import __version__
from .exceptions import (
    ConfigurationError,
    InvalidResponseError,
    NotFoundError,
    RateLimitError,
    TransportError,
)
from .models import (
    CatalogResult,
    Category,
    HomeSection,
    JsonObject,
    Language,
    Photo,
    PhotoFit,
    Product,
    ProductSummary,
    SearchResult,
    Season,
    parse_category,
    parse_home_section,
    parse_product,
    parse_product_summary,
    parse_search_result,
    parse_season,
)

_WAREHOUSE_PATTERN = re.compile(r"^[a-z0-9]{2,16}$")
_POSTAL_CODE_PATTERN = re.compile(r"^(?:0[1-9]|[1-4][0-9]|5[0-2])\d{3}$")
_RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})
# the search service answers at most this many hits for one query, which is
# why the catalog is partitioned at all.
_INDEX_RESULT_CAP = 1000
# score partitions: the upper bound starts here and grows by this factor
# until a probe above it finds nothing; ranges stop halving at this width.
_SCORE_UPPER_START = 1024.0
_SCORE_GROWTH = 4
_SCORE_BOUND_PROBES = 16
_SCORE_RESOLUTION = 1e-6
_JITTER = SystemRandom()


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """bounded retry settings for connection and transient http failures."""

    max_attempts: int = 3
    backoff_factor: float = 0.25
    max_delay: float = 5.0
    jitter_ratio: float = 0.1

    def __post_init__(self) -> None:
        if isinstance(self.max_attempts, bool) or not isinstance(
            self.max_attempts, int
        ):
            raise ConfigurationError("max_attempts must be an integer")
        if self.max_attempts < 1:
            raise ConfigurationError("max_attempts must be at least one")
        if (
            isinstance(self.backoff_factor, bool)
            or not isinstance(self.backoff_factor, (int, float))
            or not isfinite(self.backoff_factor)
            or self.backoff_factor < 0
        ):
            raise ConfigurationError(
                "backoff_factor must be a finite non-negative number"
            )
        if (
            isinstance(self.max_delay, bool)
            or not isinstance(self.max_delay, (int, float))
            or not isfinite(self.max_delay)
            or self.max_delay < 0
        ):
            raise ConfigurationError("max_delay must be a finite non-negative number")
        if (
            isinstance(self.jitter_ratio, bool)
            or not isinstance(self.jitter_ratio, (int, float))
            or not isfinite(self.jitter_ratio)
            or not 0 <= self.jitter_ratio <= 1
        ):
            raise ConfigurationError("jitter_ratio must be between zero and one")


def validate_postal_code(postal_code: str) -> str:
    """validate and return a five-digit spanish postal code."""

    if not isinstance(postal_code, str) or not _POSTAL_CODE_PATTERN.fullmatch(
        postal_code
    ):
        raise ConfigurationError(
            "postal_code must contain five digits with a province prefix from 01 to 52"
        )
    return postal_code


def _validate_warehouse(warehouse: str) -> str:
    if not isinstance(warehouse, str):
        raise ConfigurationError("warehouse must be a string")
    normalized = warehouse.strip().lower()
    if not _WAREHOUSE_PATTERN.fullmatch(normalized):
        raise ConfigurationError(
            "warehouse must contain 2 to 16 lowercase letters or digits"
        )
    return normalized


def _validate_identifier(value: str | int, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ConfigurationError(f"{label} must be a non-empty string or integer")
    result = str(value).strip()
    if not result:
        raise ConfigurationError(f"{label} must be a non-empty string or integer")
    return result


def _category_filter(category_ids: tuple[str, ...]) -> str:
    return " OR ".join(f"categories.id:{category_id}" for category_id in category_ids)


def _pack_categories(counts: dict[str, object], cap: int) -> list[tuple[str, ...]]:
    """first-fit decreasing over the facet counts: the fewest groups whose
    summed counts stay within the cap. a product in two categories counts in
    both, so a group's real hit count is at most its sum. a count that is not
    a usable integer gets a group of its own."""

    sizes = {
        str(category_id): (
            count
            if isinstance(count, int) and not isinstance(count, bool) and count >= 0
            else cap
        )
        for category_id, count in counts.items()
    }
    groups: list[list[str]] = []
    totals: list[int] = []
    for category_id in sorted(sizes, key=lambda key: (-sizes[key], key)):
        size = sizes[category_id]
        for index, total in enumerate(totals):
            if total + size <= cap:
                groups[index].append(category_id)
                totals[index] += size
                break
        else:
            groups.append([category_id])
            totals.append(size)
    return [tuple(sorted(group)) for group in groups]


def _validate_timeout(timeout: float | httpx.Timeout) -> float | httpx.Timeout:
    if isinstance(timeout, httpx.Timeout):
        values = (timeout.connect, timeout.read, timeout.write, timeout.pool)
        if any(
            value is not None and (not isfinite(value) or value <= 0)
            for value in values
        ):
            raise ConfigurationError(
                "timeout values must be finite and greater than zero"
            )
        return timeout
    if isinstance(timeout, bool):
        raise ConfigurationError("timeout must be a finite number greater than zero")
    try:
        value = float(timeout)
    except (TypeError, ValueError) as error:
        raise ConfigurationError("timeout must be a valid httpx timeout") from error
    if not isfinite(value) or value <= 0:
        raise ConfigurationError("timeout must be a finite number greater than zero")
    return value


def _validate_request_interval(value: float) -> float:
    if isinstance(value, bool):
        raise ConfigurationError(
            "min_request_interval must be a finite non-negative number"
        )
    try:
        interval = float(value)
    except (TypeError, ValueError) as error:
        raise ConfigurationError(
            "min_request_interval must be a finite non-negative number"
        ) from error
    if not isfinite(interval) or interval < 0:
        raise ConfigurationError(
            "min_request_interval must be a finite non-negative number"
        )
    return interval


class Mercadona:
    """a reusable synchronous client scoped to one mercadona warehouse."""

    def __init__(
        self,
        warehouse: str,
        *,
        language: Language | str = Language.SPANISH,
        timeout: float | httpx.Timeout = 10.0,
        retry_policy: RetryPolicy | None = None,
        min_request_interval: float = 0.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._warehouse = _validate_warehouse(warehouse)
        try:
            self._language = Language(language)
        except ValueError as error:
            raise ConfigurationError("language must be 'es', 'en', or 'ca'") from error
        self._retry_policy = retry_policy or RetryPolicy()
        self._min_request_interval = _validate_request_interval(min_request_interval)
        self._request_lock = Lock()
        self._last_request_started_at: float | None = None
        timeout_config = _validate_timeout(timeout)
        try:
            self._client = httpx.Client(
                timeout=timeout_config,
                transport=transport,
                headers={
                    "Accept": "application/json",
                    "Accept-Language": self._language.value,
                    "User-Agent": f"mercapy/{__version__}",
                },
                follow_redirects=False,
            )
        except (TypeError, ValueError) as error:
            raise ConfigurationError("timeout must be a valid httpx timeout") from error
        self._closed = False

    @classmethod
    def from_postal_code(
        cls,
        postal_code: str,
        *,
        language: Language | str = Language.SPANISH,
        timeout: float | httpx.Timeout = 10.0,
        retry_policy: RetryPolicy | None = None,
        min_request_interval: float = 0.0,
        transport: httpx.BaseTransport | None = None,
    ) -> Self:
        """resolve a postal code with one request and return a scoped client."""

        postal_code = validate_postal_code(postal_code)
        client = cls(
            "lookup",
            language=language,
            timeout=timeout,
            retry_policy=retry_policy,
            min_request_interval=min_request_interval,
            transport=transport,
        )
        try:
            response = client._request(
                "PUT",
                f"{API_URL}/api/postal-codes/actions/change-pc/",
                json={"new_postal_code": postal_code},
            )
            warehouse = response.headers.get("X-Customer-Wh")
            if warehouse is None:
                raise InvalidResponseError(
                    "postal-code response has no X-Customer-Wh header"
                )
            client._warehouse = _validate_warehouse(warehouse)
            return client
        except BaseException:
            client.close()
            raise

    @property
    def warehouse(self) -> str:
        """return the normalized warehouse code."""

        return self._warehouse

    @property
    def language(self) -> Language:
        """return the selected storefront language."""

        return self._language

    @property
    def is_closed(self) -> bool:
        """return whether the client has been closed."""

        return self._closed

    @property
    def min_request_interval(self) -> float:
        """return the minimum time between request starts in seconds."""

        return self._min_request_interval

    def close(self) -> None:
        """close the http connection pool."""

        if not self._closed:
            self._client.close()
            self._closed = True

    def __enter__(self) -> Self:
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def search_products(
        self,
        query: str,
        *,
        page: int = 0,
        page_size: int = 20,
        top_level_category_id: str | int | None = None,
    ) -> SearchResult:
        """search one zero-based page of product summaries."""

        if not isinstance(query, str):
            raise ConfigurationError("query must be a string")
        if isinstance(page, bool) or not isinstance(page, int) or page < 0:
            raise ConfigurationError("page must be a non-negative integer")
        if (
            isinstance(page_size, bool)
            or not isinstance(page_size, int)
            or not 1 <= page_size <= 1000
        ):
            raise ConfigurationError("page_size must be between 1 and 1000")

        category_id = (
            _validate_identifier(top_level_category_id, "top_level_category_id")
            if top_level_category_id is not None
            else None
        )
        data = self._search_data(
            query=query,
            page=page,
            page_size=page_size,
            filters=_category_filter((category_id,)) if category_id else None,
        )
        return parse_search_result(
            data, query=query, requested_page=page, requested_page_size=page_size
        )

    def get_indexed_catalog(self) -> CatalogResult:
        """collect the complete Algolia index through top-category partitions.

        top-level categories are packed into as few groups as the result cap
        allows, using the overview's facet counts, and each group is one query.
        a group that still reports more hits than the cap is halved.

        an index that exposes no category facets is partitioned by score
        ranges instead: numeric filters work on every index, and a range that
        reports more hits than the result cap is halved until it fits. records
        without a score, or more tied scores than the cap, leave the result
        unreconciled rather than silently short.
        """

        overview = self._search_data(
            query="",
            page=0,
            page_size=1,
            facets="categories.id",
            max_values_per_facet=1000,
        )
        reported_total_hits = overview.get("nbHits")
        if (
            isinstance(reported_total_hits, bool)
            or not isinstance(reported_total_hits, int)
            or reported_total_hits < 0
        ):
            raise InvalidResponseError("catalog index response has no usable hit count")
        facets = overview.get("facets")
        if not isinstance(facets, dict):
            raise InvalidResponseError("catalog index response has no facets object")
        category_counts = facets.get("categories.id")

        products: dict[str, ProductSummary] = {}
        score_ranges: tuple[tuple[float, float], ...] = ()
        groups: tuple[tuple[str, ...], ...] = ()
        if isinstance(category_counts, dict) and category_counts:
            category_ids = tuple(sorted(str(value) for value in category_counts))
            for group in _pack_categories(category_counts, _INDEX_RESULT_CAP):
                groups += self._collect_category_group(products, group)
        else:
            category_ids = ()
            score_ranges = self._collect_score_partitions(products)

        return CatalogResult(
            products=tuple(products.values()),
            reported_total_hits=reported_total_hits,
            queried_category_ids=category_ids,
            queried_score_ranges=score_ranges,
            queried_category_groups=groups,
            reconciled=len(products) == reported_total_hits,
        )

    def _collect_category_group(
        self, products: dict[str, ProductSummary], group: tuple[str, ...]
    ) -> tuple[tuple[str, ...], ...]:
        """query a group of categories at once and return the groups that were
        actually queried: facet counts can move between the overview and the
        query, so a group over the cap is split in two and each half retried."""

        if len(group) == 1:
            self._collect_category_partition(products, group[0])
            return (group,)
        data = self._search_data(
            query="",
            page=0,
            page_size=_INDEX_RESULT_CAP,
            filters=_category_filter(group),
        )
        result = parse_search_result(
            data, query="", requested_page=0, requested_page_size=_INDEX_RESULT_CAP
        )
        if result.total_hits > _INDEX_RESULT_CAP:
            middle = len(group) // 2
            return self._collect_category_group(
                products, group[:middle]
            ) + self._collect_category_group(products, group[middle:])
        for product in result.products:
            products.setdefault(product.id, product)
        return (group,)

    def _collect_category_partition(
        self, products: dict[str, ProductSummary], category_id: str
    ) -> None:
        page = 0
        while True:
            data = self._search_data(
                query="",
                page=page,
                page_size=_INDEX_RESULT_CAP,
                filters=_category_filter((category_id,)),
            )
            result = parse_search_result(
                data,
                query="",
                requested_page=page,
                requested_page_size=_INDEX_RESULT_CAP,
            )
            for product in result.products:
                products.setdefault(product.id, product)
            page += 1
            if page >= result.total_pages:
                break

    def _score_partition(
        self, lower: float, upper: float | None, *, page_size: int
    ) -> SearchResult:
        numeric_filters = f"score>={lower:.6f}"
        if upper is not None:
            numeric_filters += f",score<{upper:.6f}"
        data = self._search_data(
            query="", page=0, page_size=page_size, numeric_filters=numeric_filters
        )
        return parse_search_result(
            data, query="", requested_page=0, requested_page_size=page_size
        )

    def _collect_score_partitions(
        self, products: dict[str, ProductSummary]
    ) -> tuple[tuple[float, float], ...]:
        upper = _SCORE_UPPER_START
        for _ in range(_SCORE_BOUND_PROBES):
            if self._score_partition(upper, None, page_size=0).total_hits == 0:
                break
            upper *= _SCORE_GROWTH

        ranges: list[tuple[float, float]] = []
        pending: list[tuple[float, float]] = [(0.0, upper)]
        while pending:
            lower, upper = pending.pop()
            result = self._score_partition(lower, upper, page_size=_INDEX_RESULT_CAP)
            if result.total_hits == 0:
                continue
            if (
                result.total_hits > _INDEX_RESULT_CAP
                and upper - lower > _SCORE_RESOLUTION
            ):
                middle = (lower + upper) / 2
                pending.append((middle, upper))
                pending.append((lower, middle))
                continue
            ranges.append((lower, upper))
            for product in result.products:
                products.setdefault(product.id, product)
        return tuple(ranges)

    def get_product(self, product_id: str | int) -> Product:
        """return a complete product record by id."""

        product_id = _validate_identifier(product_id, "product_id")
        data = self._get_api_json(f"/api/products/{quote(product_id, safe='')}/")
        return parse_product(data)

    def get_categories(self) -> tuple[Category, ...]:
        """return the storefront category tree."""

        data = self._get_api_json("/api/categories/")
        results = data.get("results")
        if not isinstance(results, list):
            raise InvalidResponseError("categories response has no results array")
        return tuple(parse_category(item) for item in results)

    def get_category(self, category_id: str | int) -> Category:
        """return one category by id."""

        category_id = _validate_identifier(category_id, "category_id")
        data = self._get_api_json(f"/api/categories/{quote(category_id, safe='')}/")
        return parse_category(data)

    def get_catalog(self) -> tuple[ProductSummary, ...]:
        """collect deduplicated summaries from all listed category groups."""

        products: list[ProductSummary] = []
        seen: set[str] = set()

        def add_from(category: Category) -> None:
            for product in category.products:
                if product.id not in seen:
                    seen.add(product.id)
                    products.append(product)
            for child in category.children:
                add_from(child)

        for category in self.get_categories():
            add_from(category)
            for child in category.children:
                add_from(self.get_category(child.id))
        return tuple(products)

    def get_new_arrivals(self) -> tuple[ProductSummary, ...]:
        """return the current new-arrival product summaries."""

        data = self._get_api_json("/api/home/new-arrivals/")
        items = data.get("items")
        if not isinstance(items, list):
            raise InvalidResponseError("new-arrivals response has no items array")
        return tuple(parse_product_summary(item) for item in items)

    def get_home(self) -> tuple[HomeSection, ...]:
        """return ordered storefront home sections."""

        data = self._get_api_json("/api/home/")
        sections = data.get("sections")
        if not isinstance(sections, list):
            raise InvalidResponseError("home response has no sections array")
        return tuple(parse_home_section(section) for section in sections)

    def get_season(self, season_id: str) -> Season:
        """return one seasonal product collection by id."""

        season_id = _validate_identifier(season_id, "season_id")
        data = self._get_api_json(f"/api/home/sections/{quote(season_id, safe='')}/")
        return parse_season(data, season_id)

    def download_photo(
        self,
        photo: Photo,
        destination: str | os.PathLike[str],
        *,
        width: int | None = None,
        height: int | None = None,
        fit: PhotoFit | str = PhotoFit.CROP,
    ) -> Path:
        """download a photo through an atomic destination replacement."""

        if not isinstance(photo, Photo):
            raise ConfigurationError("photo must be a Photo instance")
        url = photo.url(width=width, height=height, fit=fit)
        destination_path = Path(destination)
        if destination_path.exists() and destination_path.is_dir():
            raise ConfigurationError("destination must be a file path")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination_path.parent,
            prefix=f".{destination_path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with (
                os.fdopen(descriptor, "wb") as output,
                self._stream("GET", url) as response,
            ):
                try:
                    for chunk in response.iter_bytes():
                        output.write(chunk)
                except httpx.RequestError as error:
                    raise TransportError(f"photo download failed: {error}") from error
            os.replace(temporary_path, destination_path)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
        return destination_path

    def _get_api_json(self, path: str) -> JsonObject:
        return self._request_json(
            "GET",
            f"{API_URL}{path}",
            params={"lang": self._language.value, "wh": self._warehouse},
        )

    def _search_data(
        self,
        *,
        query: str,
        page: int,
        page_size: int,
        filters: str | None = None,
        facets: str | None = None,
        max_values_per_facet: int | None = None,
        numeric_filters: str | None = None,
    ) -> JsonObject:
        index = f"products_prod_{self._warehouse}_{self._language.value}"
        url = f"{ALGOLIA_URL}/1/indexes/{quote(index, safe='')}/query"
        parameters: list[tuple[str, str | int]] = [
            ("query", query),
            ("page", page),
            ("hitsPerPage", page_size),
        ]
        if filters is not None:
            parameters.append(("filters", filters))
        if facets is not None:
            parameters.append(("facets", facets))
        if max_values_per_facet is not None:
            parameters.append(("maxValuesPerFacet", max_values_per_facet))
        if numeric_filters is not None:
            parameters.append(("numericFilters", numeric_filters))
        return self._request_json(
            "POST",
            url,
            headers={
                "x-algolia-application-id": ALGOLIA_APP_ID,
                "x-algolia-api-key": ALGOLIA_API_KEY,
            },
            json={"params": urlencode(parameters)},
        )

    def _request_json(self, method: str, url: str, **kwargs: Any) -> JsonObject:
        response = self._request(method, url, **kwargs)
        try:
            data = response.json()
        except ValueError as error:
            raise InvalidResponseError(
                f"{method} {url} returned invalid JSON"
            ) from error
        if not isinstance(data, dict):
            raise InvalidResponseError(
                f"{method} {url} returned a non-object JSON value"
            )
        return data

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return self._send_with_retries(
            lambda: self._client.request(method, url, **kwargs),
            method=method,
            url=url,
        )

    @contextmanager
    def _stream(self, method: str, url: str, **kwargs: Any) -> Iterator[httpx.Response]:
        response = self._send_with_retries(
            lambda: self._client.send(
                self._client.build_request(method, url, **kwargs), stream=True
            ),
            method=method,
            url=url,
        )

        try:
            yield response
        finally:
            response.close()

    def _send_with_retries(
        self,
        send: Callable[[], httpx.Response],
        *,
        method: str,
        url: str,
    ) -> httpx.Response:
        self._ensure_open()
        for attempt in range(self._retry_policy.max_attempts):
            self._wait_for_request_slot()
            try:
                response = send()
            except (httpx.ConnectError, httpx.ConnectTimeout) as error:
                if attempt + 1 == self._retry_policy.max_attempts:
                    raise TransportError(
                        f"{method} {url} failed after "
                        f"{self._retry_policy.max_attempts} connection attempts: "
                        f"{error}"
                    ) from error
                time.sleep(self._backoff(attempt))
                continue
            except httpx.RequestError as error:
                raise TransportError(f"{method} {url} failed: {error}") from error

            if response.status_code == 429:
                retry_after = self._retry_after(response)
                if attempt + 1 == self._retry_policy.max_attempts:
                    response.close()
                    raise RateLimitError(
                        f"{method} {url} was rate limited after "
                        f"{self._retry_policy.max_attempts} attempts",
                        retry_after=retry_after,
                    )
                response.close()
                delay = (
                    retry_after if retry_after is not None else self._backoff(attempt)
                )
                time.sleep(delay)
                continue

            if (
                response.status_code in _RETRYABLE_STATUS_CODES
                and attempt + 1 < self._retry_policy.max_attempts
            ):
                response.close()
                time.sleep(self._backoff(attempt))
                continue
            self._raise_for_status(response, method=method, url=url)
            return response

        raise RuntimeError("retry loop ended without a response")  # pragma: no cover

    def _raise_for_status(
        self, response: httpx.Response, *, method: str, url: str
    ) -> None:
        if response.status_code < 400:
            return
        status_code = response.status_code
        response.close()
        if status_code == 404:
            raise NotFoundError(f"{method} {url} returned HTTP 404")
        raise TransportError(
            f"{method} {url} returned HTTP {status_code}", status_code=status_code
        )

    def _backoff(self, attempt: int) -> float:
        delay = self._retry_policy.backoff_factor * (2.0**attempt)
        delay = min(delay, self._retry_policy.max_delay)
        if delay == 0 or self._retry_policy.jitter_ratio == 0:
            return delay
        jitter = _JITTER.uniform(0, delay * self._retry_policy.jitter_ratio)
        return min(delay + jitter, self._retry_policy.max_delay)

    def _wait_for_request_slot(self) -> None:
        if self._min_request_interval == 0:
            return
        with self._request_lock:
            started_at = time.monotonic()
            if self._last_request_started_at is not None:
                elapsed = started_at - self._last_request_started_at
                delay = self._min_request_interval - elapsed
                if delay > 0:
                    time.sleep(delay)
                    started_at = time.monotonic()
            self._last_request_started_at = started_at

    def _retry_after(self, response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if value is None:
            return None
        try:
            delay = float(value)
        except ValueError:
            try:
                retry_date = parsedate_to_datetime(value)
                if retry_date.tzinfo is None:
                    retry_date = retry_date.replace(tzinfo=UTC)
                delay = (retry_date - datetime.now(UTC)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                return None
        return min(max(delay, 0.0), self._retry_policy.max_delay)

    def _ensure_open(self) -> None:
        if self._closed:
            raise ConfigurationError("Mercadona client is closed")
