from typing import Literal

from .base import MercadonaItem, lazy_load_property

class Category(MercadonaItem):
    def __init__(
        self,
        id: str | dict,
        name: str,
        warehouse: str = "mad1",
        language: Literal["es", "en"] = "es",
    ):
        self.name = name

        if isinstance(id, dict):
            endpoint = f"/api/categories/{id.get("id")}/"
        else:
            endpoint = f"/api/categories/{id}/"

        super().__init__(id, endpoint, warehouse, language)

    @lazy_load_property
    def products(self):
        from .product import Product

        category_products = []
        subcategories = self._data.get("categories", [])
        for subcategory in subcategories:
            products = subcategory.get("products", [])

            for product_data in products:
                product = Product(product_data, self.warehouse, self.language)
                category_products.append(product)

        return category_products
