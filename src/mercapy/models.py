"""Immutable values returned by :class:`mercapy.Mercadona`."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import PurePosixPath
from typing import TypeAlias
from urllib.parse import urlencode, urlparse

from ._constants import IMAGE_URL
from .exceptions import InvalidResponseError

JsonObject: TypeAlias = dict[str, object]


class Language(StrEnum):
    """Languages supported by Mercadona's storefront."""

    SPANISH = "es"
    ENGLISH = "en"


class PhotoFit(StrEnum):
    """Imgix resize modes supported by :meth:`Photo.url`."""

    CROP = "crop"
    FIT = "fit"


@dataclass(frozen=True, slots=True)
class Price:
    unit: Decimal | None = None
    bulk: Decimal | None = None
    previous: Decimal | None = None
    reference: Decimal | None = None
    tax_percentage: Decimal | None = None
    unit_size: Decimal | None = None
    pack_size: Decimal | None = None
    total_units: Decimal | None = None
    drained_weight: Decimal | None = None
    minimum_amount: Decimal | None = None
    increment_amount: Decimal | None = None
    unit_name: str | None = None
    size_format: str | None = None
    reference_format: str | None = None
    is_discounted: bool = False
    is_new: bool = False
    is_pack: bool = False
    approximate_size: bool = False


@dataclass(frozen=True, slots=True)
class Availability:
    published: bool | None = None
    status: str | None = None
    limit: Decimal | None = None
    unavailable_from: str | None = None
    unavailable_weekdays: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class Photo:
    """A product image identified independently of its requested size."""

    file_name: str
    perspective: int | None = None

    def __post_init__(self) -> None:
        parsed = urlparse(self.file_name)
        file_name = PurePosixPath(parsed.path).name if parsed.scheme else self.file_name
        if not file_name or "/" in file_name or "\\" in file_name:
            raise ValueError("photo file_name must identify one image file")
        object.__setattr__(self, "file_name", file_name)

    def url(
        self,
        *,
        width: int | None = None,
        height: int | None = None,
        fit: PhotoFit | str = PhotoFit.CROP,
    ) -> str:
        """Build an image URL without performing I/O."""

        try:
            fit_value = PhotoFit(fit).value
        except ValueError as error:
            raise ValueError("fit must be 'crop' or 'fit'") from error
        if width is not None and width <= 0:
            raise ValueError("width must be greater than zero")
        if height is not None and height <= 0:
            raise ValueError("height must be greater than zero")

        base = f"{IMAGE_URL}/{self.file_name}"
        if width is None and height is None:
            return base
        parameters: list[tuple[str, str | int]] = [("fit", fit_value)]
        if height is not None:
            parameters.append(("h", height))
        if width is not None:
            parameters.append(("w", width))
        return f"{base}?{urlencode(parameters)}"


@dataclass(frozen=True, slots=True)
class ProductDetails:
    legal_name: str | None = None
    description: str | None = None
    origin: str | None = None
    suppliers: tuple[str, ...] = ()
    counter_info: str | None = None
    danger_mentions: str | None = None
    mandatory_mentions: str | None = None
    production_variant: str | None = None
    usage_instructions: str | None = None
    storage_instructions: str | None = None
    alcohol_by_volume: Decimal | None = None
    prepared_by_mercadona: bool | None = None


@dataclass(frozen=True, slots=True)
class Nutrition:
    allergens: str | None = None
    ingredients: str | None = None


@dataclass(frozen=True, slots=True)
class Category:
    id: str
    name: str
    order: int | None = None
    level: int | None = None
    layout: int | None = None
    published: bool | None = None
    is_extended: bool | None = None
    image_url: str | None = None
    subtitle: str | None = None
    children: tuple[Category, ...] = ()
    products: tuple[ProductSummary, ...] = ()


@dataclass(frozen=True, slots=True)
class ProductSummary:
    id: str
    name: str
    slug: str | None = None
    brand: str | None = None
    packaging: str | None = None
    main_feature: str | None = None
    share_url: str | None = None
    thumbnail: Photo | None = None
    price: Price = Price()
    availability: Availability = Availability()
    categories: tuple[Category, ...] = ()
    requires_age_check: bool = False
    is_water: bool = False
    is_new_arrival: bool = False


@dataclass(frozen=True, slots=True)
class Product:
    id: str
    name: str
    ean: str | None = None
    slug: str | None = None
    brand: str | None = None
    packaging: str | None = None
    main_feature: str | None = None
    share_url: str | None = None
    photos: tuple[Photo, ...] = ()
    price: Price = Price()
    availability: Availability = Availability()
    categories: tuple[Category, ...] = ()
    details: ProductDetails = ProductDetails()
    nutrition: Nutrition = Nutrition()
    requires_age_check: bool = False
    is_water: bool = False
    is_bulk: bool = False
    is_variable_weight: bool = False
    is_new_arrival: bool = False


@dataclass(frozen=True, slots=True)
class SeasonSummary:
    """A seasonal collection advertised by a home-page banner."""

    id: str
    title: str
    banner_id: str | None = None
    campaign_id: str | None = None
    image_url: str | None = None
    text_color: str | None = None
    background_colors: tuple[str, ...] = ()
    button_color: str | None = None


@dataclass(frozen=True, slots=True)
class HomeNotification:
    title: str
    kind: str | None = None
    action: str | None = None
    event_key: str | None = None


HomeItem: TypeAlias = ProductSummary | SeasonSummary | HomeNotification


@dataclass(frozen=True, slots=True)
class HomeSection:
    layout: str
    title: str | None = None
    subtitle: str | None = None
    id: str | None = None
    source: str | None = None
    source_code: str | None = None
    show_more: bool | None = None
    items: tuple[HomeItem, ...] = ()


@dataclass(frozen=True, slots=True)
class Season:
    id: str
    title: str
    layout: str | None = None
    source: str | None = None
    source_code: str | None = None
    products: tuple[ProductSummary, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchResult:
    query: str
    page: int
    page_size: int
    total_hits: int
    total_pages: int
    processing_time_ms: int | None
    products: tuple[ProductSummary, ...]


def _object(value: object) -> JsonObject:
    return value if isinstance(value, dict) else {}


def _items(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _identifier(value: object, label: str) -> str:
    if isinstance(value, bool) or value is None:
        raise InvalidResponseError(f"response has no usable {label}")
    if isinstance(value, (str, int)):
        result = str(value).strip()
        if result:
            return result
    raise InvalidResponseError(f"response has no usable {label}")


def _required_text(value: object, label: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise InvalidResponseError(f"response has no usable {label}")


def _decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if not isinstance(value, (str, int, float, Decimal)):
        return None
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return None


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _boolean(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _price(data: object) -> Price:
    value = _object(data)
    return Price(
        unit=_decimal(value.get("unit_price")),
        bulk=_decimal(value.get("bulk_price")),
        previous=_decimal(value.get("previous_unit_price")),
        reference=_decimal(value.get("reference_price")),
        tax_percentage=_decimal(value.get("tax_percentage")),
        unit_size=_decimal(value.get("unit_size")),
        pack_size=_decimal(value.get("pack_size")),
        total_units=_decimal(value.get("total_units")),
        drained_weight=_decimal(value.get("drained_weight")),
        minimum_amount=_decimal(value.get("min_bunch_amount")),
        increment_amount=_decimal(value.get("increment_bunch_amount")),
        unit_name=_text(value.get("unit_name")),
        size_format=_text(value.get("size_format")),
        reference_format=_text(value.get("reference_format")),
        is_discounted=_boolean(value.get("price_decreased")) or False,
        is_new=_boolean(value.get("is_new")) or False,
        is_pack=_boolean(value.get("is_pack")) or False,
        approximate_size=_boolean(value.get("approx_size")) or False,
    )


def _availability(data: JsonObject) -> Availability:
    weekdays = tuple(
        item
        for item in _items(data.get("unavailable_weekdays"))
        if isinstance(item, int) and not isinstance(item, bool)
    )
    return Availability(
        published=_boolean(data.get("published")),
        status=_text(data.get("status")),
        limit=_decimal(data.get("limit")),
        unavailable_from=_text(data.get("unavailable_from")),
        unavailable_weekdays=weekdays,
    )


def _photo(data: object) -> Photo | None:
    source: str | None
    if isinstance(data, str):
        source = data
        perspective = None
    else:
        value = _object(data)
        source = next(
            (
                url
                for key in ("regular", "zoom", "thumbnail")
                if (url := _text(value.get(key)))
            ),
            None,
        )
        perspective = _integer(value.get("perspective"))
    if source is None:
        return None
    try:
        return Photo(source, perspective=perspective)
    except ValueError:
        return None


def _badges(data: JsonObject) -> tuple[bool, bool]:
    badges = _object(data.get("badges"))
    return (
        _boolean(badges.get("requires_age_check")) or False,
        _boolean(badges.get("is_water")) or False,
    )


def parse_category(data: object) -> Category:
    value = _object(data)
    category_id = _identifier(value.get("id"), "category id")
    name = _required_text(value.get("name"), "category name")
    children = tuple(parse_category(item) for item in _items(value.get("categories")))
    products = tuple(
        parse_product_summary(item) for item in _items(value.get("products"))
    )
    return Category(
        id=category_id,
        name=name,
        order=_integer(value.get("order")),
        level=_integer(value.get("level")),
        layout=_integer(value.get("layout")),
        published=_boolean(value.get("published")),
        is_extended=_boolean(value.get("is_extended")),
        image_url=_text(value.get("image")) or _text(value.get("icon_url")),
        subtitle=_text(value.get("subtitle")),
        children=children,
        products=products,
    )


def parse_product_summary(data: object) -> ProductSummary:
    value = _object(data)
    product_id = _identifier(value.get("id"), "product id")
    name = _required_text(value.get("display_name"), "product name")
    thumbnail = _photo(value.get("thumbnail"))
    categories = tuple(parse_category(item) for item in _items(value.get("categories")))
    requires_age_check, is_water = _badges(value)
    return ProductSummary(
        id=product_id,
        name=name,
        slug=_text(value.get("slug")),
        brand=_text(value.get("brand")),
        packaging=_text(value.get("packaging")),
        main_feature=_text(value.get("main_feature")),
        share_url=_text(value.get("share_url")),
        thumbnail=thumbnail,
        price=_price(value.get("price_instructions")),
        availability=_availability(value),
        categories=categories,
        requires_age_check=requires_age_check,
        is_water=is_water,
        is_new_arrival=_boolean(value.get("is_new_arrival")) or False,
    )


def _details(data: object, product: JsonObject) -> ProductDetails:
    value = _object(data)
    suppliers = tuple(
        name
        for item in _items(value.get("suppliers"))
        if (name := _text(_object(item).get("name"))) is not None
    )
    alcohol = _text(value.get("alcohol_by_volume"))
    if alcohol is not None:
        alcohol = alcohol.strip().removesuffix("º").removesuffix("%")
        alcohol = alcohol.replace(",", ".")
    return ProductDetails(
        legal_name=_text(value.get("legal_name")),
        description=_text(value.get("description")),
        origin=_text(value.get("origin")) or _text(product.get("origin")),
        suppliers=suppliers,
        counter_info=_text(value.get("counter_info")),
        danger_mentions=_text(value.get("danger_mentions")),
        mandatory_mentions=_text(value.get("mandatory_mentions")),
        production_variant=_text(value.get("production_variant")),
        usage_instructions=_text(value.get("usage_instructions")),
        storage_instructions=_text(value.get("storage_instructions")),
        alcohol_by_volume=_decimal(alcohol),
        prepared_by_mercadona=_boolean(value.get("is_prepared_by_mercadona")),
    )


def parse_product(data: object) -> Product:
    value = _object(data)
    product_id = _identifier(value.get("id"), "product id")
    name = _required_text(value.get("display_name"), "product name")
    photos = tuple(
        photo
        for item in _items(value.get("photos"))
        if (photo := _photo(item)) is not None
    )
    categories = tuple(parse_category(item) for item in _items(value.get("categories")))
    nutrition_data = _object(value.get("nutrition_information"))
    requires_age_check, is_water = _badges(value)
    return Product(
        id=product_id,
        name=name,
        ean=_text(value.get("ean")),
        slug=_text(value.get("slug")),
        brand=_text(value.get("brand")),
        packaging=_text(value.get("packaging")),
        main_feature=_text(value.get("main_feature")),
        share_url=_text(value.get("share_url")),
        photos=photos,
        price=_price(value.get("price_instructions")),
        availability=_availability(value),
        categories=categories,
        details=_details(value.get("details"), value),
        nutrition=Nutrition(
            allergens=_text(nutrition_data.get("allergens")),
            ingredients=_text(nutrition_data.get("ingredients")),
        ),
        requires_age_check=requires_age_check,
        is_water=is_water,
        is_bulk=_boolean(value.get("is_bulk")) or False,
        is_variable_weight=_boolean(value.get("is_variable_weight")) or False,
        is_new_arrival=_boolean(value.get("is_new_arrival")) or False,
    )


def _season_summary(data: object) -> SeasonSummary:
    value = _object(data)
    api_path = _required_text(value.get("api_path"), "season API path")
    path_parts = PurePosixPath(urlparse(api_path).path).parts
    if not path_parts:
        raise InvalidResponseError("response has no usable season id")
    season_id = path_parts[-1]
    return SeasonSummary(
        id=_identifier(season_id, "season id"),
        title=_required_text(value.get("title"), "season title"),
        banner_id=(
            _identifier(value.get("id"), "season banner id")
            if value.get("id") is not None
            else None
        ),
        campaign_id=_text(value.get("campaign_id")),
        image_url=_text(value.get("image_url")),
        text_color=_text(value.get("text_color")),
        background_colors=tuple(
            color
            for item in _items(value.get("bg_colors"))
            if (color := _text(item)) is not None
        ),
        button_color=_text(value.get("button_color")),
    )


def parse_home_section(data: object) -> HomeSection:
    value = _object(data)
    layout = _required_text(value.get("layout"), "home section layout")
    content = _object(value.get("content"))
    parsed_items: list[HomeItem] = []
    if layout == "notification" and content:
        parsed_items.append(
            HomeNotification(
                title=_required_text(content.get("title"), "notification title"),
                kind=_text(content.get("type")),
                action=_text(content.get("action")),
                event_key=_text(content.get("event_key")),
            )
        )
    else:
        for item in _items(content.get("items")):
            item_value = _object(item)
            if item_value.get("api_path") is not None:
                parsed_items.append(_season_summary(item_value))
            elif item_value.get("id") is not None:
                parsed_items.append(parse_product_summary(item_value))
    return HomeSection(
        layout=layout,
        title=_text(content.get("title")),
        subtitle=_text(content.get("subtitle")),
        id=_text(content.get("uuid")),
        source=_text(content.get("source")),
        source_code=_text(content.get("source_code")),
        show_more=_boolean(content.get("show_more")),
        items=tuple(parsed_items),
    )


def parse_season(data: object, requested_id: str) -> Season:
    value = _object(data)
    title = _required_text(value.get("title"), "season title")
    products = tuple(parse_product_summary(item) for item in _items(value.get("items")))
    return Season(
        id=_text(value.get("uuid")) or requested_id,
        title=title,
        layout=_text(value.get("layout")),
        source=_text(value.get("source")),
        source_code=_text(value.get("source_code")),
        products=products,
    )


def parse_search_result(
    data: object, *, query: str, requested_page: int, requested_page_size: int
) -> SearchResult:
    value = _object(data)
    hits = value.get("hits")
    if not isinstance(hits, list):
        raise InvalidResponseError("search response has no hits array")
    page = _integer(value.get("page"))
    page_size = _integer(value.get("hitsPerPage"))
    total_hits = _integer(value.get("nbHits"))
    total_pages = _integer(value.get("nbPages"))
    return SearchResult(
        query=query,
        page=requested_page if page is None else page,
        page_size=requested_page_size if page_size is None else page_size,
        total_hits=len(hits) if total_hits is None else total_hits,
        total_pages=0 if total_pages is None else total_pages,
        processing_time_ms=_integer(value.get("processingTimeMS")),
        products=tuple(parse_product_summary(item) for item in hits),
    )
