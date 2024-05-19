from dataclasses import dataclass
from urllib.parse import urljoin

from ..constants import *
from ..utils.api import fetch_json
from .product import Product


@dataclass
class Season:
    id: str
    wh: str
    lang: str = "es"

    def __post_init__(self):
        self._endpoint = f"https://tienda.mercadona.es/api/home/seasons/{self.id}/?lang={self.lang}&wh={self.wh}"
        self._response = self._request()

    def exists(self) -> bool:
        return bool(self._response)

    def _request(self):
        return fetch_json(self._endpoint)

    @property
    def title(self):
        return self._response.get("title")

    @property
    def products(self):
        items = self._response.get("items", [])
        return [Product(i["id"]) for i in items]
