import re

NEWS_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PAGE_KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class IdentifierValidationError(ValueError):
    pass


def validate_news_slug(value: str) -> str:
    return _validate_identifier(value, NEWS_SLUG_PATTERN, max_length=160, label="news slug")


def validate_page_key(value: str) -> str:
    return _validate_identifier(value, PAGE_KEY_PATTERN, max_length=80, label="page key")


def _validate_identifier(value: str, pattern: re.Pattern[str], max_length: int, label: str) -> str:
    if not 1 <= len(value) <= max_length or pattern.fullmatch(value) is None:
        raise IdentifierValidationError(f"Invalid {label}")
    return value
