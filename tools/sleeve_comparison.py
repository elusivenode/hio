"""Side-by-side comparison of funded total-return sleeves against cash (OD-0220, T-0024 package A4).

Each input is a build directory (`series.csv` and `build.json`, the shared format written by
`tools/factor_build.py`). Two or more sleeves and one cash build are described in one numeraire on their
common complete months: the calculation conventions are those of `hio.portfolio.fixed_allocation` (months
between the last common dates of consecutive calendar months, first and last periods dropped, volatility ddof
1 times sqrt(12), geometric return on 365.25 days). It describes the returns it is given: no forecast,
optimisation or recommendation.

Only funded total-return series are accepted (RA-INV-015). Excess over cash is the arithmetic monthly
`X_m = R_m - r_m` (RA §3.3). It is summarised (mean times 12, volatility) and never chained into an index
(RA-INV-016).

The currency split (`--fx-split`) compounds the `foreign_return` and `spot_return` columns of an unhedged
build's `decomposition.csv` between the same month boundaries. It refuses unless `(1 + F)(1 + S) - 1`
equals the sleeve's month return within 1e-9. The variance of the month return is split into four fractions
of `var(R)`: foreign, spot, twice the covariance, and the remainder, which is what is left and is reported,
never forced to zero.

Uncertainty: circular blocks of whole months, the same rows for every series, seeded. Intervals are the 2.5th
and 97.5th percentiles of the resampled statistic, with the observed estimate (on a monthly basis, as
`fixed_allocation._summaries`). They are conditional on this history: resampling can't create independent
crises that did not occur. A difference interval carries `spans_zero`.

The command prints counts and hashes only, never a return, rate, correlation or date.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Context, Decimal, InvalidOperation
from itertools import combinations, pairwise
from pathlib import Path

import numpy as np

from hio.portfolio import fixed_allocation as fa

_spec = importlib.util.spec_from_file_location(
    "_portfolio_analytics_for_sleeves", Path(__file__).with_name("portfolio_analytics.py")
)
assert _spec is not None and _spec.loader is not None
pa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pa)

DECOMPOSITION_HEADER = [
    "period_start",
    "period_end",
    "foreign_return",
    "spot_return",
    "cross_term",
    "total_return",
]
MIN_MONTHS = 24
IDENTITY_LIMIT = 1e-9
CASH = "cash"
_CTX = Context(prec=50)


def load_build(directory: Path) -> dict:
    """A verified build (see `portfolio_analytics.load_build`) plus its resolved `directory`."""
    resolved = pa._check_outside_repo(Path(directory), "a build directory")
    return {**pa.load_build(resolved), "directory": resolved}


def _check_builds(sleeves: Sequence[Mapping], cash: Mapping, split: Sequence[str]) -> None:
    if len(sleeves) < 2:
        raise ValueError("at least two sleeves are needed")
    everything = [*sleeves, cash]
    ids = [b["factor_id"] for b in everything]
    if len(set(ids)) != len(ids):
        raise ValueError("factor ids are not distinct")
    for b in everything:
        if b["series_class"] != "total_return":
            raise ValueError(
                f"{b['factor_id']} is {b['series_class']}: only funded total_return series are accepted "
                "(RA-INV-015: funded and excess forms are not mixed)"
            )
        invariants = b["invariants"]
        if not invariants or not all(v.get("passed") is True for v in invariants.values()):
            raise ValueError(f"{b['factor_id']} has an invariant that did not pass")
    if len({b["numeraire"] for b in everything}) != 1:
        raise ValueError("the builds do not share one numeraire")
    given = {b["factor_id"] for b in sleeves}
    if len(set(split)) != len(split):
        raise ValueError("a factor id is named twice in --fx-split")
    for factor_id in split:
        if factor_id not in given:
            raise ValueError(f"--fx-split {factor_id} is not one of the given sleeves")


def monthly_panel(sleeves: Sequence[Mapping], cash: Mapping) -> dict:
    """One panel over all sleeves and cash: monthly returns (columns in the order given, cash last) and the
    common-date levels within the kept span."""
    ids = [b["factor_id"] for b in sleeves]
    if len({*ids, cash["factor_id"]}) != len(ids) + 1:
        raise ValueError("factor ids are not distinct")
    series = {b["factor_id"]: b["intervals"] for b in sleeves}
    series[cash["factor_id"]] = cash["intervals"]
    panel = fa.align(series)
    order = [panel.sleeves.index(name) for name in [*ids, cash["factor_id"]]]
    ends = fa.period_ends(panel.dates, "monthly")
    if len(ends) < 2:
        raise ValueError("fewer than one complete month in the common span")
    levels = fa.sleeve_levels(panel)[:, order]
    returns = fa.period_returns(panel.dates, levels, "monthly")
    first, last = ends[0], ends[-1]
    return {
        "ids": ids,
        "cash_id": cash["factor_id"],
        "returns": returns,
        "boundaries": [panel.dates[i] for i in ends],
        "month_ends": [panel.dates[i] for i in ends[1:]],
        "level_dates": list(panel.dates[first : last + 1]),
        "levels": levels[first : last + 1],
        "common_first": panel.dates[0],
        "common_last": panel.dates[-1],
        "omitted_dates": dict(panel.omitted_dates),
    }


def _days(panel: Mapping) -> int:
    return (panel["boundaries"][-1] - panel["boundaries"][0]).days


def _annualised(column: np.ndarray, days: int) -> float:
    return float(np.prod(1 + column) ** (fa.DAYS_PER_YEAR / days) - 1)


def _std(x: np.ndarray) -> float:
    return float(np.std(x, ddof=1))


def _vol(x: np.ndarray) -> float:
    return fa.annualised_volatility(x, "monthly")


def _corr(a: np.ndarray, b: np.ndarray) -> float | None:
    """None where a series is constant and the correlation is undefined."""
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def sleeve_statistics(panel: Mapping) -> dict:
    """Per sleeve and for cash; excess over cash for each sleeve."""
    returns, days = panel["returns"], _days(panel)
    names = [*panel["ids"], CASH]
    cash = returns[:, -1]
    cash_annual = _annualised(cash, days)
    out: dict[str, dict] = {}
    for k, name in enumerate(names):
        column = returns[:, k]
        worst, best = int(np.argmin(column)), int(np.argmax(column))
        entry = {
            "annualised_return": _annualised(column, days),
            "annualised_volatility": _vol(column),
            "drawdown": pa._describe_drawdown(fa.drawdown(panel["level_dates"], panel["levels"][:, k])),
            "worst_month": {
                "month_end": panel["month_ends"][worst].isoformat(),
                "return": float(column[worst]),
            },
            "best_month": {"month_end": panel["month_ends"][best].isoformat(), "return": float(column[best])},
        }
        if k < len(panel["ids"]):
            excess = column - cash
            entry["excess_over_cash"] = {
                "mean_annual": float(excess.mean() * 12),
                "volatility": _vol(excess),
                "return_difference": entry["annualised_return"] - cash_annual,
            }
        out[name] = entry
    return {"sleeves": {n: out[n] for n in panel["ids"]}, "cash": out[CASH]}


def pair_statistics(panel: Mapping) -> list[dict]:
    returns, days = panel["returns"], _days(panel)
    excess = returns[:, :-1] - returns[:, -1:]
    out = []
    for i, j in combinations(range(len(panel["ids"])), 2):
        out.append(
            {
                "first": panel["ids"][i],
                "second": panel["ids"][j],
                "correlation": _corr(returns[:, i], returns[:, j]),
                "excess_correlation": _corr(excess[:, i], excess[:, j]),
                "return_difference": _annualised(returns[:, j], days) - _annualised(returns[:, i], days),
                "difference_volatility": _vol(returns[:, j] - returns[:, i]),
            }
        )
    return out


def load_decomposition(build: Mapping) -> list[tuple[date, date, Decimal, Decimal]]:
    """Rows (start, end, foreign, spot) of a verified `decomposition.csv`."""
    factor_id = build["factor_id"]
    expected = build.get("decomposition_sha256")
    path = Path(build["directory"]) / "decomposition.csv"
    if not expected or not path.is_file():
        raise ValueError(f"{factor_id} has no decomposition.csv to split")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"decomposition.csv of {factor_id} does not match its recorded sha256")
    rows = list(csv.reader(raw.decode("utf-8").splitlines()))
    if not rows or rows[0] != DECOMPOSITION_HEADER:
        raise ValueError(f"decomposition.csv of {factor_id} has an unexpected header")
    out = []
    try:
        for row in rows[1:]:
            if len(row) != len(DECOMPOSITION_HEADER):
                raise ValueError("a row has the wrong number of fields")
            foreign, spot = Decimal(row[2]), Decimal(row[3])
            if not (foreign.is_finite() and spot.is_finite()):
                raise ValueError("a return is not finite")
            out.append((date.fromisoformat(row[0]), date.fromisoformat(row[1]), foreign, spot))
    except (ValueError, InvalidOperation) as exc:
        raise ValueError(f"decomposition.csv of {factor_id} is malformed: {exc}") from exc
    for a, b in pairwise(out):
        if a[1] != b[0]:
            raise ValueError(
                f"decomposition of {factor_id}: its periods don't join between {a[1]} and {b[0]}"
            )
    return out


def _compound_legs(factor_id: str, rows: Sequence[tuple], boundaries: Sequence[date]) -> tuple[list, list]:
    by_start = {r[0]: k for k, r in enumerate(rows)}
    foreign, spot = [], []
    for a, b in pairwise(boundaries):
        if a not in by_start:
            raise ValueError(f"month boundary {a} is not a decomposition boundary of {factor_id}")
        f, s, k = Decimal(1), Decimal(1), by_start[a]
        while rows[k][1] < b:
            f, s = _CTX.multiply(f, 1 + rows[k][2]), _CTX.multiply(s, 1 + rows[k][3])
            k += 1
            if k == len(rows):
                raise ValueError(f"decomposition of {factor_id} ends before {b}")
        if rows[k][1] != b:
            raise ValueError(f"month boundary {b} is not a decomposition boundary of {factor_id}")
        f, s = _CTX.multiply(f, 1 + rows[k][2]), _CTX.multiply(s, 1 + rows[k][3])
        foreign.append(float(f - 1))
        spot.append(float(s - 1))
    return foreign, spot


def fx_split(panel: Mapping, sleeves: Sequence[Mapping], split: Sequence[str]) -> tuple[dict, dict]:
    """Currency split per named sleeve. Returns the record and, per sleeve, the (F, S, C) monthly arrays."""
    returns, days = panel["returns"], _days(panel)
    record: dict[str, dict] = {}
    columns: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    by_id = {b["factor_id"]: b for b in sleeves}
    for factor_id in split:
        k = panel["ids"].index(factor_id)
        total = returns[:, k]
        rows = load_decomposition(by_id[factor_id])
        f_list, s_list = _compound_legs(factor_id, rows, panel["boundaries"])
        foreign, spot = np.array(f_list), np.array(s_list)
        gap = float(np.max(np.abs((1 + foreign) * (1 + spot) - 1 - total)))
        if gap > IDENTITY_LIMIT:
            raise ValueError(f"{factor_id}: the compounded legs differ from the series by {gap:.3g}")
        cross = total - foreign - spot
        var_total = float(np.var(total, ddof=1))
        if var_total == 0:
            raise ValueError(f"{factor_id}: the month returns have no variance to split")
        var_f, var_s = float(np.var(foreign, ddof=1)), float(np.var(spot, ddof=1))
        twice_cov = 2 * float(np.cov(foreign, spot, ddof=1)[0, 1])
        fractions = {
            "foreign": var_f / var_total,
            "spot": var_s / var_total,
            "covariance": twice_cov / var_total,
        }
        fractions["remainder"] = 1 - fractions["foreign"] - fractions["spot"] - fractions["covariance"]
        record[factor_id] = {
            "foreign_annualised_return": _annualised(foreign, days),
            "spot_annualised_return": _annualised(spot, days),
            "volatility": {"foreign": _vol(foreign), "spot": _vol(spot), "total": _vol(total)},
            "correlation_foreign_spot": _corr(foreign, spot),
            "variance_split": fractions,
            "spot_correlation_with": {
                other: _corr(spot, returns[:, m])
                for m, other in enumerate(panel["ids"])
                if other != factor_id
            },
            "max_identity_gap": gap,
            "max_abs_cross_term": float(np.max(np.abs(cross))),
        }
        columns[factor_id] = (foreign, spot, cross)
    return record, columns


def _rows(months: int, block: int, replications: int, seed: int) -> np.ndarray:
    """The same circular-block rows as `fa.paired_block_bootstrap` draws for the same arguments."""
    rng = np.random.default_rng(seed)
    blocks = months // block + 1
    starts = rng.integers(0, months, size=(replications, blocks))
    return (starts[:, :, None] + np.arange(block)).reshape(replications, -1)[:, :months] % months


def _band(estimate: float | None, draws: np.ndarray) -> dict:
    finite = draws[np.isfinite(draws)]
    if estimate is None or not finite.size:
        return {"estimate": None, "low": None, "high": None}
    return {
        "estimate": float(estimate),
        "low": float(np.percentile(finite, 2.5)),
        "high": float(np.percentile(finite, 97.5)),
    }


def _difference(interval: fa.BootstrapInterval) -> dict:
    return {
        "estimate": interval.estimate,
        "low": interval.low,
        "high": interval.high,
        "spans_zero": bool(interval.low <= 0 <= interval.high),
    }


def intervals(
    returns: np.ndarray,
    ids: Sequence[str],
    *,
    blocks: Sequence[int],
    replications: int,
    seed: int,
) -> dict:
    """95% block-bootstrap intervals. `returns` has one column per sleeve (in `ids`) then cash."""
    months, count = returns.shape[0], len(ids)
    sleeves = returns[:, :count]
    out = {}
    for block in blocks:
        rows = _rows(months, block, replications, seed)
        sampled = returns[rows]
        per_sleeve = {}
        for k, name in enumerate(ids):
            vol, growth, _ = fa._summaries(sampled[:, :, k])
            o_vol, o_growth, _ = fa._summaries(returns[None, :, k])
            excess = (returns[:, k] - returns[:, -1]).mean() * 12
            drawn = (sampled[:, :, k] - sampled[:, :, -1]).mean(axis=1) * 12
            per_sleeve[name] = {
                "annualised_return": _band(o_growth[0], growth),
                "volatility": _band(o_vol[0], vol),
                "mean_annual_excess": _band(excess, drawn),
            }
        pairs = []
        for i, j in combinations(range(count), 2):
            a = sampled[:, :, i] - sampled[:, :, i].mean(axis=1, keepdims=True)
            b = sampled[:, :, j] - sampled[:, :, j].mean(axis=1, keepdims=True)
            with np.errstate(divide="ignore", invalid="ignore"):
                drawn = (a * b).sum(axis=1) / np.sqrt((a * a).sum(axis=1) * (b * b).sum(axis=1))
            unit = np.eye(count)
            paired = fa.paired_block_bootstrap(
                sleeves, unit[i], unit[j], block_months=block, replications=replications, seed=seed
            )
            pairs.append(
                {
                    "first": ids[i],
                    "second": ids[j],
                    "correlation": _band(_corr(returns[:, i], returns[:, j]), drawn),
                    "volatility_difference": _difference(paired.volatility),
                    "return_difference": _difference(paired.annualised_return),
                    "drawdown_difference": _difference(paired.max_drawdown),
                }
            )
        out[str(block)] = {"sleeves": per_sleeve, "pairs": pairs}
    return out


def compare(
    sleeves: Sequence[Mapping],
    cash: Mapping,
    split: Sequence[str] = (),
    *,
    blocks: Sequence[int] = (3, 6, 12),
    replications: int = 2000,
    seed: int = 20261122,
) -> dict:
    """The comparison record. `monthly_columns` and `monthly` hold monthly.csv and are not part of
    comparison.json."""
    _check_builds(sleeves, cash, split)
    panel = monthly_panel(sleeves, cash)
    months = panel["returns"].shape[0]
    if months < MIN_MONTHS:
        raise ValueError(f"{months} complete common months; at least {MIN_MONTHS} are needed")
    for block in blocks:
        if not 1 <= block <= months:
            raise ValueError(f"a block of {block} months doesn't fit {months} months")
    if replications < 1:
        raise ValueError("at least one replication")
    stats = sleeve_statistics(panel)
    split_record, split_columns = fx_split(panel, sleeves, split)

    header = ["month_end", *panel["ids"], CASH]
    for factor_id in split:
        header += [f"{factor_id}.foreign", f"{factor_id}.spot", f"{factor_id}.cross"]
    monthly = []
    for m, month_end in enumerate(panel["month_ends"]):
        row = {"month_end": month_end.isoformat()}
        row.update({name: float(panel["returns"][m, k]) for k, name in enumerate([*panel["ids"], CASH])})
        for factor_id, (f, s, c) in split_columns.items():
            row[f"{factor_id}.foreign"], row[f"{factor_id}.spot"], row[f"{factor_id}.cross"] = (
                float(f[m]),
                float(s[m]),
                float(c[m]),
            )
        monthly.append(row)

    inputs = []
    for b in sleeves:
        item = {"factor_id": b["factor_id"], "build_id": b["build_id"], "series_sha256": b["series_sha256"]}
        if b["factor_id"] in split:
            item["decomposition_sha256"] = b["decomposition_sha256"]
        inputs.append(item)
    return {
        "inputs": {
            "sleeves": inputs,
            "cash": {
                "factor_id": cash["factor_id"],
                "build_id": cash["build_id"],
                "series_sha256": cash["series_sha256"],
            },
        },
        "span": {
            "first": panel["boundaries"][0].isoformat(),
            "last": panel["boundaries"][-1].isoformat(),
            "common_first": panel["common_first"].isoformat(),
            "common_last": panel["common_last"].isoformat(),
            "months": months,
        },
        "omitted_dates": panel["omitted_dates"],
        "settings": {"blocks": list(blocks), "replications": replications, "seed": seed},
        "sleeves": stats["sleeves"],
        "cash": stats["cash"],
        "pairs": pair_statistics(panel),
        "fx_split": split_record,
        "intervals": intervals(
            panel["returns"], panel["ids"], blocks=blocks, replications=replications, seed=seed
        ),
        "monthly_columns": header,
        "monthly": monthly,
    }


def _monthly_csv(rows: Sequence[Mapping], header: Sequence[str]) -> bytes:
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(str(row[h]) if h == "month_end" else repr(row[h]) for h in header))
    return ("\n".join(lines) + "\n").encode("utf-8")


def run(
    sleeve_dirs: Sequence[Path],
    cash_dir: Path,
    split: Sequence[str],
    out: Path,
    *,
    blocks: Sequence[int],
    replications: int,
    seed: int,
) -> dict:
    out = pa._check_outside_repo(Path(out), "--out")
    result = compare(
        [load_build(d) for d in sleeve_dirs],
        load_build(cash_dir),
        split,
        blocks=blocks,
        replications=replications,
        seed=seed,
    )
    rows, header = result.pop("monthly"), result.pop("monthly_columns")
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    out.chmod(0o700)
    body = (json.dumps(result, sort_keys=True, indent=1, allow_nan=False) + "\n").encode("utf-8")
    return {
        "months": result["span"]["months"],
        "sleeves": len(result["sleeves"]),
        "split": len(result["fx_split"]),
        "comparison_sha256": pa._write(out / "comparison.json", body),
        "monthly_sha256": pa._write(out / "monthly.csv", _monthly_csv(rows, header)),
    }


def _parse_blocks(text: str) -> list[int]:
    try:
        blocks = [int(part) for part in text.split(",")]
    except ValueError as exc:
        raise ValueError("--blocks must be comma-separated whole numbers") from exc
    if not blocks:
        raise ValueError("--blocks is empty")
    return blocks


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sleeve", action="append", required=True, type=Path)
    parser.add_argument("--cash", required=True, type=Path)
    parser.add_argument("--fx-split", action="append", default=[])
    parser.add_argument("--blocks", default="3,6,12")
    parser.add_argument("--replications", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261122)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        summary = run(
            args.sleeve,
            args.cash,
            args.fx_split,
            args.out,
            blocks=_parse_blocks(args.blocks),
            replications=args.replications,
            seed=args.seed,
        )
    except (ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"months: {summary['months']}")
    print(f"sleeves: {summary['sleeves']}")
    print(f"split sleeves: {summary['split']}")
    print(f"comparison.json sha256: {summary['comparison_sha256']}")
    print(f"monthly.csv sha256: {summary['monthly_sha256']}")
    print("identities hold: yes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
