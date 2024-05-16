from dataclasses import dataclass
from urllib.parse import urljoin
import requests, json

from ..exceptions.product import *
from ..constants import API_URL
from .image import Image


@dataclass
class Product:
    id: str
    ean: str
    name: str
    legal_name: str
    price: float
    iva: float

    age_check: bool = False
    is_new: bool = False
    is_pack: bool = False
    photos: list[Image] = None
    description: str = None
    minimum_amount: float = None
    previous_price: float = None
    unit_size: float = None
    brand: str = None
    origin: str = None
    supplier: str = None

    def __post_init__(self):
        self._endpoint = urljoin(API_URL, f"/products/{self.id}")

        if not self._product_exists():
            raise ProductNotFound

    def _request_product(self) -> dict:
        try:
            response = requests.get(self._endpoint)
            response.raise_for_status()

            # Check if response is JSON and parse it into a dictionary
            if "application/json" in response.headers.get("content-type", ""):
                return response.json()

            # If response is not JSON, return the raw text
            return response.text

        except requests.exceptions.RequestException as e:
            raise ErrorFetchingProduct

    def _product_exists(self) -> bool:
        pass
