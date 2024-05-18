from .utils.api import query_algolia, fetch_json
from .constants import API_URL
from .product import Product

from urllib.parse import urljoin


def search(query: str, lang: str = "es") -> list[Product]:
    """
    Queries Mercadona's products using their provider "Algolia".

    Args:
        query (str): Search query (e.g. Dish Soap).
        lang (str): Language code. Defaults to spanish. Can be "en" too.

    Rerturns:
        list[Product]: List of products related to the search.
    """
    response = query_algolia(query, lang)
    hits = response.get("hits", [])

    products = []
    for h in hits:
        product = Product(h["id"])

        # The search provider for Mercadona sometimes returns products that don't exists
        # so before adding them to the list, it must be checked
        if product.exists():
            products.append(product)

    return products


def get_home_recommendations(lang: str = "es") -> list[Product]:
    """
    Product recommendations on the home page.

    Args:
        lang (str): Language code. Defaults to spanish. Can be "en" too.

    Returns:
        list[Product]: List of recommended products.
    """
    url = urljoin(API_URL, f"/api/home/?lang={lang}")
    response = fetch_json(url)

    products = [
        Product(item["id"])
        for section in response.get("sections", [])
        for item in section.get("content", {}).get("items", [])
    ]
    return products


def get_new_arrivals(lang: str = "es") -> list[Product]:
    """
    New product arrivals at Mercadona

    Args:
        lang (str): Language code. Defaults to spanish. Can be "en" too.

    Returns:
        list[Product]: List of new product arrivals.
    """
    url = urljoin(API_URL, f"/api/home/new-arrivals/?lang={lang}")
    response = fetch_json(url)

    products = [Product(item["id"]) for item in response.get("items")]
    return products
