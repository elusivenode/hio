"""Descriptive analytics for a fixed-weight portfolio of built factor series (OD-0213).

Each input is a build directory (`series.csv` and `build.json`, the shared format written by
`tools/factor_build.py`). The calculation is `hio.portfolio.fixed_allocation`: monthly reset to target
weights, first and last months dropped, volatility ddof 1 times sqrt(12), geometric return on 365.25 days.
It describes the returns it is given: no forecast, optimisation or recommendation.

Only funded total-return series are accepted (RA-INV-015). The monthly contributions (target weight times
the sleeve's month return) sum to the portfolio's month return exactly, because weights reset at each month
end. Their arithmetic sum over all months does not equal the compounded return (RA-INV-016); the difference
is reported as `compounding_residual`, never forced to zero.

The command prints counts and hashes only, never a return or a date.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

from hio.portfolio import fixed_allocation as fa

REPO = Path(__file__).resolve().parent.parent
HEADER = ["period_start", "period_end", "price_return", "income_return", "total_return", "index"]
WEIGHT_TOLERANCE = 1e-12
RECONCILE_LIMIT = 1e-9
CONTRIBUTION_TOLERANCE = 1e-12


def _check_outside_repo(path: Path, what: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError(f"{what} must lie outside the repository")
    return resolved


def load_build(directory: Path) -> dict:
    """Read and verify one build. Returns its record plus `intervals`, one Interval per row."""
    directory = _check_outside_repo(Path(directory), "a build directory")
    try:
        record = json.loads((directory / "build.json").read_text(encoding="utf-8"))
        raw = (directory / "series.csv").read_bytes()
    except json.JSONDecodeError as exc:
        raise ValueError(f"build.json in {directory.name} is not valid JSON") from exc
    for key in ("factor_id", "series_class", "numeraire", "series_sha256", "build_id", "invariants"):
        if key not in record:
            raise ValueError(f"build.json in {directory.name} lacks {key}")
    if hashlib.sha256(raw).hexdigest() != record["series_sha256"]:
        raise ValueError(f"series.csv of {record['factor_id']} does not match its recorded sha256")
    lines = raw.decode("utf-8").splitlines()
    rows = list(csv.reader(lines))
    if not rows or rows[0] != HEADER:
        raise ValueError(f"series.csv of {record['factor_id']} has an unexpected header")
    intervals = []
    try:
        for row in rows[1:]:
            if len(row) != len(HEADER):
                raise ValueError("a row has the wrong number of fields")
            r = Decimal(row[4])
            if not r.is_finite():
                raise ValueError("a total_return is not finite")
            intervals.append(fa.Interval(date.fromisoformat(row[0]), date.fromisoformat(row[1]), r))
    except (ValueError, InvalidOperation) as exc:
        raise ValueError(f"series.csv of {record['factor_id']} is malformed: {exc}") from exc
    return {**record, "intervals": intervals}


def _check_builds(builds: Sequence[Mapping], weights: Mapping[str, float]) -> None:
    if not builds:
        raise ValueError("no builds given")
    ids = [b["factor_id"] for b in builds]
    if len(set(ids)) != len(ids):
        raise ValueError("factor ids are not distinct")
    for b in builds:
        if b["series_class"] != "total_return":
            raise ValueError(
                f"{b['factor_id']} is {b['series_class']}: only funded total_return series are accepted "
                "(RA-INV-015: funded and excess forms are not mixed)"
            )
    if len({b["numeraire"] for b in builds}) != 1:
        raise ValueError("the builds do not share one numeraire")
    if set(weights) != set(ids):
        raise ValueError("weights must name exactly the builds given")
    for factor_id, w in weights.items():
        if not 0 < w <= 1:
            raise ValueError(f"weight of {factor_id} is not in (0, 1]")
    if abs(sum(weights.values()) - 1) > WEIGHT_TOLERANCE:
        raise ValueError("weights do not sum to 1")
    for b in builds:
        invariants = b["invariants"]
        if not invariants or not all(v.get("passed") is True for v in invariants.values()):
            raise ValueError(f"{b['factor_id']} has an invariant that did not pass")


def _describe_drawdown(d: fa.Drawdown) -> dict:
    return {
        "max_drawdown": d.max_drawdown,
        "peak": d.peak.isoformat(),
        "trough": d.trough.isoformat(),
        "recovery": d.recovery.isoformat() if d.recovery else None,
        "longest_underwater_days": d.longest_underwater_days,
        "underwater_fraction": d.underwater_fraction,
    }


def _metrics(dates: Sequence[date], levels: np.ndarray, monthly: np.ndarray, month_ends: list[date]) -> dict:
    path = fa.WealthPath(tuple(dates), levels, levels[:, None])
    worst, best = int(np.argmin(monthly)), int(np.argmax(monthly))
    return {
        "annualised_return": fa.annualised_return(path),
        "annualised_volatility": fa.annualised_volatility(monthly, "monthly"),
        "drawdown": _describe_drawdown(fa.drawdown(dates, levels)),
        "worst_month": {"month_end": month_ends[worst].isoformat(), "return": float(monthly[worst])},
        "best_month": {"month_end": month_ends[best].isoformat(), "return": float(monthly[best])},
    }


def analyse(builds: Sequence[Mapping], weights: Mapping[str, float]) -> dict:
    """The analytics record. `monthly` holds the rows for monthly.csv and is not part of analytics.json."""
    _check_builds(builds, weights)
    panel = fa.align({b["factor_id"]: b["intervals"] for b in builds})
    ids = list(panel.sleeves)  # sorted
    path = fa.wealth_path(panel, weights)
    try:
        residual = fa.reconcile(panel, weights, path)
    except ArithmeticError:
        residual = RECONCILE_LIMIT * 2
    if residual > RECONCILE_LIMIT:
        raise ValueError("the wealth path does not reconcile")

    ends = fa.period_ends(panel.dates, "monthly")
    if len(ends) < 3:
        raise ValueError("fewer than two complete months in the common span")
    month_ends = [panel.dates[i] for i in ends[1:]]
    portfolio = fa.period_returns(panel.dates, path.wealth, "monthly")
    levels = fa.sleeve_levels(panel)
    sleeves = fa.period_returns(panel.dates, levels, "monthly")  # months x sleeves
    target = np.array([weights[i] for i in ids], dtype=np.float64)
    contributions = sleeves * target
    gap = float(np.max(np.abs(contributions.sum(axis=1) - portfolio)))
    if gap > CONTRIBUTION_TOLERANCE:
        raise ValueError(f"contributions do not sum to the portfolio return (largest gap {gap})")

    compounded = float(np.prod(1 + portfolio) - 1)
    residual_compounding = float(contributions.sum() - compounded)
    peaks = np.maximum.accumulate(path.wealth)
    depth = (1 - path.wealth / peaks)[ends[1:]]
    correlation = np.atleast_2d(fa.covariance(sleeves)[1]) if len(ids) > 1 else np.ones((1, 1))

    sleeve_record = {}
    for k, factor_id in enumerate(ids):
        entry = _metrics(panel.dates, levels[:, k], sleeves[:, k], month_ends)
        entry["weight"] = weights[factor_id]
        entry["sum_of_contributions"] = float(contributions[:, k].sum())
        sleeve_record[factor_id] = entry

    portfolio_record = _metrics(panel.dates, path.wealth, portfolio, month_ends)
    portfolio_record.update(
        {
            "compounded_return": compounded,
            "sum_of_contributions": float(contributions.sum()),
            "compounding_residual": residual_compounding,
            "reconcile_residual": residual,
            "max_contribution_gap": gap,
        }
    )
    monthly = []
    for m, month_end in enumerate(month_ends):
        row = {"month_end": month_end.isoformat(), "portfolio_return": float(portfolio[m])}
        for k, factor_id in enumerate(ids):
            row[f"{factor_id}.return"] = float(sleeves[m, k])
            row[f"{factor_id}.contribution"] = float(contributions[m, k])
        row["drawdown"] = float(depth[m])
        monthly.append(row)
    return {
        "inputs": [
            {"factor_id": b["factor_id"], "build_id": b["build_id"], "series_sha256": b["series_sha256"]}
            for b in sorted(builds, key=lambda b: b["factor_id"])
        ],
        "weights": {i: weights[i] for i in ids},
        "span": {
            "first": panel.dates[ends[0]].isoformat(),
            "last": month_ends[-1].isoformat(),
            "common_first": panel.dates[0].isoformat(),
            "common_last": panel.dates[-1].isoformat(),
            "months": len(month_ends),
        },
        "omitted_dates": dict(panel.omitted_dates),
        "portfolio": portfolio_record,
        "sleeves": sleeve_record,
        "correlation": {"order": ids, "matrix": correlation.tolist()},
        "monthly": monthly,
    }


def _monthly_csv(rows: Sequence[Mapping], ids: Sequence[str]) -> bytes:
    header = ["month_end", "portfolio_return"]
    for i in ids:
        header += [f"{i}.return", f"{i}.contribution"]
    header.append("drawdown")
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(str(row[h]) if h == "month_end" else repr(row[h]) for h in header))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _write(path: Path, data: bytes) -> str:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    path.chmod(0o600)
    return hashlib.sha256(data).hexdigest()


def run(build_dirs: Sequence[Path], weights: Mapping[str, float], out: Path) -> dict:
    out = _check_outside_repo(Path(out), "--out")
    result = analyse([load_build(d) for d in build_dirs], weights)
    rows = result.pop("monthly")
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    out.chmod(0o700)
    analytics = (json.dumps(result, sort_keys=True, indent=1) + "\n").encode("utf-8")
    return {
        "months": result["span"]["months"],
        "sleeves": len(result["sleeves"]),
        "analytics_sha256": _write(out / "analytics.json", analytics),
        "monthly_sha256": _write(out / "monthly.csv", _monthly_csv(rows, sorted(result["sleeves"]))),
    }


def _parse_weights(items: Sequence[str]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for item in items:
        factor_id, sep, text = item.rpartition("=")
        if not sep or not factor_id:
            raise ValueError("--weight must be FACTOR_ID=WEIGHT")
        if factor_id in weights:
            raise ValueError("a factor id is weighted twice")
        try:
            weights[factor_id] = float(text)
        except ValueError as exc:
            raise ValueError("a weight is not a number") from exc
    return weights


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="append", required=True, type=Path)
    parser.add_argument("--weight", action="append", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        summary = run(args.build, _parse_weights(args.weight), args.out)
    except (ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"months: {summary['months']}")
    print(f"sleeves: {summary['sleeves']}")
    print(f"analytics.json sha256: {summary['analytics_sha256']}")
    print(f"monthly.csv sha256: {summary['monthly_sha256']}")
    print("contributions reconcile: yes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
