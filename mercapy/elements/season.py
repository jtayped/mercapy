from typing import Literal

from .base import MercadonaItem, lazy_load_property
from .product import Product


class Season(MercadonaItem):
    def __init__(
        self,
        id: str | dict,
        warehouse: str = "mad1",
        language: Literal["es", "en"] = "es",
    ):
        if isinstance(id, dict):
            endpoint = f"/api/home/seasons/{id.get("id")}/"
        else:
            endpoint = f"/api/home/seasons/{id}/"
        
        super().__init__(id, endpoint, warehouse, language)

    @lazy_load_property
    def title(self) -> str:
        return self._data.get("title")

    @lazy_load_property
    def products(self) -> list[Product]:
        items = self._data.get("items", [])
        return [Product(i, self.warehouse, self.language) for i in items]
