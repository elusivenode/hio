"""A simple, descriptive risk model for a set of built series (OD-0215).

Inputs are build directories: total-return builds (`series.csv` with `total_return`, written by
`tools/factor_build.py`) or excess-return builds (`series.csv` with `asset_return`, `cash_return`,
`excess_return`). All builds in one run have the same `series_class`: funded and excess forms are never
mixed (RA-INV-015). Total-return weights form a funded portfolio (each in (0, 1], summing to 1). Excess-return
weights are exposures (each non-zero and finite, no sum constraint): the cash leg lies outside the model and
is counted once, by the user.

Monthly returns come from `hio.portfolio.fixed_allocation`: the legs are aligned on their common dates, each
compounded exactly between common dates, and taken between calendar month ends; the first month (possibly
partial) and the last (possibly partial) are dropped. For excess-return builds the asset leg and the cash leg
are compounded separately to month ends and their difference is the month's excess. The excess is never
compounded itself (RA-INV-016; RA section 1: the excess is arithmetic per period).

The model describes the sample it is given: sample covariance (ddof 1, annualised by 12), volatilities,
risk contributions for fixed weights, a diversification ratio and trailing-window rolling statistics. It makes
no forecast, optimisation or recommendation. The command prints counts and hashes only, never a return.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

from hio.portfolio import fixed_allocation as fa

TOOLS = Path(__file__).resolve().parent
TOTAL_HEADER = ["period_start", "period_end", "price_return", "income_return", "total_return", "index"]
EXCESS_HEADER = ["period_start", "period_end", "asset_return", "cash_return", "excess_return"]
WEIGHT_TOLERANCE = 1e-12
EULER_TOLERANCE = 1e-12
IDENTITY_TOLERANCE = 1e-12
PERIODS_PER_YEAR = 12
DEFAULT_WINDOW = 36


def _load_helpers():
    spec = importlib.util.spec_from_file_location(
        "_hio_portfolio_analytics", TOOLS / "portfolio_analytics.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PA = _load_helpers()
_check_outside_repo = _PA._check_outside_repo
_write = _PA._write
_parse_weights = _PA._parse_weights


def _decimal(text: str) -> Decimal:
    value = Decimal(text)
    if not value.is_finite():
        raise ValueError("a return is not finite")
    return value


def load_build(directory: Path) -> dict:
    """Read and verify one build of either format. The record gains `legs`: leg name to Intervals (a
    total-return build has one leg, `total`; an excess-return build has `asset` and `cash`)."""
    directory = _check_outside_repo(Path(directory), "a build directory")
    try:
        record = json.loads((directory / "build.json").read_text(encoding="utf-8"))
        raw = (directory / "series.csv").read_bytes()
    except json.JSONDecodeError as exc:
        raise ValueError(f"build.json in {directory.name} is not valid JSON") from exc
    for key in ("factor_id", "series_class", "numeraire", "series_sha256", "build_id", "invariants"):
        if key not in record:
            raise ValueError(f"build.json in {directory.name} lacks {key}")
    name = record["factor_id"]
    if hashlib.sha256(raw).hexdigest() != record["series_sha256"]:
        raise ValueError(f"series.csv of {name} does not match its recorded sha256")
    if record["series_class"] == "total_return":
        header, columns = TOTAL_HEADER, {"total": 4}
    elif record["series_class"] == "excess_return":
        header, columns = EXCESS_HEADER, {"asset": 2, "cash": 3}
    else:
        raise ValueError(
            f"{name} has series_class {record['series_class']}: not total_return or excess_return"
        )
    rows = list(csv.reader(raw.decode("utf-8").splitlines()))
    if not rows or rows[0] != header:
        raise ValueError(f"series.csv of {name} has an unexpected header")
    legs: dict[str, list[fa.Interval]] = {leg: [] for leg in columns}
    try:
        for row in rows[1:]:
            if len(row) != len(header):
                raise ValueError("a row has the wrong number of fields")
            start, end = date.fromisoformat(row[0]), date.fromisoformat(row[1])
            for leg, column in columns.items():
                legs[leg].append(fa.Interval(start, end, _decimal(row[column])))
    except (ValueError, InvalidOperation) as exc:
        raise ValueError(f"series.csv of {name} is malformed: {exc}") from exc
    return {**record, "legs": legs}


def _check_builds(builds: Sequence[Mapping], weights: Mapping[str, float], window: int) -> None:
    if not builds:
        raise ValueError("no builds given")
    ids = [b["factor_id"] for b in builds]
    if len(set(ids)) != len(ids):
        raise ValueError("factor ids are not distinct")
    if len({b["series_class"] for b in builds}) != 1:
        raise ValueError(
            "the builds do not share one series_class (RA-INV-015: funded and excess forms are not mixed)"
        )
    if len({b["numeraire"] for b in builds}) != 1:
        raise ValueError("the builds do not share one numeraire")
    for b in builds:
        invariants = b["invariants"]
        if not isinstance(invariants, dict) or not invariants:
            raise ValueError(f"{b['factor_id']} records no invariants")
        if not all(isinstance(v, dict) and v.get("passed") is True for v in invariants.values()):
            raise ValueError(f"{b['factor_id']} has an invariant that did not pass")
    if set(weights) != set(ids):
        raise ValueError("weights must name exactly the builds given")
    if builds[0]["series_class"] == "total_return":
        for factor_id, w in weights.items():
            if not 0 < w <= 1:
                raise ValueError(f"weight of {factor_id} is not in (0, 1]")
        if abs(sum(weights.values()) - 1) > WEIGHT_TOLERANCE:
            raise ValueError("weights do not sum to 1")
    else:
        for factor_id, w in weights.items():
            if not math.isfinite(w) or w == 0:
                raise ValueError(f"exposure of {factor_id} is zero or not finite")
    if window < 2:
        raise ValueError("--window must be at least 2 months")


def monthly_returns(builds: Sequence[Mapping]) -> tuple[list[str], list[date], date, np.ndarray]:
    """(sorted factor ids, month ends, first date of the first month, months x sleeves matrix)."""
    if not builds:
        raise ValueError("no builds given")
    kinds = {b["series_class"] for b in builds}
    if len(kinds) != 1:
        raise ValueError("the builds do not share one series_class (RA-INV-015)")
    excess = kinds == {"excess_return"}
    series: dict[str, list[fa.Interval]] = {}
    for b in builds:
        for leg, intervals in b["legs"].items():
            series[f"{b['factor_id']}#{leg}"] = intervals
    panel = fa.align(series)
    ends = fa.period_ends(panel.dates, "monthly")
    if len(ends) < 2:
        raise ValueError("fewer than one complete month in the common span")
    levels = fa.sleeve_levels(panel)
    monthly = fa.period_returns(panel.dates, levels, "monthly")  # months x legs
    column = {name: k for k, name in enumerate(panel.sleeves)}
    ids = sorted(b["factor_id"] for b in builds)
    if excess:
        matrix = np.column_stack(
            [monthly[:, column[f"{i}#asset"]] - monthly[:, column[f"{i}#cash"]] for i in ids]
        )
    else:
        matrix = np.column_stack([monthly[:, column[f"{i}#total"]] for i in ids])
    return ids, [panel.dates[i] for i in ends[1:]], panel.dates[ends[0]], matrix


def _covariance(matrix: np.ndarray) -> np.ndarray:
    return np.atleast_2d(np.cov(matrix, rowvar=False, ddof=1)) * PERIODS_PER_YEAR


def _rolling(
    matrix: np.ndarray, w: np.ndarray, window: int
) -> list[tuple[int, np.ndarray, np.ndarray, float]]:
    rows = []
    for t in range(window, len(matrix) + 1):
        cov = _covariance(matrix[t - window : t])
        vol = np.sqrt(np.diag(cov))
        if not np.all(vol > 0) or not np.all(np.isfinite(cov)):
            raise ValueError("a rolling window has a sleeve with zero or undefined volatility")
        variance = float(w @ cov @ w)
        if not variance > 0:
            raise ValueError("a rolling window has a non-positive portfolio variance")
        rows.append((t - 1, vol, cov / np.outer(vol, vol), math.sqrt(variance)))
    return rows


def risk(builds: Sequence[Mapping], weights: Mapping[str, float], window: int = DEFAULT_WINDOW) -> dict:
    """The risk record. `rolling` holds the rows for rolling.csv and is not part of risk.json."""
    _check_builds(builds, weights, window)
    ids, month_ends, first, matrix = monthly_returns(builds)
    months = len(month_ends)
    if months < window + 1:
        raise ValueError(f"{months} months is fewer than window + 1 ({window + 1})")
    w = np.array([weights[i] for i in ids], dtype=np.float64)
    cov = _covariance(matrix)
    vol = np.sqrt(np.diag(cov))
    if not np.all(vol > 0) or not np.all(np.isfinite(cov)):
        raise ValueError("a sleeve has zero or undefined volatility in the sample")
    corr = cov / np.outer(vol, vol)
    variance = float(w @ cov @ w)
    if not variance > 0:
        raise ValueError("the portfolio variance is not positive")
    sigma = math.sqrt(variance)
    sigma_w = cov @ w
    marginal = sigma_w / sigma
    component = w * sigma_w / sigma
    euler = abs(float(component.sum()) / sigma - 1)
    if euler > EULER_TOLERANCE:
        raise ValueError(f"risk contributions do not sum to the portfolio volatility (relative gap {euler})")
    sanity = None
    if builds[0]["series_class"] == "total_return":
        own = float(np.std(matrix @ w, ddof=1) * math.sqrt(PERIODS_PER_YEAR))
        gap = abs(own / sigma - 1)
        if gap > IDENTITY_TOLERANCE:
            raise ValueError(f"w'Sw does not match the monthly portfolio volatility (relative gap {gap})")
        sanity = {"monthly_portfolio_volatility": own, "relative_difference": gap}

    def by_id(values: np.ndarray) -> dict:
        return {i: float(v) for i, v in zip(ids, values, strict=True)}

    rolling = [
        {"month_end": month_ends[t].isoformat(), "vol": v, "corr": c, "portfolio": p}
        for t, v, c, p in _rolling(matrix, w, window)
    ]
    return {
        "inputs": [
            {
                "factor_id": b["factor_id"],
                "build_id": b["build_id"],
                "series_sha256": b["series_sha256"],
                "series_class": b["series_class"],
            }
            for b in sorted(builds, key=lambda b: b["factor_id"])
        ],
        "weights": by_id(w),
        "span": {"first": first.isoformat(), "last": month_ends[-1].isoformat(), "months": months},
        "window": window,
        "results": {
            "covariance": {"order": ids, "matrix": cov.tolist()},
            "correlation": {"order": ids, "matrix": corr.tolist()},
            "volatility": by_id(vol),
            "portfolio_variance": variance,
            "portfolio_volatility": sigma,
            "marginal_contribution": by_id(marginal),
            "component_contribution": by_id(component),
            "percentage_contribution": by_id(component / sigma),
            "euler_relative_gap": euler,
            "diversification_ratio": float(np.abs(w) @ vol / sigma),
            "sanity_monthly_portfolio_volatility": sanity,
        },
        "rolling": rolling,
    }


def _pairs(ids: Sequence[str]) -> list[tuple[int, int]]:
    return [(a, b) for a in range(len(ids)) for b in range(a + 1, len(ids))]


def _rolling_csv(rows: Sequence[Mapping], ids: Sequence[str]) -> bytes:
    pairs = _pairs(ids)
    header = ["month_end", *(f"{i}.volatility" for i in ids)]
    header += [f"{ids[a]}|{ids[b]}.correlation" for a, b in pairs] + ["portfolio.volatility"]
    lines = [",".join(header)]
    for row in rows:
        cells = [row["month_end"], *(repr(float(v)) for v in row["vol"])]
        cells += [repr(float(row["corr"][a, b])) for a, b in pairs] + [repr(float(row["portfolio"]))]
        lines.append(",".join(cells))
    return ("\n".join(lines) + "\n").encode("utf-8")


def run(build_dirs: Sequence[Path], weights: Mapping[str, float], window: int, out: Path) -> dict:
    out = _check_outside_repo(Path(out), "--out")
    result = risk([load_build(d) for d in build_dirs], weights, window)
    rows = result.pop("rolling")
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    out.chmod(0o700)
    body = (json.dumps(result, sort_keys=True, indent=1) + "\n").encode("utf-8")
    return {
        "months": result["span"]["months"],
        "sleeves": len(result["weights"]),
        "rolling_rows": len(rows),
        "risk_sha256": _write(out / "risk.json", body),
        "rolling_sha256": _write(out / "rolling.csv", _rolling_csv(rows, sorted(result["weights"]))),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="append", required=True, type=Path)
    parser.add_argument("--weight", action="append", required=True)
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        summary = run(args.build, _parse_weights(args.weight), args.window, args.out)
    except (ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"months: {summary['months']}")
    print(f"sleeves: {summary['sleeves']}")
    print(f"rolling rows: {summary['rolling_rows']}")
    print(f"risk.json sha256: {summary['risk_sha256']}")
    print(f"rolling.csv sha256: {summary['rolling_sha256']}")
    print("risk contributions reconcile: yes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
