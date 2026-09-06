from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from mercapy import ConfigurationError, Mercadona, Photo, RetryPolicy, TransportError


def temporary_siblings(destination: Path) -> list[Path]:
    return list(destination.parent.glob(f".{destination.name}.*.tmp"))


def test_download_photo_streams_resized_image_atomically(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, request=request, content=b"image-bytes")

    destination = tmp_path / "nested" / "photo.jpg"
    with Mercadona("mad3", transport=httpx.MockTransport(handler)) as client:
        result = client.download_photo(
            Photo("photo.jpg"), destination, width=640, height=480, fit="fit"
        )

    assert result == destination
    assert destination.read_bytes() == b"image-bytes"
    assert requests[0].url == httpx.URL(
        "https://prod-mercadona.imgix.net/images/photo.jpg?fit=fit&h=480&w=640"
    )
    assert temporary_siblings(destination) == []


def test_failed_download_preserves_existing_destination(tmp_path: Path) -> None:
    destination = tmp_path / "photo.jpg"
    destination.write_bytes(b"old")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, request=request)

    with (
        Mercadona(
            "mad3",
            retry_policy=RetryPolicy(max_attempts=1),
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(TransportError),
    ):
        client.download_photo(Photo("photo.jpg"), destination)
    assert destination.read_bytes() == b"old"
    assert temporary_siblings(destination) == []


class BrokenStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b"partial"
        raise httpx.ReadError("connection interrupted")


def test_interrupted_download_removes_temporary_file(tmp_path: Path) -> None:
    destination = tmp_path / "photo.jpg"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, stream=BrokenStream())

    with (
        Mercadona("mad3", transport=httpx.MockTransport(handler)) as client,
        pytest.raises(TransportError, match="interrupted"),
    ):
        client.download_photo(Photo("photo.jpg"), destination)
    assert not destination.exists()
    assert temporary_siblings(destination) == []


def test_download_validates_photo_and_destination(tmp_path: Path) -> None:
    with Mercadona("mad3") as client:
        with pytest.raises(ConfigurationError, match="Photo"):
            client.download_photo("photo.jpg", tmp_path / "x")  # type: ignore[arg-type]
        with pytest.raises(ConfigurationError, match="file path"):
            client.download_photo(Photo("photo.jpg"), tmp_path)
