from typing import Literal
from urllib.parse import urljoin

from .constants import WAREHOUSES
from .utils.warehouses import get_warehouse_code
from .utils.api import *
from .elements import Product, Season, Category


class Mercadona:

    def __init__(
        self,
        postcode: str,
        language: Literal["es", "en"] = "es",
    ) -> None:
        """
        Represents a Mercadona warehouse, from where their catalog can browsed.
        A postcode that isn't a Mercadona warehouse will be treated as a city postcode, and will find the closes warehouse to the population if any.

        Args:
            postcode (str): The postcode from where products are being accessed. From there, the closest warehouse will be found. Warehouse codes are accepted too (e.g. "mad1", "vlc1", etc.)
            language (str): The language of the information recieved. Defaults to "es": Spanish. Can also be "en": English.
        """
        self.language = language

        if postcode in WAREHOUSES:
            self.postcode = postcode
            self.warehouse = self.postcode
        else:
            self.postcode = postcode
            self.warehouse = get_warehouse_code(self.postcode)

    def _get_with_context(self, url: str):
        return fetch_json(url, {"lang": self.language, "wh": self.warehouse})

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
            products.append(product)

        return products

    def get_home_recommendations(self) -> dict:
        """
        Retrieves product recommendations for the home page grouped by sections.

        Returns:
            dict: Dictionary where keys are layout names and values are lists of recommended products. The lists of products can also include banners which often are Season objects.
        """
        url = urljoin(API_URL, f"/api/home/")
        response = self._get_with_context(url)

        sections = response.get("sections", [])

        # Dictionary to store products grouped by sections
        section_products = {}

        for section in sections:
            section_name = section.get("layout")

            items = section.get("content", {}).get("items", [])

            for item in items:
                if item.get("bg_colors", None):
                    parsed_item = Season(str(item["id"]), self.warehouse, self.language)
                else:
                    parsed_item = Product(item, self.warehouse, self.language)

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
        response = self._get_with_context(url)

        products = []
        for item in response.get("items", []):
            product = Product(item, self.warehouse, self.language)
            products.append(product)

        return products

    def get_categories(self) -> list[Category]:
        url = urljoin(API_URL, "/api/categories/")
        response = self._get_with_context(url)

        # Get all level 1 categories
        lvl1_categories = []

        results = response.get("results", [])
        for result in results:
            categories = result.get("categories", [])
            for c in categories:
                category = Category(c, self.warehouse, self.language)
                lvl1_categories.append(category)

        return lvl1_categories

    def get_catalog(self) -> list[Product]:
        return [p for c in self.get_categories() for p in c.products]
