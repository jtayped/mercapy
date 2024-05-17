import requests


def fetch_json(url: str, params: dict = None) -> dict:
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        if response.ok:
            return response.json()

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching data from {url}: {e}")
