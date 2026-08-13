"""Human and JSON output helpers for Whitfield CLI commands."""

import json
import sys
from typing import Any


def emit(value: Any, as_json: bool) -> None:
    """Write data as strict JSON or compact readable terminal text.

    Args:
        value: JSON-compatible API response value.
        as_json: Whether stdout must contain JSON only.
    """
    if as_json:
        print(json.dumps(value, indent=2, default=str))
        return
    if isinstance(value, list):
        for item in value:
            print(_format_item(item))
        if not value:
            print("No records found.")
        return
    print(_format_item(value))


def error(message: str) -> None:
    """Write a safe CLI error to stderr.

    Args:
        message: User-facing error text.
    """
    print(message, file=sys.stderr)


def _format_item(value: Any) -> str:
    """Convert a simple API object to readable key-value terminal text.

    Args:
        value: Response object or primitive.

    Returns:
        str: Compact human-readable output.
    """
    if not isinstance(value, dict):
        return str(value)
    return "\n".join(f"{key.replace('_', ' ').title()}: {_format_value(item)}" for key, item in value.items())


def _format_value(value: Any) -> str:
    """Render nested JSON values without terminal-specific dependencies.

    Args:
        value: JSON-compatible value.

    Returns:
        str: Readable scalar or compact JSON text.
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)
