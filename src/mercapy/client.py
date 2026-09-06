"""Synchronous Mercadona client."""

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


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Bounded retry settings for connection and transient HTTP failures."""

    max_attempts: int = 3
    backoff_factor: float = 0.25
    max_delay: float = 5.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ConfigurationError("max_attempts must be at least one")
        if self.backoff_factor < 0:
            raise ConfigurationError("backoff_factor cannot be negative")
        if self.max_delay < 0:
            raise ConfigurationError("max_delay cannot be negative")


def validate_postal_code(postal_code: str) -> str:
    """Validate and return a five-digit Spanish postal code."""

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


class Mercadona:
    """A reusable synchronous client scoped to one Mercadona warehouse."""

    def __init__(
        self,
        warehouse: str,
        *,
        language: Language | str = Language.SPANISH,
        timeout: float | httpx.Timeout = 10.0,
        retry_policy: RetryPolicy | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._warehouse = _validate_warehouse(warehouse)
        try:
            self._language = Language(language)
        except ValueError as error:
            raise ConfigurationError("language must be 'es' or 'en'") from error
        self._retry_policy = retry_policy or RetryPolicy()
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
        transport: httpx.BaseTransport | None = None,
    ) -> Self:
        """Resolve a postal code with one request and return a scoped client."""

        postal_code = validate_postal_code(postal_code)
        client = cls(
            "lookup",
            language=language,
            timeout=timeout,
            retry_policy=retry_policy,
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
        return self._warehouse

    @property
    def language(self) -> Language:
        return self._language

    @property
    def is_closed(self) -> bool:
        return self._closed

    def close(self) -> None:
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
        self, query: str, *, page: int = 0, page_size: int = 20
    ) -> SearchResult:
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

        index = f"products_prod_{self._warehouse}_{self._language.value}"
        url = f"{ALGOLIA_URL}/1/indexes/{quote(index, safe='')}/query"
        parameters = urlencode(
            (("query", query), ("page", page), ("hitsPerPage", page_size))
        )
        data = self._request_json(
            "POST",
            url,
            headers={
                "x-algolia-application-id": ALGOLIA_APP_ID,
                "x-algolia-api-key": ALGOLIA_API_KEY,
            },
            json={"params": parameters},
        )
        return parse_search_result(
            data, query=query, requested_page=page, requested_page_size=page_size
        )

    def get_product(self, product_id: str | int) -> Product:
        product_id = _validate_identifier(product_id, "product_id")
        data = self._get_api_json(f"/api/products/{quote(product_id, safe='')}/")
        return parse_product(data)

    def get_categories(self) -> tuple[Category, ...]:
        data = self._get_api_json("/api/categories/")
        results = data.get("results")
        if not isinstance(results, list):
            raise InvalidResponseError("categories response has no results array")
        return tuple(parse_category(item) for item in results)

    def get_category(self, category_id: str | int) -> Category:
        category_id = _validate_identifier(category_id, "category_id")
        data = self._get_api_json(f"/api/categories/{quote(category_id, safe='')}/")
        return parse_category(data)

    def get_catalog(self) -> tuple[ProductSummary, ...]:
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
        data = self._get_api_json("/api/home/new-arrivals/")
        items = data.get("items")
        if not isinstance(items, list):
            raise InvalidResponseError("new-arrivals response has no items array")
        return tuple(parse_product_summary(item) for item in items)

    def get_home(self) -> tuple[HomeSection, ...]:
        data = self._get_api_json("/api/home/")
        sections = data.get("sections")
        if not isinstance(sections, list):
            raise InvalidResponseError("home response has no sections array")
        return tuple(parse_home_section(section) for section in sections)

    def get_season(self, season_id: str) -> Season:
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
        last_connection_error: httpx.RequestError | None = None
        for attempt in range(self._retry_policy.max_attempts):
            try:
                response = send()
            except (httpx.ConnectError, httpx.ConnectTimeout) as error:
                last_connection_error = error
                if attempt + 1 == self._retry_policy.max_attempts:
                    break
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

        assert last_connection_error is not None
        raise TransportError(
            f"{method} {url} failed after {self._retry_policy.max_attempts} "
            f"connection attempts: {last_connection_error}"
        ) from last_connection_error

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
        return min(delay, self._retry_policy.max_delay)

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
