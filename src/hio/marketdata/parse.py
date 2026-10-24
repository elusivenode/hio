"""Synthetic receipt format and schema validation (quality gate 1, observations standard §6).

Format (CSV, UTF-8):
    line 1:  a '#' comment containing SYNTHETIC
    header:  series_id,valid_time,value[,published_at][,vintage_from][,archived_at]
    rows:    valid_time is a market-local ISO date; value a decimal; the optional columns are
             UTC instants with a Z suffix and are the only vintage-specific evidence a row can
             carry (OBS-INV-006).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from hio.contracts.observation import parse_instant

REQUIRED = ("series_id", "valid_time", "value")
OPTIONAL = ("published_at", "vintage_from", "archived_at")


class MalformedReceipt(ValueError):
    pass


@dataclass(frozen=True)
class RawRow:
    series_id: str
    valid_time: date
    value: Decimal
    published_at: datetime | None = None
    vintage_from: datetime | None = None
    archived_at: datetime | None = None


def parse_receipt(data: bytes) -> list[RawRow]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MalformedReceipt("not UTF-8") from exc
    lines = text.splitlines()
    if not lines or not lines[0].startswith("#") or "SYNTHETIC" not in lines[0]:
        raise MalformedReceipt("line 1 must be a '#' comment declaring SYNTHETIC")
    reader = csv.DictReader(io.StringIO("\n".join(lines[1:])))
    header = tuple(reader.fieldnames or ())
    if header[:3] != REQUIRED or any(h not in OPTIONAL for h in header[3:]):
        raise MalformedReceipt(f"unexpected header: {header}")
    rows, seen = [], set()
    for n, rec in enumerate(reader, start=3):
        try:
            if None in rec or any(v is None for v in rec.values()):
                raise MalformedReceipt("wrong number of fields")
            valid_time = date.fromisoformat(rec["valid_time"])  # a calendar date, never an instant
            if len(rec["valid_time"]) != 10:
                raise MalformedReceipt("valid_time must be YYYY-MM-DD")
            value = Decimal(rec["value"])
            if not value.is_finite():
                raise MalformedReceipt("value must be finite")
            opt = {k: parse_instant(rec[k]) if rec.get(k) else None for k in OPTIONAL}
        except (ValueError, InvalidOperation) as exc:
            raise MalformedReceipt(f"line {n}: {exc}") from exc
        if not rec["series_id"]:
            raise MalformedReceipt(f"line {n}: empty series_id")
        # One row per key, except that a vintage archive may list several vintages of a key,
        # each with its own evidence instant.
        key = (rec["series_id"], valid_time, opt["published_at"], opt["vintage_from"], opt["archived_at"])
        if key in seen:
            raise MalformedReceipt(f"line {n}: duplicate key {key}")
        seen.add(key)
        rows.append(RawRow(rec["series_id"], valid_time, value, **opt))
    return rows  # a well-formed receipt with no rows is valid: nothing has been released yet
