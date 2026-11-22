"""The portfolio-path calculation of the gold marts contract (§6), pure and exact.

Built to `docs/decisions/gold-marts-contract.md` (proposed; OD-0233). From a portfolio spec and a
panel's three tables it returns the three §6 tables' rows: the target allocation, the monthly
portfolio return with its wealth index, and each member's contribution. Weights reset to target at
every month end. Arithmetic is `decimal` in `hio.contracts.gold.CTX` and every cell is text; no
float and no file access. This module imports `hio.contracts` only.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from itertools import pairwise
from typing import Any

from hio.contracts.gold import CTX, decimal_text

_PANEL_TABLES = ("bridge_panel_member", "fact_panel_return", "fact_panel_coverage")
_CONTRIBUTION_TOLERANCE = Decimal("1e-30")
_ONE = Decimal(1)


def _weights(spec: Mapping[str, Any]) -> dict[str, Decimal]:
    if not isinstance(spec, Mapping) or "weights" not in spec:
        raise ValueError("portfolio spec has no weights")
    raw = spec["weights"]
    if not isinstance(raw, Mapping) or not raw:
        raise ValueError("portfolio weights must be a non-empty mapping")
    weights: dict[str, Decimal] = {}
    total = Fraction(0)
    for code, value in raw.items():
        if not isinstance(value, str) or value != value.strip() or "_" in value:
            raise ValueError(f"weight {code!r} is not a decimal string: {value!r}")
        try:
            weight = Decimal(value)
        except InvalidOperation:
            raise ValueError(f"weight {code!r} is not a decimal string: {value!r}") from None
        if not weight.is_finite():
            raise ValueError(f"weight {code!r} is not finite: {value!r}")
        if weight.is_signed():
            raise ValueError(f"weight {code!r} is negative: {value!r}")
        weights[code] = weight
        total += Fraction(weight)
    if total != 1:
        raise ValueError(f"weights must sum to exactly 1: they sum to {total}")
    return weights


def _decimal(label: str, cell: object) -> Decimal:
    if not isinstance(cell, str) or cell == "":
        raise ValueError(f"{label} is not a decimal string: {cell!r}")
    try:
        value = Decimal(cell)
    except InvalidOperation:
        raise ValueError(f"{label} is not a decimal string: {cell!r}") from None
    if not value.is_finite():
        raise ValueError(f"{label} is not finite: {cell!r}")
    return value


def _rows(panel_tables: Mapping[str, list[dict[str, str]]], name: str) -> list[dict[str, str]]:
    rows = panel_tables[name]
    if not isinstance(rows, list):
        raise ValueError(f"panel table {name} must be a list of rows")
    return rows


def _panel_members(panel_tables: Mapping[str, list[dict[str, str]]]) -> tuple[str, set[str]]:
    """Check the panel tables' shape and return (the one panel build id, the member codes)."""
    if not isinstance(panel_tables, Mapping):
        raise ValueError("panel_tables must be a mapping")
    missing = [name for name in _PANEL_TABLES if name not in panel_tables]
    if missing:
        raise ValueError(f"panel tables missing: {missing}")
    ids: set[str] = set()
    for name in _PANEL_TABLES:
        for row in _rows(panel_tables, name):
            ids.add(row.get("panel_build_id", ""))
    if len(ids) != 1 or "" in ids:
        raise ValueError(f"panel tables must name exactly one panel_build_id: {sorted(ids)}")
    members: set[str] = set()
    for row in _rows(panel_tables, "bridge_panel_member"):
        code = row.get("member_code", "")
        if code in members:
            raise ValueError(f"panel member {code!r} is listed twice")
        members.add(code)
        if row.get("series_class") != "total_return":
            raise ValueError(
                f"panel member {code!r} is a {row.get('series_class')!r} series: only total_return "
                "series are holdings (an excess return is not a holding)"
            )
    if not members:
        raise ValueError("panel has no members")
    return next(iter(ids)), members


def _monthly_returns(
    panel_tables: Mapping[str, list[dict[str, str]]], members: set[str]
) -> dict[str, list[tuple[str, str, Decimal]]]:
    """Each member's months as (period_start, period_end, return), ascending, with the months
    checked to be identical across members and to run end to start."""
    by_member: dict[str, list[tuple[str, str, Decimal]]] = {code: [] for code in members}
    for row in _rows(panel_tables, "fact_panel_return"):
        code = row.get("member_code", "")
        if code not in by_member:
            raise ValueError(f"return row for {code!r}, which is not a panel member")
        start, end = row.get("period_start", ""), row.get("period_end", "")
        if not start or not end or start >= end:
            raise ValueError(f"member {code!r}: bad month {start!r} to {end!r}")
        by_member[code].append((start, end, _decimal(f"member {code!r} return for {end}", row.get("return"))))
    for code, months in by_member.items():
        months.sort(key=lambda m: (m[1], m[0]))
        for earlier, later in pairwise(months):
            if earlier[1] != later[0]:
                raise ValueError(
                    f"member {code!r}: months do not join end to start ({earlier[1]} then {later[0]})"
                )
    calendars = {code: [(m[0], m[1]) for m in months] for code, months in by_member.items()}
    first_code = sorted(calendars)[0]
    for code in sorted(calendars):
        if calendars[code] != calendars[first_code]:
            raise ValueError(f"members {first_code!r} and {code!r} have different months")
    if not calendars[first_code]:
        raise ValueError("panel has no months")
    counts = {row.get("member_code"): row.get("months") for row in _rows(panel_tables, "fact_panel_coverage")}
    for code, months in by_member.items():
        if counts.get(code) != str(len(months)):
            raise ValueError(
                f"member {code!r}: coverage says {counts.get(code)!r} months, return rows have {len(months)}"
            )
    return by_member


def build_portfolio_path(
    spec: Mapping[str, Any],
    panel_tables: Mapping[str, list[dict[str, str]]],
    portfolio_build_id: str,
) -> dict[str, list[dict[str, str]]]:
    """§6: the three portfolio-path tables' rows (every cell text; unsorted is fine).

    `spec` is what `read_portfolio_spec` returns (only `weights` is used); `panel_tables` holds
    the panel's `bridge_panel_member`, `fact_panel_return` and `fact_panel_coverage` rows as parsed
    text. Weights reset to target at every month end, so each month's portfolio return is the sum
    over members of `weight x member return`; the wealth index starts at 1 and is multiplied by
    `1 + portfolio return` each month, and is written after each month. A contribution is
    `weight x member return`, and a month's contributions are checked to sum to its portfolio
    return within 1e-30. Pure: `Decimal` in `CTX` only.

    Refused (`ValueError`): weights that do not name exactly the panel's members, that are not
    decimal strings, are negative, or do not sum to exactly 1; a panel with any member that is not
    `total_return`; panel tables that are missing, name more than one panel, or disagree with one
    another; members whose months differ or do not join end to start; no months.
    """
    if not isinstance(portfolio_build_id, str) or not portfolio_build_id:
        raise ValueError("portfolio_build_id must be non-empty text")
    weights = _weights(spec)
    _, members = _panel_members(panel_tables)
    if set(weights) != members:
        raise ValueError(
            f"weights name {sorted(weights)}, but the panel's members are {sorted(members)}: "
            f"unknown {sorted(set(weights) - members)}, missing {sorted(members - set(weights))}"
        )
    returns = _monthly_returns(panel_tables, members)
    codes = sorted(weights)

    allocation = [
        {
            "portfolio_build_id": portfolio_build_id,
            "member_code": code,
            "target_weight": decimal_text(weights[code]),
        }
        for code in codes
    ]
    path: list[dict[str, str]] = []
    contributions: list[dict[str, str]] = []
    wealth = _ONE
    for index, (start, end, _) in enumerate(returns[codes[0]]):
        parts = {code: CTX.multiply(weights[code], returns[code][index][2]) for code in codes}
        portfolio_return = Decimal(0)
        for code in codes:
            portfolio_return = CTX.add(portfolio_return, parts[code])
        # The check re-adds the written contributions in the opposite order, in `CTX`.
        readded = Decimal(0)
        for code in reversed(codes):
            readded = CTX.add(readded, parts[code])
        if abs(CTX.subtract(portfolio_return, readded)) > _CONTRIBUTION_TOLERANCE:
            raise ValueError(f"contributions do not sum to the portfolio return for {end}")
        wealth = CTX.multiply(wealth, CTX.add(_ONE, portfolio_return))
        path.append(
            {
                "portfolio_build_id": portfolio_build_id,
                "period_start": start,
                "period_end": end,
                "portfolio_return": decimal_text(portfolio_return),
                "wealth_index": decimal_text(wealth),
            }
        )
        for code in codes:
            contributions.append(
                {
                    "portfolio_build_id": portfolio_build_id,
                    "member_code": code,
                    "period_start": start,
                    "period_end": end,
                    "start_weight": decimal_text(weights[code]),
                    "member_return": decimal_text(returns[code][index][2]),
                    "contribution": decimal_text(parts[code]),
                }
            )
    return {
        "fact_target_allocation": allocation,
        "fact_portfolio_return": path,
        "fact_return_contribution": contributions,
    }
