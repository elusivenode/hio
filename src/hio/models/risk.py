"""The covariance and risk-contribution calculations (gold marts contract §6a; proposed, OD-0234).

Pure: IEEE `float64` through NumPy and the standard library, no file access. Every result is
written through `float_text`; counts are plain integers. A decimal cell from a parent is read with
`float(text)`. Section numbers are the contract's.

Choices where the contract is silent (each is also listed in the task summary):

- The panel's members are those of `fact_panel_return`; `bridge_panel_member` and
  `fact_panel_coverage` are not read.
- A member whose values are all equal over a window is refused as constant, in addition to the
  contract's "volatility not positive" test (a repeated value can leave a tiny positive variance
  from rounding).
- The covariance matrix handed to the risk calculation is rebuilt from `fact_covariance`, which
  must hold every ordered pair of the window's members exactly once. Volatility is read from
  `fact_volatility`.
- Weights are taken as given: sign and sum are the portfolio mart's business, not rechecked here.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

import numpy as np

from hio.contracts.gold import TABLES, float_text

Rows = dict[str, list[dict[str, str]]]
Tables = Mapping[str, Sequence[Mapping[str, str]]]

EULER_TOLERANCE = 1e-9


def _text(label: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text: {value!r}")
    return value


def _rows(parent: str, tables: Tables, name: str) -> list[Mapping[str, str]]:
    if not isinstance(tables, Mapping) or name not in tables:
        raise ValueError(f"{parent} has no table {name}")
    rows = list(tables[name])
    return rows


def _cell(parent: str, table: str, number: int, row: Mapping[str, str], column: str) -> str:
    value = row.get(column) if isinstance(row, Mapping) else None
    if not isinstance(value, str):
        raise ValueError(f"{parent} {table} row {number}: {column} is missing or not text")
    return value


def _float(label: str, value: str) -> float:
    if not value or value != value.strip() or "_" in value:
        raise ValueError(f"{label} is not a number: {value!r}")
    try:
        number = float(value)
    except ValueError:
        raise ValueError(f"{label} is not a number: {value!r}") from None
    if not math.isfinite(number):
        raise ValueError(f"{label} is not finite: {value!r}")
    return number


def _date(label: str, value: str) -> str:
    try:
        day = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label} is not an ISO date: {value!r}") from None
    if day.isoformat() != value:
        raise ValueError(f"{label} is not an ISO date (YYYY-MM-DD): {value!r}")
    return value


def _out(kind: str, table: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    columns = TABLES[kind][table]
    for row in rows:
        assert tuple(row) == columns
    return rows


# --------------------------------------------------------------------------------------
# Covariance
# --------------------------------------------------------------------------------------


def _panel_matrix(panel_tables: Tables) -> tuple[list[str], list[tuple[str, str]], np.ndarray]:
    """Members (sorted), the months as `(period_start, period_end)` ascending by end, and the
    months-by-members matrix of `return`. Refuses mismatched months and non-finite values."""
    by_member: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    for number, row in enumerate(_rows("panel", panel_tables, "fact_panel_return")):
        member = _text(f"panel fact_panel_return row {number} member_code", row.get("member_code"))
        start = _date(
            f"panel fact_panel_return row {number} period_start",
            _cell("panel", "fact_panel_return", number, row, "period_start"),
        )
        end = _date(
            f"panel fact_panel_return row {number} period_end",
            _cell("panel", "fact_panel_return", number, row, "period_end"),
        )
        if end <= start:
            raise ValueError(f"member {member}: a month ends on or before its start, at {start}")
        value = _float(
            f"member {member} return for {end}",
            _cell("panel", "fact_panel_return", number, row, "return"),
        )
        if any(e == end for _, e in by_member[member]):
            raise ValueError(f"member {member}: more than one return for the month ending {end}")
        by_member[member][(start, end)] = value
    if not by_member:
        raise ValueError("the panel has no members")
    members = sorted(by_member)
    months = sorted(by_member[members[0]], key=lambda month: month[1])
    for member in members:
        if sorted(by_member[member], key=lambda month: month[1]) != months:
            raise ValueError(f"member {member} has different months from member {members[0]}")
    matrix = np.array(
        [[by_member[member][month] for member in members] for month in months], dtype=np.float64
    ).reshape(len(months), len(members))
    return members, months, matrix


def _window_stats(
    members: Sequence[str], window_id: str, matrix: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """§6a: `numpy.cov(matrix, rowvar=False, ddof=1) * 12`, the volatility and the correlation."""
    for index, member in enumerate(members):
        if bool(np.all(matrix[:, index] == matrix[0, index])):
            raise ValueError(f"window {window_id}: member {member} is constant")
    cov = np.atleast_2d(np.cov(matrix, rowvar=False, ddof=1)) * 12
    vol = np.sqrt(np.diag(cov))
    if not bool(np.all(np.isfinite(cov))) or not bool(np.all(np.isfinite(vol))):
        raise ValueError(f"window {window_id}: a covariance value is not finite")
    if not bool(np.all(vol > 0)):
        raise ValueError(f"window {window_id}: a member has a volatility that is not positive")
    corr = cov / np.outer(vol, vol)
    if not bool(np.all(np.isfinite(corr))):
        raise ValueError(f"window {window_id}: a correlation value is not finite")
    return cov, vol, corr


def build_covariance(
    spec: Mapping[str, Any],
    panel_tables: Tables,
    covariance_build_id: str,
) -> Rows:
    """§6a: the covariance mart's tables, as rows of text.

    `spec` is what `read_covariance_spec` returns; `panel_tables` maps the panel bundle's table
    names to parsed rows (`fact_panel_return` is the one read). Windows: `full` (every month) and,
    when `trailing_months` is n, one `trailing:<last period_end>` for each month end from the n-th
    on. Refused with `ValueError`: fewer than 2 months, or fewer than n + 1 when n is set; months
    that differ between members; a constant member or one whose volatility is not positive; a
    value that is not finite.
    """
    if not isinstance(spec, Mapping) or spec.get("kind") != "covariance":
        raise ValueError("spec is not a covariance spec")
    if spec.get("ddof") != 1 or spec.get("annualisation") != 12 or spec.get("estimator") != "sample":
        raise ValueError("covariance spec: estimator must be sample, ddof 1 and annualisation 12")
    trailing = spec.get("trailing_months")
    if trailing is not None and (isinstance(trailing, bool) or not isinstance(trailing, int) or trailing < 2):
        raise ValueError(f"trailing_months must be an integer of at least 2, or null: {trailing!r}")
    build = _text("covariance_build_id", covariance_build_id)

    members, months, matrix = _panel_matrix(panel_tables)
    count = len(months)
    if count < 2:
        raise ValueError(f"{count} months is fewer than 2")
    if trailing is not None and count < trailing + 1:
        raise ValueError(f"{count} months is fewer than trailing_months + 1 ({trailing + 1})")

    # (window_id, kind, first index, last index), the span being the months first..last.
    windows: list[tuple[str, str, int, int]] = [("full", "full", 0, count - 1)]
    if trailing is not None:
        for last in range(trailing - 1, count):
            windows.append((f"trailing:{months[last][1]}", "trailing", last - trailing + 1, last))

    dim_window: list[dict[str, str]] = []
    fact_covariance: list[dict[str, str]] = []
    fact_volatility: list[dict[str, str]] = []
    for window_id, kind, first, last in windows:
        cov, vol, corr = _window_stats(members, window_id, matrix[first : last + 1])
        dim_window.append(
            {
                "covariance_build_id": build,
                "window_id": window_id,
                "window_kind": kind,
                "first_period_end": months[first][1],
                "last_period_end": months[last][1],
                "n_obs": str(last - first + 1),
            }
        )
        for i, member_i in enumerate(members):
            fact_volatility.append(
                {
                    "covariance_build_id": build,
                    "window_id": window_id,
                    "member_code": member_i,
                    "volatility": float_text(vol[i]),
                }
            )
            for j, member_j in enumerate(members):
                fact_covariance.append(
                    {
                        "covariance_build_id": build,
                        "window_id": window_id,
                        "member_i": member_i,
                        "member_j": member_j,
                        "covariance": float_text(cov[i, j]),
                        "correlation": float_text(corr[i, j]),
                    }
                )
    return {
        "dim_window": _out("covariance", "dim_window", dim_window),
        "fact_covariance": _out("covariance", "fact_covariance", fact_covariance),
        "fact_volatility": _out("covariance", "fact_volatility", fact_volatility),
    }


# --------------------------------------------------------------------------------------
# Risk contribution
# --------------------------------------------------------------------------------------


def _weights(portfolio_tables: Tables) -> dict[str, float]:
    weights: dict[str, float] = {}
    builds: set[str] = set()
    for number, row in enumerate(_rows("portfolio", portfolio_tables, "fact_target_allocation")):
        member = _text(f"portfolio fact_target_allocation row {number} member_code", row.get("member_code"))
        if member in weights:
            raise ValueError(f"portfolio: more than one weight for member {member}")
        weights[member] = _float(
            f"portfolio weight for {member}",
            _cell("portfolio", "fact_target_allocation", number, row, "target_weight"),
        )
        builds.add(_cell("portfolio", "fact_target_allocation", number, row, "portfolio_build_id"))
    if not weights:
        raise ValueError("the portfolio has no weights")
    if len(builds) != 1:
        raise ValueError("the portfolio's weights come from more than one build")
    return weights


def _covariance_windows(
    covariance_tables: Tables,
) -> tuple[list[str], dict[str, tuple[np.ndarray, np.ndarray]]]:
    """Window ids in `dim_window` order, and for each the covariance matrix and the volatility
    vector, members in `member_code` order. Every window must have the same members."""
    window_ids: list[str] = []
    builds: set[str] = set()
    for number, row in enumerate(_rows("covariance", covariance_tables, "dim_window")):
        window_id = _text(f"covariance dim_window row {number} window_id", row.get("window_id"))
        if window_id in window_ids:
            raise ValueError(f"covariance: window {window_id} is listed twice")
        window_ids.append(window_id)
        builds.add(_cell("covariance", "dim_window", number, row, "covariance_build_id"))
    if not window_ids:
        raise ValueError("the covariance has no windows")
    if len(builds) != 1:
        raise ValueError("the covariance's windows come from more than one build")

    vols: dict[str, dict[str, float]] = defaultdict(dict)
    for number, row in enumerate(_rows("covariance", covariance_tables, "fact_volatility")):
        window_id = _cell("covariance", "fact_volatility", number, row, "window_id")
        member = _text(f"covariance fact_volatility row {number} member_code", row.get("member_code"))
        if window_id not in window_ids:
            raise ValueError(f"covariance: volatility for unknown window {window_id}")
        if member in vols[window_id]:
            raise ValueError(f"covariance: window {window_id} repeats the volatility of {member}")
        vols[window_id][member] = _float(
            f"volatility of {member} in {window_id}",
            _cell("covariance", "fact_volatility", number, row, "volatility"),
        )
    covs: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    for number, row in enumerate(_rows("covariance", covariance_tables, "fact_covariance")):
        window_id = _cell("covariance", "fact_covariance", number, row, "window_id")
        pair = (
            _text(f"covariance fact_covariance row {number} member_i", row.get("member_i")),
            _text(f"covariance fact_covariance row {number} member_j", row.get("member_j")),
        )
        if window_id not in window_ids:
            raise ValueError(f"covariance: covariance for unknown window {window_id}")
        if pair in covs[window_id]:
            raise ValueError(f"covariance: window {window_id} repeats the pair {pair}")
        covs[window_id][pair] = _float(
            f"covariance of {pair} in {window_id}",
            _cell("covariance", "fact_covariance", number, row, "covariance"),
        )

    members = sorted(vols[window_ids[0]])
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for window_id in window_ids:
        if sorted(vols[window_id]) != members:
            raise ValueError(f"covariance: window {window_id} has different members from {window_ids[0]}")
        if set(covs[window_id]) != {(i, j) for i in members for j in members}:
            raise ValueError(f"covariance: window {window_id} does not hold every ordered pair once")
        matrix = np.array([[covs[window_id][(i, j)] for j in members] for i in members], dtype=np.float64)
        vol = np.array([vols[window_id][m] for m in members], dtype=np.float64)
        out[window_id] = (matrix.reshape(len(members), len(members)), vol)
    return members, out


def build_risk_contribution(
    spec: Mapping[str, Any],
    covariance_tables: Tables,
    portfolio_tables: Tables,
    risk_build_id: str,
) -> Rows:
    """§6a: the risk-contribution mart's tables, as rows of text.

    `spec` is what `read_risk_spec` returns; `covariance_tables` holds `dim_window`,
    `fact_covariance` and `fact_volatility` of the covariance bundle, `portfolio_tables` holds
    `fact_target_allocation` of the portfolio-path bundle. For each window: variance `w'Sw`,
    volatility, marginal `Sw / s`, component `w * Sw / s`, percentage `component / s`, the Euler
    gap `|sum(component) / s - 1|` and the diversification ratio `sum(|w| * vol) / s`. Refused with
    `ValueError`: a non-positive variance; a gap above 1e-9; a weight for a member the covariance
    lacks, or a covariance member without a weight; a value that is not finite.
    """
    if not isinstance(spec, Mapping) or spec.get("kind") != "risk_contribution":
        raise ValueError("spec is not a risk-contribution spec")
    build = _text("risk_build_id", risk_build_id)

    weights = _weights(portfolio_tables)
    members, windows = _covariance_windows(covariance_tables)
    if set(weights) != set(members):
        lacking = sorted(set(weights) - set(members))
        unweighted = sorted(set(members) - set(weights))
        raise ValueError(
            f"weights and covariance members differ: no covariance for {lacking}, no weight for {unweighted}"
        )
    w = np.array([weights[m] for m in members], dtype=np.float64)

    portfolio_risk: list[dict[str, str]] = []
    contributions: list[dict[str, str]] = []
    for window_id, (cov, vol) in windows.items():
        sw = cov @ w
        variance = float(w @ sw)
        if not math.isfinite(variance) or not variance > 0:
            raise ValueError(f"window {window_id}: the portfolio variance is not positive")
        sigma = math.sqrt(variance)
        marginal = sw / sigma
        component = w * sw / sigma
        percentage = component / sigma
        euler = abs(float(component.sum()) / sigma - 1)
        ratio = float(np.abs(w) @ vol) / sigma
        for label, values in (
            ("marginal", marginal),
            ("component", component),
            ("percentage", percentage),
            ("euler gap", np.array([euler])),
            ("diversification ratio", np.array([ratio])),
        ):
            if not bool(np.all(np.isfinite(values))):
                raise ValueError(f"window {window_id}: the {label} contribution is not finite")
        if euler > EULER_TOLERANCE:
            raise ValueError(
                f"window {window_id}: risk contributions do not sum to the portfolio volatility "
                f"(relative gap {euler})"
            )
        portfolio_risk.append(
            {
                "risk_build_id": build,
                "window_id": window_id,
                "portfolio_variance": float_text(variance),
                "portfolio_volatility": float_text(sigma),
                "diversification_ratio": float_text(ratio),
                "euler_relative_gap": float_text(euler),
            }
        )
        for index, member in enumerate(members):
            contributions.append(
                {
                    "risk_build_id": build,
                    "window_id": window_id,
                    "member_code": member,
                    "weight": float_text(float(w[index])),
                    "marginal_contribution": float_text(float(marginal[index])),
                    "component_contribution": float_text(float(component[index])),
                    "percentage_contribution": float_text(float(percentage[index])),
                }
            )
    return {
        "fact_portfolio_risk": _out("risk_contribution", "fact_portfolio_risk", portfolio_risk),
        "fact_risk_contribution": _out("risk_contribution", "fact_risk_contribution", contributions),
    }
