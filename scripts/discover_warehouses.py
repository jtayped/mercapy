"""resolve explicit spanish postal codes to mercadona warehouses."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from mercapy.discovery import discover_warehouses, resolve_warehouse

lookup_warehouse = resolve_warehouse


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
