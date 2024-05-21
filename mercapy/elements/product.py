from typing import Literal

from .base import MercadonaItem, lazy_load_property
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
        details = self._data.get("details", None)
        if not details:
            self._fetch_data()

    @lazy_load_property
    @require_complete_data
    def ean(self) -> str:
        return self._data.get("ean")

    @lazy_load_property
    def name(self) -> str:
        return self._data.get("display_name")

    @lazy_load_property
    def slug(self) -> str:
        return self._data.get("slug")

    @lazy_load_property
    @require_complete_data
    def legal_name(self) -> str:
        details = self._data.get("details", {})
        return details.get("legal_name")

    @lazy_load_property
    def unit_price(self) -> float | None:
        return float(self._data.get("price_instructions", {}).get("unit_price"))

    @lazy_load_property
    def bulk_price(self) -> float:
        return float(self._data.get("price_instructions", {}).get("bulk_price"))

    @lazy_load_property
    def is_discounted(self) -> bool:
        return self._data.get("price_instructions", {}).get("price_decreased")

    @lazy_load_property
    @require_complete_data
    def previous_price(self) -> float | None:
        return self._data.get("price_instructions", {}).get("previous_unit_price")

    @lazy_load_property
    def iva(self) -> int:
        return self._data.get("price_instructions", {}).get("iva")

    @lazy_load_property
    def age_check(self) -> bool:
        return self._data.get("badges", {}).get("requires_age_check", False)

    @lazy_load_property
    @require_complete_data
    def alcohol_by_volume(self) -> float | None:
        details = self._data.get("details", {})
        percentage = details.get("alcohol_by_volume")

        if percentage:
            return float(percentage.removesuffix("º"))

    @lazy_load_property
    def is_new(self) -> bool:
        return self._data.get("price_instructions", {}).get("is_new", False)

    @lazy_load_property
    def is_pack(self) -> bool:
        return self._data.get("price_instructions", {}).get("is_pack", False)

    @lazy_load_property
    def pack_size(self) -> int | None:
        if not self.is_pack:
            return None

        return self._data.get("price_instructions", {}).get("pack_size")

    @lazy_load_property
    def photos(self) -> list[Photo]:
        photos = self._data.get("photos", [])

        # If photos aren't found, it is probable that a dict was provided without
        # the photo information. So fetching the data from the main product endpoint
        # the information can be populated.
        if not photos:
            self._fetch_data()
            photos = self._data.get("photos", [])

        return [Photo(get_file_path(p.get("regular"))) for p in photos]

    @lazy_load_property
    @require_complete_data
    def description(self) -> str:
        details = self._data.get("details", {})
        return details.get("description", "")

    @lazy_load_property
    def minimum_amount(self) -> int:
        return self._data.get("price_instructions", {}).get("min_bunch_amount", 1)

    @lazy_load_property
    def weight(self) -> float:
        return self._data.get("price_instructions", {}).get("unit_size")

    @lazy_load_property
    def brand(self) -> str:
        return self._data.get("brand")

    @lazy_load_property
    @require_complete_data
    def origin(self) -> str:
        details = self._data.get("details", {})

        return details.get("origin")

    @lazy_load_property
    @require_complete_data
    def suppliers(self) -> list[str]:
        details = self._data.get("details", {})
        suppliers = details.get("suppliers", [])
        return [s["name"] for s in suppliers]

    @lazy_load_property
    def categories(self) -> list[str]:
        categories = self._data.get("categories", [])
        return [c["name"] for c in categories]
