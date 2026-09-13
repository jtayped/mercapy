"""mercapy's public api."""

from ._version import __version__
from .client import Mercadona, RetryPolicy
from .discovery import discover_warehouses, resolve_warehouse
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
    CatalogResult,
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
    "CatalogResult",
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
    "discover_warehouses",
    "resolve_warehouse",
]
