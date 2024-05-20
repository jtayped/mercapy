from dataclasses import dataclass, field
from typing import List, Literal

from ..constants import *
from ..utils.api import fetch_json
from .product import Product


def lazy_load_property(func):
    @property
    def wrapper(self):
        self._fetch_data()
        return func(self)

    return wrapper


@dataclass
class Season:
    """
    Represents a season in Mercadona's catalog.

    Args:
        id (str): Season identifier.
        warehouse (str): Warehouse or distribution center postal code. Defaults to the one in Níjar, Almería.
        lang (str): The language in which the API responds. Defaults to spanish ("es"), and can also be english ("en").
    """

    id: str
    warehouse: str = MAD1
    lang: Literal["es", "en"] = "es"
    _endpoint: str = field(init=False, repr=False)
    _response: dict = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self._endpoint = f"https://tienda.mercadona.es/api/home/seasons/{self.id}/"

    def _fetch_data(self):
        if self._response is None:
            self._response = fetch_json(
                self._endpoint,
                params={"lang": self.lang, "wh": self.warehouse},
            )

    def exists(self) -> bool:
        self._fetch_data()
        return bool(self._response)

    @lazy_load_property
    def title(self) -> str:
        return self._response.get("title")

    @lazy_load_property
    def products(self) -> List[Product]:
        items = self._response.get("items", [])
        return [Product(i, self.warehouse) for i in items]

    @lazy_load_property
    def __dict__(self):
        return self._response
