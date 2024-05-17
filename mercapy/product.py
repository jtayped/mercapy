from dataclasses import dataclass
from urllib.parse import urljoin

from .exceptions.product import *
from .constants import API_URL
from .utils.urls import get_file_path
from .utils.api import fetch_json
from .product.photo import Photo


@dataclass
class Product:
    id: str
    lang: str = "es"

    def __post_init__(self):
        self._endpoint = urljoin(API_URL, f"/api/products/{self.id}")
        self._response = self._request(self._endpoint)
        if not self._product_exists():
            raise ProductNotFound(self.id)

    def _product_exists(self) -> bool:
        return bool(self._response)

    def _request(self, url):
        return fetch_json(url, params={"lang": self.lang})

    def get_recommended(self) -> list["Product"]:
        endpoint = urljoin(self._endpoint, f"/api/products/{self.id}/xselling/")

        response = self._request(endpoint)
        results = response["results"]

        return [Product(r.get("id")) for r in results]

    def refresh(self):
        self._response = self._request(self._endpoint)

    @property
    def ean(self) -> str:
        return self._response.get("ean")

    @property
    def name(self) -> str:
        return self._response.get("display_name")

    @property
    def legal_name(self) -> str:
        return self._response.get("details", {}).get("legal_name", None)

    @property
    def price(self) -> float:
        return self._response.get("price_instructions", {}).get("unit_price", None)

    @property
    def iva(self) -> float:
        return self._response.get("price_instructions", {}).get("iva", None)

    @property
    def age_check(self) -> bool:
        return self._response.get("badges", {}).get("requires_age_check", False)

    @property
    def alcohol_by_volume(self) -> float:
        percentage = self._response.get("details", {}).get("alcohol_by_volume", None)

        if not percentage:
            return

        # "37.5ª"  ->  37.5"
        percentage = float(percentage.removesuffix("º"))
        return percentage

    @property
    def is_new(self) -> bool:
        return self._response.get("price_instructions", {}).get("is_new", False)

    @property
    def is_pack(self) -> bool:
        return self._response.get("price_instructions", {}).get("is_pack", False)

    @property
    def photos(self) -> list[Photo]:
        photos = self._response.get("photos", [])
        return [Photo(get_file_path(p.get("regular"))) for p in photos]

    @property
    def description(self) -> str:
        return self._response.get("details", {}).get("description", "")

    @property
    def minimum_amount(self) -> float:
        return self._response.get("price_instructions", {}).get("min_bunch_amount", 1)

    @property
    def previous_price(self) -> float:
        return self._response.get("price_instructions", {}).get(
            "previous_unit_price", None
        )

    @property
    def weight(self) -> float:
        return self._response.get("price_instructions", {}).get("unit_size", None)

    @property
    def brand(self) -> str:
        return self._response.get("brand", None)

    @property
    def origin(self) -> str:
        return self._response.get("details", {}).get("origin", None)

    @property
    def suppliers(self) -> list[str]:
        suppliers = self._response.get("details", {}).get("suppliers", [])
        return [s["name"] for s in suppliers]
