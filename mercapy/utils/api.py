import requests, json
from ..constants import *


def fetch_json(url: str, params: dict = None) -> dict:
    """
    Fetches JSON data from a given URL.

    Args:
        url (str): The URL to fetch data from.
        params (dict, optional): The parameters to send with the request. Defaults to None.

    Returns:
        dict: The JSON response as a dictionary, or an empty dictionary if there's an error.
    """
    try:
        response = requests.get(url, params=params, allow_redirects=False)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        return {"err_code": response.status_code, "err_message": e}


def query_algolia(query: str, warehouse: str = MAD1, lang: str = "es") -> dict | None:
    """
    Queries Algolia for product data.

    Args:
        query (str): The query string.
        lang (str, optional): The language for the query. Defaults to "es".

    Returns:
        dict or None: The JSON response as a dictionary, or None if there's an error.
    """
    url = f"https://7uzjkl1dj0-dsn.algolia.net/1/indexes/products_prod_{warehouse}_{lang}/query"

    # Headers required for the request
    headers = {
        "x-algolia-application-id": ALGOLIA_APP_ID,
        "x-algolia-api-key": ALGOLIA_API_KEY,
        "Content-Type": "application/json",
    }

    # Data payload for the request
    payload = {"params": f"query={query}"}

    try:
        with requests.post(url, headers=headers, data=json.dumps(payload)) as response:
            response.raise_for_status()

            # Check if the request was successful
            if response.ok:
                return response.json()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return None
