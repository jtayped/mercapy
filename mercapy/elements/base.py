from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urljoin
import time

from ..utils.api import fetch_json
from ..constants import API_URL


def lazy_load_property(func):
    @property
    def wrapper(self):
        if self._is_empty():
            self._fetch_data()
        return func(self)

    return wrapper


@dataclass
class MercadonaItem:
    """
    Represents a season in Mercadona's catalog.

    Args:
        id (str | dict): Season identifier.
        endpoint (str): API endpoint to fetch data from.
        warehouse (str): Warehouse or distribution center postal code. Defaults to "mad1".
        language (str): Language for the API response. Defaults to "es".
    """

    id: str | dict
    endpoint: str = field(repr=False)
    warehouse: str = "mad1"
    language: Literal["es", "en"] = field(default="es", init=True, repr=False)
    _data: dict = field(init=False, default=None, repr=False)

    def __post_init__(self):
        if isinstance(self.id, dict):
            self._data = self.id
            self.id = self._data.get("id")

    def _fetch_with_context(self, endpoint: str) -> dict:
        url = urljoin(API_URL, endpoint)
        return fetch_json(url, {"lang": self.language, "wh": self.warehouse})

    def _fetch_data(self, retry_attempts: int = 3, retry_delay: int = 20) -> None:
        attempt = 0
        while attempt <= retry_attempts:
            self._data = self._fetch_with_context(self.endpoint)
            err_code = self._data.get("err_code")

            if err_code is None:
                # No error, data fetched successfully
                break
            elif err_code == 429:
                # Too Many Requests, retry
                attempt += 1
                calculated_delay = attempt**2 * retry_delay
                print(
                    f"[{attempt}/{retry_attempts}]: Retrying to fetch {self} in {calculated_delay} seconds..."
                )
                time.sleep(calculated_delay)
            elif err_code == 404:
                # Not Found, no need to retry
                print(f"Couldn't find {self} :(")
                self._data = None
                break
            else:
                # Other errors, stop retrying
                print(f"Error fetching data for {self}.")
                self._data = None
                break

    def _is_empty(self):
        return not bool(self._data)

    def __dict__(self):
        if self._is_empty():
            self._fetch_data()

        return self._data
