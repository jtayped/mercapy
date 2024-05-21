from mercapy import Mercadona, WAREHOUSES
import json


def save_catalog(products: list[dict], wh: str):
    with open(f"catalogs/{wh}_catalog.json", "w") as file:
        json.dump(products, file, indent=4)


for warehouse in WAREHOUSES[8:]:
    print(f"STARTING Warehouse {warehouse}...")
    m = Mercadona(warehouse, language="en")
    categories = m.get_categories()

    catalog = []
    for category in categories:
        products = category.products
        catalog.extend([p.__dict__() for p in products])

        print(f"Found {len(products)} in {category}.")

    print(f"FOUND {len(catalog)} products in {warehouse}!\n")
    save_catalog(catalog, warehouse)
