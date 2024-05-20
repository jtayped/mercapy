from dataclasses import dataclass, field
from urllib.parse import urljoin
from typing import List, Union, Literal
import time

from ..constants import *
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
    """
    Represents a product in Mercadona's catalog.

    Args:
        id (str or dict): Product's identifier or information from Mercadona's API.
        warehouse (str): Warehouse or distribution center postal code. Defaults to the one in Níjar, Almería.
        lang (str): The language in which the API responds. Defaults to spanish ("es"), and can also be english ("en").
    """

    id: Union[str, dict]
    warehouse: str = MAD1
    lang: Literal["es", "en"] = "es"
    _endpoint: str = field(init=False, repr=False)
    _response: dict = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.id, dict):
            self._response = self.id
            self.id = self._response.get("id")
            if not self.id:
                raise ValueError("The dictionary provided must contain an 'id' key.")

        self._endpoint = urljoin(API_URL, f"/api/products/{self.id}")

    def _fetch_data(self, override=False, retry_attempts=3, retry_delay=10):
        if override or self._response is None:
            attempt = 0
            while attempt < retry_attempts:
                self._response = fetch_json(
                    self._endpoint,
                    params={"lang": self.lang, "wh": self.warehouse},
                )
                err_code = self._response.get("err_code")

                if err_code is None:
                    # No error, break out of the loop
                    break
                elif err_code == 429:
                    # Too Many Requests, need to retry
                    attempt += 1
                    if attempt < retry_attempts:
                        time.sleep(retry_delay)
                        print(
                            f"[{attempt}/{retry_attempts}]: Retrying to fetch {self.id} in {retry_delay} seconds..."
                        )
                elif err_code == 404:
                    print(f"Couldn't find {self.id} :(")
                    self._response = None
                    break  # no need to retry

    def exists(self) -> bool:
        self._fetch_data()
        return bool(self._response)

    def get_recommended(self) -> List["Product"]:
        self._fetch_data()
        endpoint = urljoin(API_URL, f"/api/products/{self.id}/xselling/")
        response = fetch_json(
            endpoint, params={"lang": self.lang, "wh": self.warehouse}
        )
        results = response.get("results", [])
        return [Product(r) for r in results]

    def refresh(self):
        self._response = fetch_json(self._endpoint, params={"lang": self.lang})

    @lazy_load_property
    def ean(self) -> str:
        ean = self._response.get("ean")

        if not ean:
            self._fetch_data(override=True)

        ean = self._response.get("ean")
        return self._response.get("ean")

    @lazy_load_property
    def name(self) -> str:
        return self._response.get("display_name")

    @lazy_load_property
    def slug(self) -> str:
        return self._response.get("slug")

    @lazy_load_property
    def legal_name(self) -> str:
        details = self._response.get("details", None)
        if not details:
            self._fetch_data(override=True)

        details = self._response.get("details", {})
        return details.get("legal_name")

    @lazy_load_property
    def unit_price(self) -> float | None:
        try:
            return float(self._response.get("price_instructions", {}).get("unit_price"))
        except:
            print(self._response)

    @lazy_load_property
    def bulk_price(self) -> float:
        return float(self._response.get("price_instructions", {}).get("bulk_price"))

    @lazy_load_property
    def is_discounted(self) -> bool:
        return self._response.get("price_instructions", {}).get("price_decreased")

    @lazy_load_property
    def previous_price(self) -> float | None:
        if not self.is_discounted:
            return None

        return self._response.get("price_instructions", {}).get("previous_unit_price")

    @lazy_load_property
    def iva(self) -> int:
        return self._response.get("price_instructions", {}).get("iva")

    @lazy_load_property
    def age_check(self) -> bool:
        return self._response.get("badges", {}).get("requires_age_check", False)

    @lazy_load_property
    def alcohol_by_volume(self) -> float | None:
        details = self._response.get("details", None)
        if not details:
            self._fetch_data(override=True)

        details = self._response.get("details", {})
        percentage = details.get("alcohol_by_volume")

        if percentage:
            return float(percentage.removesuffix("º"))

    @lazy_load_property
    def is_new(self) -> bool:
        return self._response.get("price_instructions", {}).get("is_new", False)

    @lazy_load_property
    def is_pack(self) -> bool:
        return self._response.get("price_instructions", {}).get("is_pack", False)

    @lazy_load_property
    def pack_size(self) -> int | None:
        if not self.is_pack:
            return None

        return self._response.get("price_instructions", {}).get("pack_size")

    @lazy_load_property
    def photos(self) -> List[Photo]:
        photos = self._response.get("photos", [])

        # If photos aren't found, it is probable that a dict was provided without
        # the photo information. So fetching the data from the main product endpoint
        # the information can be populated.
        if not photos:
            self._fetch_data(override=True)
            photos = self._response.get("photos", [])

        return [Photo(get_file_path(p.get("regular"))) for p in photos]

    @lazy_load_property
    def description(self) -> str:
        details = self._response.get("details", None)
        if not details:
            self._fetch_data(override=True)

        details = self._response.get("details", {})
        return details.get("description", "")

    @lazy_load_property
    def minimum_amount(self) -> int:
        return self._response.get("price_instructions", {}).get("min_bunch_amount", 1)

    @lazy_load_property
    def weight(self) -> float:
        return self._response.get("price_instructions", {}).get("unit_size")

    @lazy_load_property
    def brand(self) -> str:
        return self._response.get("brand")

    @lazy_load_property
    def origin(self) -> str:
        details = self._response.get("details", None)
        if not details:
            self._fetch_data(override=True)

        details = self._response.get("details", {})

        return details.get("origin")

    @lazy_load_property
    def suppliers(self) -> List[str]:
        details = self._response.get("details", None)
        if not details:
            self._fetch_data(override=True)

        details = self._response.get("details", {})
        suppliers = details.get("suppliers", [])
        return [s["name"] for s in suppliers]

    @lazy_load_property
    def categories(self) -> List[str]:
        categories = self._response.get("categories", [])
        return [c["name"] for c in categories]

    @lazy_load_property
    def __dict__(self):
        # If the EAN is not there, it means that the info is incomplete
        ean = self._response.get("ean")
        if not ean:
            self._fetch_data(override=True)

        return self._response
