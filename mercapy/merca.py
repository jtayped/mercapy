from typing import Literal
from urllib.parse import urljoin

from .constants import WAREHOUSES, MAD1
from .utils.warehouses import get_warehouse_code
from .utils.api import *
from .elements import Product, Season


class Mercadona:

    def __init__(
        self,
        warehouse: Literal[
            "mad1",
            "mad2",
            "bcn1",
            "alc1",
            "vlc1",
        ] = MAD1,
        language: Literal["es", "en"] = "es",
    ) -> None:
        """
        Represents a Mercadona warehouse, from where their catalog can browsed.
        A postcode that isn't a Mercadona warehouse will be treated as a city postcode, and will find the closes warehouse to the population if any.

        Args:
            warehouse (str): The target warehouse to retrieve products from. It can also be a city postcode which Mercadona can deliver too. Defaults to "mad1", in Madrid. More warehouses are available in constants.WAREHOUSES.
            language (str): The language of the information recieved. Defaults to "es": Spanish. Can also be "en": English.

        Raises:
            ValueError: Raises when a postcode is not in Mercadona's network.
        """
        self.language = language
        self.warehouse = warehouse

        # If the warehouse code is not in the list of warehouses, it means that it
        # is most probably a postcode.
        if self.warehouse not in WAREHOUSES:
            # Get closest warehouse to the postcode
            self.warehouse = get_warehouse_code(self.warehouse)

            # Raise error if the postcode isn't in Mercadona's network
            if self.warehouse is None:
                raise ValueError(
                    "The postcode specified isn't available in Mercadona's network... Try using any of the warehouse codes in constants.WAREHOUSES."
                )

    def search(self, query: str) -> list[Product]:
        """
        Queries Mercadona's products using their provider "Algolia".

        Args:
            query (str): Search query (e.g. Dish Soap).
            lang (str): Language code. Defaults to spanish. Can be "en" too.

        Rerturns:
            list[Product]: List of products related to the search.
        """
        response = query_algolia(query, self.warehouse, self.language)
        hits = response.get("hits", [])

        products = []
        for h in hits:
            product = Product(h["id"], self.warehouse, self.language)

            if product.exists():
                products.append(product)

        return products

    def get_home_recommendations(self) -> dict:
        """
        Retrieves product recommendations for the home page grouped by sections.

        Returns:
            dict: Dictionary where keys are layout names and values are lists of recommended products. The lists of products can also include banners which often are Season objects.
        """
        url = urljoin(API_URL, f"/api/home/")
        response = fetch_json(url, {"lang": self.language, "wh": self.warehouse})

        sections = response.get("sections", [])

        # Dictionary to store products grouped by sections
        section_products = {}

        for section in sections:
            section_name = section.get("layout")

            items = section.get("content", {}).get("items", [])

            for item in items:
                if item.get("bg_colors", None):
                    parsed_item = Season(item["id"], self.warehouse, self.language)
                else:
                    parsed_item = Product(item, self.warehouse, self.language)

                if parsed_item.exists():
                    if section_products.get(section_name, None):
                        section_products[section_name].append(parsed_item)
                    else:
                        section_products[section_name] = [parsed_item]

        return section_products

    def get_new_arrivals(self) -> list[Product]:
        """
        New product arrivals at Mercadona

        Args:
            lang (str): Language code. Defaults to spanish. Can be "en" too.

        Returns:
            list[Product]: List of new product arrivals.
        """
        url = urljoin(API_URL, f"/api/home/new-arrivals/")
        response = fetch_json(url, {"lang": self.language, "wh": self.warehouse})

        products = []
        for item in response.get("items", []):
            product = Product(item)
            if product.exists():
                products.append(product)

        return products
