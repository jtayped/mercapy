"""exceptions raised by mercapy."""


class MercapyError(Exception):
    """base class for all mercapy errors."""


class ConfigurationError(MercapyError, ValueError):
    """the client or a request was configured with an invalid value."""


class TransportError(MercapyError):
    """a request failed before mercapy received a usable response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(TransportError):
    """the upstream service kept returning http 429."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NotFoundError(TransportError):
    """the requested mercadona resource does not exist."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class InvalidResponseError(MercapyError):
    """the upstream response is not valid json or has no usable structure."""
