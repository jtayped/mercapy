class ProductNotFound(Exception):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"Couldn't find product with ID: {product_id}")


class ErrorFetchingProduct(Exception):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"There has been an error fetching the product with ID: {product_id}")
