from typing import Literal

from .base import MercadonaItem, lazy_load_property
from .category import Category
from ..constants import *
from ..utils.urls import get_file_path
from .photo import Photo


def require_complete_data(func):
    def wrapper(self):
        if self._is_data_incomplete():
            self._fetch_data()

        value = func(self)
        return value

    return wrapper


class Product(MercadonaItem):
    def __init__(
        self,
        id: str | dict,
        warehouse: str = "mad1",
        language: Literal["es", "en"] = "es",
    ):
        if isinstance(id, dict):
            endpoint = f"/api/products/{id.get("id")}/"
        else:
            endpoint = f"/api/products/{id}/"

        super().__init__(id, endpoint, warehouse, language)

    def _is_data_incomplete(self):
        if self._data is None:
            return True
        
        details = self._data.get("details", {})
        return not details

    @lazy_load_property
    @require_complete_data
    def ean(self) -> str:
        """
        Returns the European Article Number (EAN) for the product.
        """
        return self._data.get("ean")

    @lazy_load_property
    def name(self) -> str:
        """
        Returns the display name of the product.
        """
        return self._data.get("display_name")

    @lazy_load_property
    def slug(self) -> str:
        """
        Returns the slug (URL-friendly version of the name) for the product.
        """
        return self._data.get("slug")

    @lazy_load_property
    @require_complete_data
    def legal_name(self) -> str | None:
        """
        Returns the legal name of the product.
        """
        details = self._data.get("details", {})
        return details.get("legal_name", None)

    @lazy_load_property
    def unit_price(self) -> float | None:
        """
        Returns the unit price of the product.
        """
        return float(self._data.get("price_instructions", {}).get("unit_price"))

    @lazy_load_property
    def bulk_price(self) -> float | None:
        """
        Returns the bulk price of the product.

        Returns:
            float: The bulk price as a float, or None if not available.
        """
        return float(self._data.get("price_instructions", {}).get("bulk_price", None))

    @lazy_load_property
    def is_discounted(self) -> bool:
        """
        Checks if the product is currently discounted.
        """
        return self._data.get("price_instructions", {}).get("price_decreased")

    @lazy_load_property
    @require_complete_data
    def previous_price(self) -> float | None:
        """
        Returns the previous unit price before any discounts.
        """
        return self._data.get("price_instructions", {}).get("previous_unit_price")

    @lazy_load_property
    def iva(self) -> int:
        """
        Returns the tax rate (IVA) applied to the product.
        """
        return self._data.get("price_instructions", {}).get("iva")

    @lazy_load_property
    def age_check(self) -> bool:
        """
        Checks if the product requires an age check.
        """
        return self._data.get("badges", {}).get("requires_age_check", False)

    @lazy_load_property
    @require_complete_data
    def alcohol_by_volume(self) -> float | None:
        """
        Returns the alcohol by volume percentage of the product.
        """
        details = self._data.get("details", {})
        percentage = details.get("alcohol_by_volume")

        if percentage:
            return float(percentage.removesuffix("º"))

    @lazy_load_property
    def is_new(self) -> bool:
        """
        Checks if the product is new.
        """
        return self._data.get("price_instructions", {}).get("is_new", False)

    @lazy_load_property
    def is_pack(self) -> bool:
        """
        Checks if the product is sold as a pack.
        """
        return self._data.get("price_instructions", {}).get("is_pack", False)

    @lazy_load_property
    def pack_size(self) -> int | None:
        """
        Returns the pack size of the product, if applicable.
        """
        if not self.is_pack:
            return None

        return self._data.get("price_instructions", {}).get("pack_size",  None)

    @lazy_load_property
    def total_units(self) -> int | None:
        """
        Returns the total units in the pack, if applicable.
        """
        if not self.is_pack:
            return None
        
        return self._data.get("price_instructions", {}).get("total_units", None)

    @lazy_load_property
    @require_complete_data
    def photos(self) -> list[Photo]:
        """
        Returns the list of photos for the product.
        """
        photos = self._data.get("photos", [])
        return [Photo(get_file_path(p.get("regular"))) for p in photos]

    @lazy_load_property
    @require_complete_data
    def description(self) -> str:
        """
        Returns the description of the product.
        """
        details = self._data.get("details", {})
        return details.get("description", "")

    @lazy_load_property
    def minimum_amount(self) -> int:
        """
        Returns the minimum amount that can be purchased.
        """
        return int(self._data.get("price_instructions", {}).get("min_bunch_amount", 1))

    @lazy_load_property
    def weight(self) -> float:
        """
        Returns the weight of the product.
        """
        return self._data.get("price_instructions", {}).get("unit_size")

    @lazy_load_property
    def brand(self) -> str:
        """
        Returns the brand of the product.
        """
        return self._data.get("brand")

    @lazy_load_property
    @require_complete_data
    def origin(self) -> str | None:
        """
        Returns the origin of the product.
        """
        details = self._data.get("details", {})
        return details.get("origin", None)

    @lazy_load_property
    @require_complete_data
    def supplier(self) -> str:
        """
        Returns the supplier of the product.
        """
        details = self._data.get("details", {})
        suppliers = details.get("suppliers", [])
        return suppliers[0].get("name")

    @lazy_load_property
    def category(self) -> list[str]:
        """
        Returns the category of the product.
        """
        high_level_category = self._data.get("categories", [])[0]
        category_data = high_level_category.get("categories", [])[0]
        
        category = Category(category_data, self.warehouse, self.language)
        return category
    
    def __dict__(self):
        """
        Converts the product object to a dictionary.
        """
        return {
            "id": self.id,
            "warehouse": self.warehouse,
            "language": self.language,
            "ean": self.ean,
            "name": self.name,
            "slug": self.slug,
            "legal_name": self.legal_name,
            "unit_price": self.unit_price,
            "bulk_price": self.bulk_price,
            "is_discounted": self.is_discounted,
            "previous_price": self.previous_price,
            "iva": self.iva,
            "age_check": self.age_check,
            "alcohol_by_volume": self.alcohol_by_volume,
            "is_new": self.is_new,
            "is_pack": self.is_pack,
            "pack_size": self.pack_size,
            "description": self.description,
            "minimum_amount": self.minimum_amount,
            "weight": self.weight,
            "brand": self.brand,
            "origin": self.origin,
            "supplier": self.supplier,
            "category": self.category.name
        }
