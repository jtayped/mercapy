from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from typing import Any

import httpx
import pytest

from mercapy import (
    ConfigurationError,
    InvalidResponseError,
    Mercadona,
    NotFoundError,
    RateLimitError,
    RetryPolicy,
    TransportError,
)


def client_for(
    handler: Any,
    *,
    attempts: int = 3,
    backoff: float = 0.25,
    max_delay: float = 5,
    jitter: float = 0,
    interval: float = 0,
) -> Mercadona:
    return Mercadona(
        "mad3",
        retry_policy=RetryPolicy(
            max_attempts=attempts,
            backoff_factor=backoff,
            max_delay=max_delay,
            jitter_ratio=jitter,
        ),
        min_request_interval=interval,
        transport=httpx.MockTransport(handler),
    )


def test_connection_errors_are_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.ConnectError("offline", request=request)
        return httpx.Response(200, request=request, json={"results": []})

    monkeypatch.setattr("mercapy.client.time.sleep", delays.append)
    with client_for(handler) as client:
        assert client.get_categories() == ()
    assert attempts == 3
    assert delays == [0.25, 0.5]


def test_exhausted_connection_errors_raise_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectTimeout("offline", request=request)

    monkeypatch.setattr("mercapy.client.time.sleep", lambda delay: None)
    with (
        client_for(handler, attempts=2) as client,
        pytest.raises(TransportError, match="2 connection attempts"),
    ):
        client.get_categories()
    assert attempts == 2


def test_read_timeout_is_not_retried() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("slow", request=request)

    with client_for(handler) as client, pytest.raises(TransportError, match="slow"):
        client.get_categories()
    assert attempts == 1


@pytest.mark.parametrize("body", [b"not-json", b"[]"])
def test_invalid_json_or_top_level_shape_raises(body: bytes) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, request=request, content=body)
    )
    with (
        client_for(transport.handle_request) as client,
        pytest.raises(InvalidResponseError),
    ):
        client.get_categories()


@pytest.mark.parametrize(
    ("operation", "payload", "message"),
    [
        ("get_categories", {}, "results array"),
        ("get_home", {}, "sections array"),
        ("get_new_arrivals", {}, "items array"),
        ("search_products", {}, "hits array"),
        ("get_product", {"id": "1"}, "product name"),
    ],
)
def test_unusable_response_shapes_raise(
    operation: str, payload: object, message: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json=payload)

    with client_for(handler) as client:
        arguments = ("x",) if operation in {"search_products", "get_product"} else ()
        with pytest.raises(InvalidResponseError, match=message):
            getattr(client, operation)(*arguments)


def test_404_and_ordinary_4xx_are_not_retried() -> None:
    for status_code, exception in [(404, NotFoundError), (400, TransportError)]:
        attempts = 0

        def handler(
            request: httpx.Request, response_status: int = status_code
        ) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            return httpx.Response(response_status, request=request)

        with client_for(handler) as client, pytest.raises(exception) as raised:
            client.get_product("missing")
        assert raised.value.status_code == status_code
        assert attempts == 1


def test_429_honors_numeric_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, request=request, headers={"Retry-After": "12"})
        return httpx.Response(200, request=request, json={"results": []})

    monkeypatch.setattr("mercapy.client.time.sleep", delays.append)
    with client_for(handler, max_delay=2) as client:
        client.get_categories()
    assert attempts == 2
    assert delays == [2]


def test_429_without_retry_after_uses_backoff_and_exhausts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, request=request)

    monkeypatch.setattr("mercapy.client.time.sleep", delays.append)
    with (
        client_for(handler, attempts=2) as client,
        pytest.raises(RateLimitError) as raised,
    ):
        client.get_categories()
    assert raised.value.retry_after is None
    assert delays == [0.25]


def test_429_parses_http_date_and_ignores_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    future = format_datetime(datetime.now(UTC) + timedelta(seconds=30), usegmt=True)
    headers = iter((future, "not-a-date", None))
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        retry_after = next(headers)
        if retry_after is None:
            return httpx.Response(200, request=request, json={"results": []})
        return httpx.Response(
            429, request=request, headers={"Retry-After": retry_after}
        )

    monkeypatch.setattr("mercapy.client.time.sleep", delays.append)
    with client_for(handler, max_delay=1) as client:
        client.get_categories()
    assert delays == [1, 0.5]


def test_transient_5xx_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statuses = iter((503, 500, 200))
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        status = next(statuses)
        return httpx.Response(
            status,
            request=request,
            json={"results": []} if status == 200 else None,
        )

    monkeypatch.setattr("mercapy.client.time.sleep", delays.append)
    with client_for(handler) as client:
        client.get_categories()
    assert delays == [0.25, 0.5]


def test_backoff_adds_bounded_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    statuses = iter((503, 200))
    delays: list[float] = []

    class MaximumJitter:
        @staticmethod
        def uniform(lower: float, upper: float) -> float:
            assert lower == 0
            return upper

    def handler(request: httpx.Request) -> httpx.Response:
        status = next(statuses)
        return httpx.Response(
            status,
            request=request,
            json={"results": []} if status == 200 else None,
        )

    monkeypatch.setattr("mercapy.client._JITTER", MaximumJitter())
    monkeypatch.setattr("mercapy.client.time.sleep", delays.append)
    with client_for(handler, jitter=0.2) as client:
        client.get_categories()

    assert delays == pytest.approx([0.3])


def test_request_pacing_also_applies_to_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statuses = iter((503, 200))
    clock = [10.0]
    delays: list[float] = []

    def sleep(delay: float) -> None:
        delays.append(delay)
        clock[0] += delay

    def handler(request: httpx.Request) -> httpx.Response:
        status = next(statuses)
        return httpx.Response(
            status,
            request=request,
            json={"results": []} if status == 200 else None,
        )

    monkeypatch.setattr("mercapy.client.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("mercapy.client.time.sleep", sleep)
    with client_for(handler, interval=0.5) as client:
        client.get_categories()

    assert delays == pytest.approx([0.25, 0.25])


@pytest.mark.parametrize("status", [500, 501])
def test_server_error_exhaustion_raises_transport_error(
    status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(status, request=request)

    monkeypatch.setattr("mercapy.client.time.sleep", lambda delay: None)
    with (
        client_for(handler, attempts=2) as client,
        pytest.raises(TransportError) as raised,
    ):
        client.get_categories()
    assert raised.value.status_code == status
    assert attempts == (2 if status == 500 else 1)


def test_postcode_transport_and_invalid_header_errors_close_cleanly() -> None:
    def bad_header(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, request=request, headers={"X-Customer-Wh": "bad/value"}, json={}
        )

    with pytest.raises(ConfigurationError, match="warehouse"):
        Mercadona.from_postal_code("28001", transport=httpx.MockTransport(bad_header))
