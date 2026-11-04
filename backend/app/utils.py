"""Small shared helpers."""
from datetime import date, datetime
from typing import Optional


def escape_like(value: str) -> str:
    """Escape LIKE/ILIKE wildcards so user input is matched literally (use escape='\\\\')."""
    return value.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


def iso(value) -> Optional[str]:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
