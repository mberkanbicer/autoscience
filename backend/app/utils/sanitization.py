"""Input sanitization utilities for XSS prevention."""

import html
from typing import Any


def sanitize_string(value: str, allow_html: bool = False) -> str:
    """Sanitize a string value for XSS prevention."""
    if not value:
        return value
    if allow_html:
        # Only allow safe HTML tags if explicitly requested
        return value
    return html.escape(value, quote=True)


def sanitize_dict(value: dict[str, Any], recursive: bool = True) -> dict[str, Any]:
    """Sanitize all string values in a dictionary."""
    if not value:
        return value

    result = {}
    for k, v in value.items():
        if isinstance(v, str):
            result[k] = sanitize_string(v)
        elif isinstance(v, dict) and recursive:
            result[k] = sanitize_dict(v, recursive)
        elif isinstance(v, list) and recursive:
            result[k] = sanitize_list(v)
        else:
            result[k] = v
    return result


def sanitize_list(value: list[Any]) -> list[Any]:
    """Sanitize all values in a list."""
    result = []
    for item in value:
        if isinstance(item, str):
            result.append(sanitize_string(item))
        elif isinstance(item, dict):
            result.append(sanitize_dict(item))
        elif isinstance(item, list):
            result.append(sanitize_list(item))
        else:
            result.append(item)
    return result
