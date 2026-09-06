"""mercapy's public api."""

from ._version import __version__
from .client import Mercadona, RetryPolicy
from .exceptions import (
    ConfigurationError,
    InvalidResponseError,
    MercapyError,
    NotFoundError,
    RateLimitError,
    TransportError,
)
from .models import (
    Availability,
    Category,
    HomeNotification,
    HomeSection,
    Language,
    Nutrition,
    Photo,
    PhotoFit,
    Price,
    Product,
    ProductDetails,
    ProductSummary,
    SearchResult,
    Season,
    SeasonSummary,
)

__all__ = [
    "Availability",
    "Category",
    "ConfigurationError",
    "HomeNotification",
    "HomeSection",
    "InvalidResponseError",
    "Language",
    "Mercadona",
    "MercapyError",
    "NotFoundError",
    "Nutrition",
    "Photo",
    "PhotoFit",
    "Price",
    "Product",
    "ProductDetails",
    "ProductSummary",
    "RateLimitError",
    "RetryPolicy",
    "SearchResult",
    "Season",
    "SeasonSummary",
    "TransportError",
    "__version__",
]
