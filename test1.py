import requests
import json


def query_algolia(query):
    url = "https://7uzjkl1dj0-dsn.algolia.net/1/indexes/products_prod_4115_es/query"

    # Headers required for the request
    headers = {
        "x-algolia-application-id": "7UZJKL1DJ0",
        "x-algolia-api-key": "9d8f2e39e90df472b4f2e559a116fe17",
        "Content-Type": "application/json",
    }

    # Data payload for the request
    payload = {
        "params": f'query={query}'
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Check if the request was successful
        if response.status_code == 200:
            print("Request was successful!")
            return response.json()
        else:
            print(f"Request failed with status code: {response.status_code}")
            print("Response:", response.text)
            return None

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None


if __name__ == "__main__":
    query = "knebep"  # Example query
    result = query_algolia(query)
    if result:
        print("Result:", json.dumps(result, indent=4))
