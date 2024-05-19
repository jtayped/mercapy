from dataclasses import dataclass, field
from urllib.parse import urljoin
from typing import Any, Dict, List, Union, Literal

from ..exceptions.product import *
from ..constants import API_URL
from ..utils.urls import get_file_path
from ..utils.api import fetch_json
from .photo import Photo


def lazy_load_property(func):
    @property
    def wrapper(self: "Product"):
        self._fetch_data()
        return func(self)

    return wrapper


@dataclass
class Product:
    id: Union[str, Dict[str, Any]]
    lang: Literal["es", "en"] = "es"
    _endpoint: str = field(init=False, repr=False)
    _response: Dict[str, Any] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.id, str):
            self._endpoint = urljoin(API_URL, f"/api/products/{self.id}")
        else:
            self._response = self.id
            self.id = self._response.get("id")
            if not self.id:
                raise ValueError("The dictionary provided must contain an 'id' key.")
            self._endpoint = urljoin(API_URL, f"/api/products/{self.id}")

    def _fetch_data(self):
        if self._response is None:
            self._response = fetch_json(self._endpoint, params={"lang": self.lang})
            self.id = self._response.get("id", self.id)

    def exists(self) -> bool:
        self._fetch_data()
        return bool(self._response)

    def get_recommended(self) -> List["Product"]:
        self._fetch_data()
        endpoint = urljoin(self._endpoint, f"/xselling/")
        response = fetch_json(endpoint, params={"lang": self.lang})
        results = response["results"]
        return [Product(r.get("id")) for r in results]

    def refresh(self):
        self._response = fetch_json(self._endpoint, params={"lang": self.lang})

    @lazy_load_property
    def ean(self) -> str:
        return self._response.get("ean")

    @lazy_load_property
    def name(self) -> str:
        return self._response.get("display_name")

    @lazy_load_property
    def legal_name(self) -> str:
        return self._response.get("details", {}).get("legal_name")

    @lazy_load_property
    def price(self) -> float:
        return self._response.get("price_instructions", {}).get("unit_price")

    @lazy_load_property
    def iva(self) -> float:
        return self._response.get("price_instructions", {}).get("iva")

    @lazy_load_property
    def age_check(self) -> bool:
        return self._response.get("badges", {}).get("requires_age_check", False)

    @lazy_load_property
    def alcohol_by_volume(self) -> float:
        percentage = self._response.get("details", {}).get("alcohol_by_volume")
        if percentage:
            return float(percentage.removesuffix("º"))
        return None

    @lazy_load_property
    def is_new(self) -> bool:
        return self._response.get("price_instructions", {}).get("is_new", False)

    @lazy_load_property
    def is_pack(self) -> bool:
        return self._response.get("price_instructions", {}).get("is_pack", False)

    @lazy_load_property
    def photos(self) -> List[Photo]:
        photos = self._response.get("photos", [])
        return [Photo(get_file_path(p.get("regular"))) for p in photos]

    @lazy_load_property
    def description(self) -> str:
        return self._response.get("details", {}).get("description", "")

    @lazy_load_property
    def minimum_amount(self) -> float:
        return self._response.get("price_instructions", {}).get("min_bunch_amount", 1)

    @lazy_load_property
    def previous_price(self) -> float:
        return self._response.get("price_instructions", {}).get("previous_unit_price")

    @lazy_load_property
    def weight(self) -> float:
        return self._response.get("price_instructions", {}).get("unit_size")

    @lazy_load_property
    def brand(self) -> str:
        return self._response.get("brand")

    @lazy_load_property
    def origin(self) -> str:
        return self._response.get("details", {}).get("origin")

    @lazy_load_property
    def suppliers(self) -> List[str]:
        suppliers = self._response.get("details", {}).get("suppliers", [])
        return [s["name"] for s in suppliers]

    @lazy_load_property
    def __dict__(self):
        return self._response
