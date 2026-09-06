"""Exceptions raised by Mercapy."""


class MercapyError(Exception):
    """Base class for all Mercapy errors."""


class ConfigurationError(MercapyError, ValueError):
    """The client or a request was configured with an invalid value."""


class TransportError(MercapyError):
    """A request failed before Mercapy received a usable response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(TransportError):
    """The upstream service kept returning HTTP 429."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NotFoundError(TransportError):
    """The requested Mercadona resource does not exist."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class InvalidResponseError(MercapyError):
    """The upstream response is not valid JSON or has no usable structure."""
