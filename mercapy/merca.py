from .utils.api import query_algolia
from .product import Product


def search(query: str):
    response = query_algolia(query)
    hits = response.get("hits", [])

    products = []
    for h in hits:
        product = Product(h["id"])
        if product.exists():
            products.append(product)

    return products
