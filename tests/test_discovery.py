from __future__ import annotations

import httpx
import pytest
from scripts.discover_warehouses import (
    discover_warehouses,
    lookup_warehouse,
    main,
)

from mercapy import ConfigurationError, InvalidResponseError, TransportError
from mercapy.client import validate_postal_code


@pytest.mark.parametrize("postal_code", ["", "2800", "2800A", "00000", "53000"])
def test_postal_code_validation_rejects_invalid_values(postal_code: str) -> None:
    with pytest.raises(ConfigurationError):
        validate_postal_code(postal_code)


def test_postal_code_validation_accepts_all_province_edges() -> None:
    assert validate_postal_code("01000") == "01000"
    assert validate_postal_code("52000") == "52000"


def test_concurrent_discovery_maps_each_result_to_submitted_postcode() -> None:
    codes = ["28001", "08001", "46001", "28001"]

    def lookup(postal_code: str) -> str:
        return f"warehouse-{postal_code}"

    assert discover_warehouses(codes, max_workers=3, lookup=lookup) == {
        "28001": "warehouse-28001",
        "08001": "warehouse-08001",
        "46001": "warehouse-46001",
    }


@pytest.mark.parametrize("workers", [0, 33])
def test_discovery_bounds_concurrency(workers: int) -> None:
    with pytest.raises(ValueError, match="max_workers"):
        discover_warehouses(["28001"], max_workers=workers)


def test_lookup_warehouse_uses_header(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("PUT", "https://example.test")
    response = httpx.Response(200, request=request, headers={"X-Customer-Wh": "mad3"})
    monkeypatch.setattr(
        "scripts.discover_warehouses.httpx.put", lambda *a, **k: response
    )
    assert lookup_warehouse("28001") == "mad3"


def test_lookup_warehouse_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("PUT", "https://example.test")
    response = httpx.Response(503, request=request)
    monkeypatch.setattr(
        "scripts.discover_warehouses.httpx.put", lambda *a, **k: response
    )
    with pytest.raises(TransportError):
        lookup_warehouse("28001")


def test_lookup_warehouse_requires_header(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("PUT", "https://example.test")
    response = httpx.Response(200, request=request)
    monkeypatch.setattr(
        "scripts.discover_warehouses.httpx.put", lambda *a, **k: response
    )
    with pytest.raises(InvalidResponseError, match="X-Customer-Wh"):
        lookup_warehouse("28001")


def test_cli_prints_sorted_mapping(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "scripts.discover_warehouses.discover_warehouses",
        lambda postal_codes, max_workers: {"28001": "mad3", "08001": "bcn1"},
    )
    assert main(["28001", "08001", "--max-workers", "2"]) == 0
    assert capsys.readouterr().out == "08001\tbcn1\n28001\tmad3\n"
