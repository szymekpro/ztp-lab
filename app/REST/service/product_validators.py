# service/product_validators.py
from app.REST.data.product_repository import get_product_by_name
from app.REST.data.category_repository import get_category_by_id
from app.REST.data.forbidden_product_name_repository import get_forbidden_product_phrases


class ValidationError(Exception):
    pass


class ConflictError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


def validate_product_name_length(name: str):
    if not (3 <= len(name) <= 20):
        raise ValidationError("Nazwa produktu musi mieć od 3 do 20 znaków.")


def validate_product_name_alphanumeric(name: str):
    if not name.isalnum():
        raise ValidationError("Nazwa produktu może zawierać wyłącznie litery i cyfry.")


def validate_product_name_unique(db, name: str, current_product_id=None):
    existing = get_product_by_name(db, name)
    if existing:
        if current_product_id is None or existing.id != current_product_id:
            raise ConflictError("Produkt o tej nazwie już istnieje.")


def validate_category_exists(db, category_id: int):
    category = get_category_by_id(db, category_id)
    if category is None:
        raise ResourceNotFoundError("Kategoria nie istnieje.")
    return category


def validate_price_range(category, price: float):
    if price < category.min_price or price > category.max_price:
        raise ValidationError(
            f"Cena musi mieścić się w przedziale "
            f"{category.min_price}–{category.max_price} dla tej kategorii."
        )


def validate_quantity_non_negative(quantity: int):
    if quantity < 0:
        raise ValidationError("Ilość dostępnych sztuk nie może być ujemna.")


def validate_product_name_forbidden_phrases(db, name: str):
    phrases = get_forbidden_product_phrases(db)
    name_lower = name.lower()
    for phrase in phrases:
        if phrase.lower() in name_lower:
            raise ValidationError("Nazwa produktu zawiera zakazaną frazę.")
