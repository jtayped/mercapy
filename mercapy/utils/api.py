from ..constants import *
import requests, json


def fetch_json(url: str, params: dict = None) -> dict:
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        if response.ok:
            return response.json()

    except requests.exceptions.RequestException as e:
        return {}


def query_algolia(query: str, lang: str = "es") -> dict:
    url = (
        f"https://7uzjkl1dj0-dsn.algolia.net/1/indexes/products_prod_4115_{lang}/query"
    )

    # Headers required for the request
    headers = {
        "x-algolia-application-id": ALGOLIA_APP_ID,
        "x-algolia-api-key": ALGOLIA_API_KEY,
        "Content-Type": "application/json",
    }

    # Data payload for the request
    payload = {"params": f"query={query}"}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        # Check if the request was successful
        if response.ok:
            return response.json()

    except requests.exceptions.RequestException as e:
        return {}
