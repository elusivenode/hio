"""Canonical byte renderings and content hashes (releases standard §1–§2).

JSON: UTF-8, sorted keys, no insignificant whitespace. Decimals are rendered as strings in
plain notation, so a value's bytes never depend on float formatting.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decimal_str(value: Decimal) -> str:
    """Plain-notation rendering with no exponent and no trailing zeros (0 renders as "0")."""
    if not value.is_finite():
        raise ValueError(f"non-finite decimal: {value}")
    text = format(value.normalize(), "f")
    return "0" if text in {"-0", "0"} else text


def _default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return decimal_str(obj)
    if isinstance(obj, datetime):
        return instant_str(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"not canonically serialisable: {type(obj).__name__}")


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False, default=_default
    ).encode("utf-8")


def instant_str(value: datetime) -> str:
    """A UTC instant as ISO 8601 with a Z suffix. Naive datetimes are refused."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("instants must be timezone-aware")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
