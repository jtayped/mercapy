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


def get_home_recommendations(lang: str = "es") -> dict:
    """
    Retrieves product recommendations for the home page grouped by sections.

    Args:
        lang (str): Language code. Defaults to Spanish. Can be "en" for English.

    Returns:
        dict: Dictionary where keys are section names (or "layout") and values are lists of recommended products.
    """
    url = urljoin(API_URL, f"/api/home/?lang={lang}")
    response = fetch_json(url)

    sections = response.get("sections", [])

    # Dictionary to store products grouped by sections
    section_products = {}

    for section in sections:
        section_name = section.get(
            "layout"
        )

        # Banners often aren't actual products but "seasons" or groups of products
        if section_name != "banner":
            items = section.get("content", {}).get("items", [])

            products = [Product(item["id"]) for item in items]
            section_products[section_name] = products

    return section_products


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
