import requests


def get_warehouse_code(postal_code):
    """
    Get warehouse code for a given postal code.

    Args:
        postal_code (str): The postal code to query.

    Returns:
        str or None: Warehouse code if found, None otherwise.
    """
    url = "https://tienda.mercadona.es/api/postal-codes/actions/change-pc/"
    payload = {"new_postal_code": postal_code}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.headers.get("X-Customer-Wh")
    except Exception as e:
        print(f"Error for postal code {postal_code}: {e}")
    return None
