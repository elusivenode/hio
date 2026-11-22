"""The monthly panel calculation (gold marts contract §5; proposed, OD-0233).

Pure: exact `Decimal` arithmetic in `hio.contracts.gold.CTX`, every result written through
`decimal_text`, no float and no file access. Section numbers are the contract's.

This is today's alignment and month convention (`hio.portfolio.fixed_allocation`) done in exact
decimals, with one difference by design: an `excess` member's asset and cash legs are each
compounded over the month and then differenced; daily excess is never compounded.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from itertools import pairwise
from typing import Any

from hio.contracts.gold import CTX, TABLES, FactorSeries, decimal_text

_LEGS: dict[str, tuple[str, ...]] = {
    "total_return": ("total_return",),
    "excess": ("asset_return", "cash_return"),
}
_ONE = Decimal(1)

Rows = dict[str, list[dict[str, str]]]


def _date(member: str, label: str, value: object) -> date:
    if not isinstance(value, str):
        raise ValueError(f"member {member}: {label} is not text: {value!r}")
    try:
        day = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"member {member}: {label} is not an ISO date: {value!r}") from None
    if day.isoformat() != value:
        raise ValueError(f"member {member}: {label} is not an ISO date (YYYY-MM-DD): {value!r}")
    return day


def _rate(member: str, label: str, value: object) -> Decimal:
    if not isinstance(value, str) or not value or value != value.strip() or "_" in value:
        raise ValueError(f"member {member}: {label} is not a decimal string: {value!r}")
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"member {member}: {label} is not a decimal string: {value!r}") from None
    if not number.is_finite():
        raise ValueError(f"member {member}: {label} is not finite: {value!r}")
    return number


def _periods(member: str, series: FactorSeries) -> list[tuple[date, date, tuple[Decimal, ...]]]:
    """The member's periods as `(start, end, growth per leg)`, checked to be strictly increasing
    and to join end to start. Growth is `1 + r`, in `CTX`."""
    if series.series_class not in _LEGS:
        raise ValueError(f"member {member}: series_class must be total_return or excess")
    legs = _LEGS[series.series_class]
    if not series.rows:
        raise ValueError(f"member {member}: the series has no periods")
    periods: list[tuple[date, date, tuple[Decimal, ...]]] = []
    for number, row in enumerate(series.rows):
        start = _date(member, f"row {number} period_start", row.get("period_start"))
        end = _date(member, f"row {number} period_end", row.get("period_end"))
        if end <= start:
            raise ValueError(f"member {member}: a period ends on or before its start, at {start}")
        growth = tuple(CTX.add(_ONE, _rate(member, f"row {number} {leg}", row.get(leg))) for leg in legs)
        periods.append((start, end, growth))
    for (first_start, first_end, _), (second_start, _, _) in pairwise(periods):
        if second_start <= first_start:
            raise ValueError(f"member {member}: periods are not strictly increasing at {second_start}")
        if second_start != first_end:
            raise ValueError(
                f"member {member}: its periods do not join between {first_end} and {second_start}"
            )
    return periods


def _compound(
    periods: list[tuple[date, date, tuple[Decimal, ...]]], common: list[date]
) -> list[tuple[Decimal, ...]]:
    """§5.2: the growth of each leg from one common boundary to the next, the product of `1 + r`
    over the member's own periods in between."""
    index = {start: i for i, (start, _, _) in enumerate(periods)}
    legs = len(periods[0][2])
    cursor = index[common[0]]
    out: list[tuple[Decimal, ...]] = []
    for target in common[1:]:
        level = [_ONE] * legs
        while True:
            _, end, growth = periods[cursor]
            level = [CTX.multiply(a, b) for a, b in zip(level, growth, strict=True)]
            cursor += 1
            if end == target:
                break
        out.append(tuple(level))
    return out


def build_panel(spec: Mapping[str, Any], members: Mapping[str, FactorSeries], panel_build_id: str) -> Rows:
    """§5: the rows of the three panel tables, every cell text.

    `spec` is what `read_panel_spec` returns (its `members` maps member code to factor id);
    `members` maps each of those codes to its verified `FactorSeries`. Refuses, with
    `ValueError`: `members` keys that differ from the spec's member codes; a series whose
    `factor_id` differs from the spec's; members that do not share one `numeraire` or one
    `series_class`; a member whose periods are not strictly increasing, or do not join end to
    start; fewer than two common boundaries; fewer than two marks.
    """
    if not isinstance(panel_build_id, str) or not panel_build_id:
        raise ValueError(f"panel_build_id must be non-empty text: {panel_build_id!r}")
    for key, allowed in (
        ("frequency", "monthly"),
        ("alignment", "common_boundaries"),
        ("incomplete_periods", "exclude"),
    ):
        if key in spec and spec[key] != allowed:
            raise ValueError(f"panel spec {key} must be {allowed!r}: {spec[key]!r}")
    wanted = spec.get("members")
    if not isinstance(wanted, Mapping) or not wanted:
        raise ValueError("panel spec members must be a non-empty mapping")
    if set(members) != set(wanted):
        raise ValueError(f"members {sorted(members)} differ from the spec's member codes {sorted(wanted)}")
    codes = sorted(wanted)
    for code in codes:
        if members[code].factor_id != wanted[code]:
            raise ValueError(
                f"member {code}: series factor_id {members[code].factor_id!r} differs from "
                f"the spec's {wanted[code]!r}"
            )
    if len({members[code].numeraire for code in codes}) != 1:
        raise ValueError("members do not share one numeraire")
    if len({members[code].series_class for code in codes}) != 1:
        raise ValueError("members do not share one series_class")

    periods = {code: _periods(code, members[code]) for code in codes}
    boundaries = {code: {p[0] for p in periods[code]} | {periods[code][-1][1]} for code in codes}
    common = sorted(set.intersection(*boundaries.values()))
    if len(common) < 2:
        raise ValueError("the members share fewer than two common boundaries")
    # §5.3: a mark is a common boundary whose next common boundary is in a different month.
    marks = [i for i, (a, b) in enumerate(pairwise(common)) if (a.year, a.month) != (b.year, b.month)]
    if len(marks) < 2:
        raise ValueError("fewer than two marks: the common boundaries span no complete month")

    tables: Rows = {name: [] for name in TABLES["panel"]}
    for order, code in enumerate(codes):
        series = members[code]
        tables["bridge_panel_member"].append(
            {
                "panel_build_id": panel_build_id,
                "member_code": code,
                "column_order": str(order),
                "factor_id": series.factor_id,
                "spec_version": series.spec_version,
                "input_build_id": series.build_id,
                "input_series_sha256": series.series_sha256,
                "series_class": series.series_class,
                "numeraire": series.numeraire,
            }
        )
        growths = _compound(periods[code], common)
        excess = series.series_class == "excess"
        for first, second in pairwise(marks):
            legs = [_ONE] * len(growths[0])
            for growth in growths[first:second]:
                legs = [CTX.multiply(a, b) for a, b in zip(legs, growth, strict=True)]
            returns = [CTX.subtract(leg, _ONE) for leg in legs]
            tables["fact_panel_return"].append(
                {
                    "panel_build_id": panel_build_id,
                    "member_code": code,
                    "period_start": common[first].isoformat(),
                    "period_end": common[second].isoformat(),
                    "return": decimal_text(CTX.subtract(returns[0], returns[1]) if excess else returns[0]),
                    "asset_return": decimal_text(returns[0]) if excess else "",
                    "cash_return": decimal_text(returns[1]) if excess else "",
                }
            )
        tables["fact_panel_coverage"].append(
            {
                "panel_build_id": panel_build_id,
                "member_code": code,
                "first_boundary": min(boundaries[code]).isoformat(),
                "last_boundary": max(boundaries[code]).isoformat(),
                "boundaries": str(len(boundaries[code])),
                "omitted_boundaries": str(len(boundaries[code] - set(common))),
                "common_first": common[0].isoformat(),
                "common_last": common[-1].isoformat(),
                "months": str(len(marks) - 1),
            }
        )
    return tables
