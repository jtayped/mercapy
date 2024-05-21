from dataclasses import dataclass, field
from urllib.parse import urljoin
from typing import Literal

from ..constants import MAD1, API_URL
from ..utils.api import fetch_json


@dataclass
class Category:
    id: str
    name: str = None
    warehouse: str = MAD1
    language: Literal["es", "en"] = "es"
    _endpoint: str = field(init=False, repr=False)
    _response: dict = field(default=None, init=False, repr=False)

    def get_products(self):
        from .product import Product

        url = urljoin(API_URL, f"/api/categories/{self.id}/")
        response = fetch_json(url, {"lang": self.language, "wh": self.warehouse})

        category_products = []
        subcategories = response.get("categories", [])
        for subcategory in subcategories:
            products = subcategory.get("products", [])

            for product_data in products:
                product = Product(product_data, self.warehouse, self.language)
                category_products.append(product)

        return category_products
