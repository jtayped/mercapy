from __future__ import annotations

from decimal import Decimal

import pytest

import mercapy
from mercapy import Photo, PhotoFit
from mercapy.exceptions import InvalidResponseError
from mercapy.models import parse_category, parse_product, parse_product_summary


def test_photo_url_generation_is_pure_and_validated() -> None:
    photo = Photo("https://example.test/path/image name.jpg?old=query")
    assert photo.file_name == "image name.jpg"
    assert photo.url() == ("https://prod-mercadona.imgix.net/images/image name.jpg")
    assert photo.url(width=640) == (
        "https://prod-mercadona.imgix.net/images/image name.jpg?fit=crop&w=640"
    )
    assert photo.url(height=480, fit=PhotoFit.FIT) == (
        "https://prod-mercadona.imgix.net/images/image name.jpg?fit=fit&h=480"
    )
    assert photo.url(width=640, height=480) == (
        "https://prod-mercadona.imgix.net/images/image name.jpg?fit=crop&h=480&w=640"
    )
    for kwargs in ({"width": 0}, {"height": -1}, {"fit": "stretch"}):
        with pytest.raises(ValueError):
            photo.url(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["", "folder/image.jpg", "folder\\image.jpg"])
def test_photo_rejects_invalid_file_names(value: str) -> None:
    with pytest.raises(ValueError):
        Photo(value)


def test_optional_malformed_values_are_ignored() -> None:
    product = parse_product_summary(
        {
            "id": 7,
            "display_name": "Test",
            "limit": {},
            "published": "yes",
            "unavailable_weekdays": [1, True, "2"],
            "price_instructions": {
                "unit_price": " 1.200 ",
                "unit_size": [],
                "price_decreased": "yes",
            },
            "thumbnail": {"bad": "shape"},
            "badges": "bad",
            "categories": "bad",
        }
    )
    assert product.id == "7"
    assert product.price.unit == Decimal("1.200")
    assert product.price.unit_size is None
    assert not product.price.is_discounted
    assert product.availability.unavailable_weekdays == (1,)
    assert product.thumbnail is None


def test_selling_method_marks_products_sold_by_weight() -> None:
    # live shape of a loose fish counter product with no unit size: upstream
    # reports 99 times the price per kilo as the unit price, kept as supplied.
    shrimp = parse_product_summary(
        {
            "id": "24147",
            "display_name": "Gamba argentina congelada",
            "price_instructions": {
                "unit_size": None,
                "bulk_price": "12.95",
                "unit_price": "1282.05",
                "size_format": "kg",
                "selling_method": 1,
                "min_bunch_amount": 0.15,
                "increment_bunch_amount": 0.15,
            },
        }
    )
    assert shrimp.price.sold_by_weight
    assert shrimp.price.unit == Decimal("1282.05")
    assert shrimp.price.minimum_amount == Decimal("0.15")

    for selling_method in (0, None, True, "1"):
        product = parse_product_summary(
            {
                "id": "1",
                "display_name": "Llet",
                "price_instructions": {"selling_method": selling_method},
            }
        )
        assert not product.price.sold_by_weight


@pytest.mark.parametrize(
    ("parser", "payload"),
    [
        (parse_product_summary, {}),
        (parse_product, {"id": True, "display_name": "Bad"}),
        (parse_category, {"id": 1, "name": ""}),
    ],
)
def test_core_identity_is_required(parser: object, payload: object) -> None:
    with pytest.raises(InvalidResponseError):
        parser(payload)  # type: ignore[operator]


def test_public_api_is_deliberate_and_versioned() -> None:
    assert mercapy.__version__ == "2.4.0"
    assert "Mercadona" in mercapy.__all__
    assert "CatalogResult" in mercapy.__all__
    assert "discover_warehouses" in mercapy.__all__
    assert "parse_product" not in mercapy.__all__
    assert "WAREHOUSES" not in mercapy.__all__
