"""resolve explicit spanish postal codes to mercadona warehouses."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from mercapy.client import validate_postal_code
from mercapy.exceptions import InvalidResponseError, TransportError

POSTAL_CODE_URL = "https://tienda.mercadona.es/api/postal-codes/actions/change-pc/"


def lookup_warehouse(postal_code: str, *, timeout: float = 5.0) -> str:
    """resolve one validated postcode."""

    postal_code = validate_postal_code(postal_code)
    try:
        response = httpx.put(
            POSTAL_CODE_URL,
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
    return str(warehouse)


def discover_warehouses(
    postal_codes: Iterable[str],
    *,
    max_workers: int = 5,
    lookup: Callable[[str], str] = lookup_warehouse,
) -> dict[str, str]:
    """resolve postcodes concurrently while retaining each future's input."""

    if not 1 <= max_workers <= 32:
        raise ValueError("max_workers must be between 1 and 32")
    validated = tuple(
        dict.fromkeys(validate_postal_code(code) for code in postal_codes)
    )
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_postcodes = {
            executor.submit(lookup, postal_code): postal_code
            for postal_code in validated
        }
        for future in as_completed(future_postcodes):
            postal_code = future_postcodes[future]
            results[postal_code] = future.result()
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve Spanish postal codes to Mercadona warehouse codes."
    )
    parser.add_argument("postal_codes", nargs="+", help="five-digit Spanish postcodes")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="concurrent requests, from 1 to 32 (default: 5)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    results = discover_warehouses(
        arguments.postal_codes, max_workers=arguments.max_workers
    )
    for postal_code, warehouse in sorted(results.items()):
        print(f"{postal_code}\t{warehouse}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
