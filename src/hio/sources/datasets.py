"""The five S1b-1 datasets: source id, series, and a payload parser per dataset (T-0009 §1).

Each parser validates the payload's schema, fail closed, so a malformed or restructured payload
becomes a failed run, never a receipt. The label date in a payload is taken as `valid_time`
exactly as the publisher labels it; no timing or publication meaning is assigned here (P3).

**Payload layouts are ASSUMED**, from the publishers' documented structure and the 2026-10-25
evidence note (T-0002), not from a retained sample. The fixtures mirror those assumptions and the
first authorised structure check must confirm them. A mismatch fails closed.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from hio.marketdata.parse import RawRow


class MalformedPayload(ValueError):
    """error_class `parse` (cannot be read) or `schema` (readable but not the expected layout)."""

    def __init__(self, error_class: str, message: str) -> None:
        super().__init__(message)
        self.error_class = error_class


@dataclass(frozen=True)
class Flag:
    """An expert-judgement day: the AONIA rate was set by fallback type A, B or C."""

    valid_time: date
    kind: str


@dataclass(frozen=True)
class Parsed:
    rows: tuple[RawRow, ...] = ()
    flags: tuple[Flag, ...] = ()


@dataclass(frozen=True)
class DatasetSpec:
    source_id: str
    parse: Callable[[bytes], Parsed]
    url: str | None = None  # configured per environment and approved with the rights (T-0009 §8)


def _text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MalformedPayload("parse", "not UTF-8") from exc


_MONTHS = {
    m: i
    for i, m in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), start=1
    )
}


def _date(s: str) -> date:
    """A calendar-date label as text (dd-Mon-yyyy or yyyy-mm-dd); never an instant."""
    s = s.strip()
    try:
        if len(s) == 10 and s[4] == "-":
            return date.fromisoformat(s)
        day, mon, year = s.split("-")
        return date(int(year), _MONTHS[mon.lower()], int(day))
    except (ValueError, KeyError) as exc:
        raise MalformedPayload("parse", f"not a date: {s!r}") from exc


def _dec(s: str) -> Decimal:
    try:
        v = Decimal(s.strip())
    except InvalidOperation as exc:
        raise MalformedPayload("parse", f"not a number: {s!r}") from exc
    if not v.is_finite():
        raise MalformedPayload("parse", f"not finite: {s!r}")
    return v


def parse_rba_f1(wanted: Mapping[str, str]) -> Callable[[bytes], Parsed]:
    """RBA F1 CSV: a 'Series ID' row names each column; data rows start with a dd-Mon-yyyy date.
    `wanted` maps RBA series ids to HIO series ids. Empty cells are not yet published and skipped."""

    def parse(data: bytes) -> Parsed:
        rows = list(csv.reader(io.StringIO(_text(data))))
        header_at = next((i for i, r in enumerate(rows) if r and r[0].strip().lower() == "series id"), None)
        if header_at is None:
            raise MalformedPayload("schema", "no 'Series ID' row")
        columns = {c.strip(): i for i, c in enumerate(rows[header_at]) if c.strip()}
        missing = sorted(set(wanted) - set(columns))
        if missing:
            raise MalformedPayload("schema", f"series missing: {missing}")
        out: list[RawRow] = []
        seen: set[tuple[str, date]] = set()
        for r in rows[header_at + 1 :]:
            if not r or not r[0].strip():
                continue
            day = _date(r[0])
            for rba_id, our_id in wanted.items():
                cell = r[columns[rba_id]] if columns[rba_id] < len(r) else ""
                if not cell.strip():
                    continue
                if (our_id, day) in seen:
                    raise MalformedPayload("parse", f"duplicate {our_id} {day}")
                seen.add((our_id, day))
                out.append(RawRow(our_id, day, _dec(cell)))
        if not out:
            raise MalformedPayload("schema", "no data rows")
        return Parsed(rows=tuple(out))

    return parse


def parse_rba_expert_judgement(data: bytes) -> Parsed:
    """RBA expert-judgement CSV: a header with a date column and a type column (A, B or C)."""
    rows = list(csv.reader(io.StringIO(_text(data))))
    for i, r in enumerate(rows):
        lowered = [c.strip().lower() for c in r]
        d = next((j for j, c in enumerate(lowered) if "date" in c), None)
        t = next((j for j, c in enumerate(lowered) if "type" in c), None)
        if d is not None and t is not None:
            flags = []
            for rr in rows[i + 1 :]:
                if not rr or not any(c.strip() for c in rr):
                    continue
                kind = rr[t].strip().upper()
                if kind not in {"A", "B", "C"}:
                    raise MalformedPayload("schema", f"unknown fallback type {kind!r}")
                flags.append(Flag(_date(rr[d]), kind))
            return Parsed(flags=tuple(flags))
    raise MalformedPayload("schema", "no header with a date column and a type column")


def parse_nyfed(rate_type: str, field: str, series_id: str) -> Callable[[bytes], Parsed]:
    """NY Fed Markets API JSON: {"refRates": [{"effectiveDate", "type", <field>, ...}]}.
    The revisionIndicator stays in the raw receipt; no meaning is assigned to it here."""

    def parse(data: bytes) -> Parsed:
        try:
            doc = json.loads(_text(data), parse_float=Decimal)
        except json.JSONDecodeError as exc:
            raise MalformedPayload("parse", "not JSON") from exc
        refs = doc.get("refRates") if isinstance(doc, dict) else None
        if not isinstance(refs, list) or not refs:
            raise MalformedPayload("schema", "no refRates list")
        out, seen = [], set()
        for ref in refs:
            if not isinstance(ref, dict) or ref.get("type") != rate_type:
                raise MalformedPayload("schema", f"entry is not type {rate_type}")
            if field not in ref or "effectiveDate" not in ref:
                raise MalformedPayload("schema", f"entry lacks effectiveDate or {field}")
            raw = ref[field]
            if not isinstance(raw, Decimal):
                raise MalformedPayload("schema", f"{field} is not a number")
            day = _date(str(ref["effectiveDate"]))
            if day in seen:
                raise MalformedPayload("parse", f"duplicate {series_id} {day}")
            seen.add(day)
            out.append(RawRow(series_id, day, raw))
        return Parsed(rows=tuple(out))

    return parse


AONIA = "rba.cash_rate.aonia"
TRI = "rba.cash_rate.tri"
SOFR = "nyfed.sofr"
SOFR_INDEX = "nyfed.sofr_index"

DATASETS: Mapping[str, DatasetSpec] = {
    "rba.cash_rate": DatasetSpec("rba.cash_rate", parse_rba_f1({"FIRMMCRID": AONIA})),
    "rba.expert_judgement": DatasetSpec("rba.expert_judgement", parse_rba_expert_judgement),
    "rba.cash_rate_tri": DatasetSpec("rba.cash_rate_tri", parse_rba_f1({"FIRMMCTRI": TRI})),
    "nyfed.sofr": DatasetSpec("nyfed.sofr", parse_nyfed("SOFR", "percentRate", SOFR)),
    "nyfed.sofr_index": DatasetSpec("nyfed.sofr_index", parse_nyfed("SOFRAI", "index", SOFR_INDEX)),
}
