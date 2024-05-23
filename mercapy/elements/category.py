from typing import Literal

from .base import MercadonaItem, lazy_load_property

def require_complete_data(func):
    def wrapper(self):
        if self._is_data_incomplete():
            self._fetch_data()

        value = func(self)
        return value

    return wrapper

class Category(MercadonaItem):
    def __init__(
        self,
        id: str | dict,
        warehouse: str,
        language: Literal["es", "en"] = "es",
    ):
        if isinstance(id, dict):
            endpoint = f"/api/categories/{id.get("id")}/"
        else:
            endpoint = f"/api/categories/{id}/"

        super().__init__(id, endpoint, warehouse, language)

    def _is_data_incomplete(self):      
        subcategories = self._data.get("categories", None)
        return subcategories is None

    @lazy_load_property
    @require_complete_data
    def products(self):
        from .product import Product

        category_products = []
        subcategories = self._data.get("categories", [])

        for subcategory in subcategories:
            products = subcategory.get("products", None)

            for product_data in products:
                product = Product(product_data, self.warehouse, self.language)
                category_products.append(product)

        return category_products

    @lazy_load_property
    def name(self):
        return self._data.get("name")
