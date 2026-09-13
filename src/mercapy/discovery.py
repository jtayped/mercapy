"""postal-code based Mercadona warehouse discovery."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from ._constants import API_URL
from .client import validate_postal_code
from .exceptions import InvalidResponseError, TransportError


def resolve_warehouse(postal_code: str, *, timeout: float = 5.0) -> str:
    """resolve one Spanish postal code to its current warehouse code."""

    postal_code = validate_postal_code(postal_code)
    try:
        response = httpx.put(
            f"{API_URL}/api/postal-codes/actions/change-pc/",
            json={"new_postal_code": postal_code},
            timeout=timeout,
            follow_redirects=False,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise TransportError(
            f"could not resolve postal code {postal_code}: {error}"
        ) from error
    warehouse = response.headers.get("X-Customer-Wh")
    if not warehouse:
        raise InvalidResponseError(
            f"postal code {postal_code} returned no X-Customer-Wh header"
        )
    return str(warehouse).strip().lower()


def discover_warehouses(
    postal_codes: Iterable[str],
    *,
    max_workers: int = 5,
    lookup: Callable[[str], str] = resolve_warehouse,
) -> dict[str, str]:
    """resolve unique postal codes concurrently while retaining input mapping."""

    if not 1 <= max_workers <= 32:
        raise ValueError("max_workers must be between 1 and 32")
    validated = tuple(
        dict.fromkeys(validate_postal_code(code) for code in postal_codes)
    )
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(lookup, postal_code): postal_code
            for postal_code in validated
        }
        for future in as_completed(futures):
            postal_code = futures[future]
            results[postal_code] = future.result()
    return results
