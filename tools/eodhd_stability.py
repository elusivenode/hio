"""EODHD stability (OD-0194, docs/evidence/e0002/stability-1.md): one snapshot against an earlier one.

Over the first snapshot's span, per fund: raw closes, distributions and splits changed, removed or added;
missing weekdays; the new dates after the span; and the return impact, built with `eodhd_eval.analyse` (HIO's
market-price total return), not re-implemented here. Stdout holds counts, impacts and the reading only. Values
go to reports/stability-<stamp>/ under --root, for the owner. Stability is not accuracy.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import eodhd_eval as ev

THRESHOLD = Decimal("0.0001")  # 0.01 points, as a fraction
STABLE = "stable"
CHANGES = "changes found"
UNEXPLAINED = "revisions not explained"
COUNT_KEYS = {
    "closes": ("changed", "removed", "added_inside"),
    "distributions": ("changed", "removed", "added", "payment_date_changed"),
    "splits": ("changed", "removed", "added"),
}
ROW_FIELDS = ("symbol", "kind", "date", "first", "second")


def _day(row: Mapping[str, Any]) -> date:
    return date.fromisoformat(str(row["date"]))


def _diff(
    old: Mapping[date, Any], new: Mapping[date, Any], kind: str, symbol: str, added_name: str
) -> tuple[dict[str, int], list[tuple[str, str, str, str, str]]]:
    rows = []
    for d in sorted(old.keys() | new.keys()):
        if d in old and d in new:
            if old[d] != new[d]:
                rows.append((symbol, f"{kind}_changed", d.isoformat(), str(old[d]), str(new[d])))
        elif d in old:
            rows.append((symbol, f"{kind}_removed", d.isoformat(), str(old[d]), ""))
        else:
            rows.append((symbol, f"{kind}_{added_name}", d.isoformat(), "", str(new[d])))
    counts = {
        "changed": sum(1 for r in rows if r[1].endswith("_changed")),
        "removed": sum(1 for r in rows if r[1].endswith("_removed")),
        added_name: sum(1 for r in rows if r[1].endswith(f"_{added_name}")),
    }
    return counts, rows


def _missing_weekdays(days: set[date], start: date, end: date) -> int:
    span = (end - start).days + 1
    return sum(1 for n in range(span) if (d := start + timedelta(days=n)).weekday() < 5 and d not in days)


def _impact(
    symbol: str,
    eod: tuple[Sequence[Mapping[str, Any]], Sequence[Mapping[str, Any]]],
    div: tuple[Sequence[Mapping[str, Any]], Sequence[Mapping[str, Any]]],
    splits: tuple[Sequence[Mapping[str, Any]], Sequence[Mapping[str, Any]]],
    start: date,
    end: date,
) -> dict[str, str]:
    """Each snapshot's period returns over the span, from eodhd_eval's own construction."""
    inside = [[r for r in rows if start <= _day(r) <= end] for rows in (*eod, *div, *splits)]
    series = []
    for e, d, s in ((inside[0], inside[2], inside[4]), (inside[1], inside[3], inside[5])):
        built = ev.analyse(symbol, ev.ETFS[symbol], ev.ETFS[symbol], e, d, s)
        if not built.periods:
            raise ev.Stop(f"{symbol}: the series could not be built over the common span")
        series.append(built.periods)
    wealth = []
    for periods in series:
        total = Decimal(1)
        for p in periods:
            total = ev.CTX.multiply(total, ev.CTX.add(Decimal(1), p.total_return))
        wealth.append(total)
    by_end = [{p.end: p.total_return for p in periods} for periods in series]
    common = by_end[0].keys() & by_end[1].keys()
    largest = max((abs(by_end[1][e] - by_end[0][e]) for e in common), default=Decimal(0))
    difference = wealth[1] - wealth[0]
    return {
        "compounded_difference": str(difference) if difference else "0",
        "largest_period_difference": str(largest) if largest else "0",
    }


def _compare_one(root: Path, first: Mapping, second: Mapping, symbol: str) -> tuple[dict, list]:
    eods = [ev._read(root, m, symbol, "eod") for m in (first, second)]
    divs = [ev._read(root, m, symbol, "div") for m in (first, second)]
    spl = [ev._read(root, m, symbol, "splits") for m in (first, second)]
    if not eods[0]:
        raise ev.Stop(f"{symbol}: the first snapshot has no closes")
    first_days = {_day(r) for r in eods[0]}
    start, end = min(first_days), max(first_days)

    def within(rows: Sequence[Mapping[str, Any]], field: str) -> dict[date, Any]:
        return {_day(r): r.get(field) for r in rows if start <= _day(r) <= end}

    closes, rows = _diff(*(within(e, "close") for e in eods), "close", symbol, "added_inside")
    d_old, d_new = (within(d, "unadjustedValue") for d in divs)
    dists, d_rows = _diff(d_old, d_new, "distribution", symbol, "added")
    p_old, p_new = (within(d, "paymentDate") for d in divs)
    moved = {d for d in p_old.keys() & p_new.keys() if p_old[d] != p_new[d]}
    for d in sorted(moved):
        d_rows.append((symbol, "distribution_payment_date", d.isoformat(), str(p_old[d]), str(p_new[d])))
    dists["payment_date_changed"] = len(moved)
    splits, s_rows = _diff(*(within(s, "split") for s in spl), "split", symbol, "added")
    second_days = {_day(r) for r in eods[1]}
    result = {
        "closes": {
            "changed": closes["changed"],
            "removed": closes["removed"],
            "added_inside": closes["added_inside"],
        },
        "distributions": dists,
        "splits": splits,
        "missing_weekdays": {
            "first": _missing_weekdays(first_days, start, end),
            "second": _missing_weekdays(second_days, start, end),
        },
        "new_after": sum(1 for d in second_days if d > end),
        "return_impact": _impact(symbol, tuple(eods), tuple(divs), tuple(spl), start, end),
    }
    return result, rows + d_rows + s_rows


def compare_with_rows(
    root: Path, first: str, second: str, symbols: Sequence[str]
) -> tuple[dict[str, dict], list[tuple[str, str, str, str, str]]]:
    unknown = [s for s in symbols if s not in ev.ETFS]
    if unknown or not symbols:
        raise ev.Stop("--symbols must name funds this evaluation covers")
    manifests = [ev.load_snapshot(root, name) for name in (first, second)]
    results, rows = {}, []
    for symbol in symbols:
        results[symbol], more = _compare_one(root, manifests[0], manifests[1], symbol)
        rows += more
    return results, rows


def compare(root: Path, first: str, second: str, symbols: Sequence[str]) -> dict[str, dict]:
    return compare_with_rows(root, first, second, symbols)[0]


def reading(results: Mapping[str, Mapping[str, Any]]) -> str:
    """The fixed table. A cause can't be automated: a changed series reads as "changes found", or, if the
    compounded difference is 0.01 points or more, "revisions not explained"."""
    changed = any(r[part][k] > 0 for r in results.values() for part, keys in COUNT_KEYS.items() for k in keys)
    if not changed:
        return STABLE
    impact = max(abs(Decimal(r["return_impact"]["compounded_difference"])) for r in results.values())
    return UNEXPLAINED if impact >= THRESHOLD else CHANGES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.home() / ".hio-research" / "E-0002-eodhd")
    parser.add_argument("--first", default="s2")
    parser.add_argument("--second", default="s3")
    parser.add_argument("--symbols", nargs="+", default=["SPY.US", "IEF.US", "BIL.US"])
    args = parser.parse_args(argv)
    try:
        ev.check_root(args.root)
        results, rows = compare_with_rows(args.root, args.first, args.second, args.symbols)
        verdict = reading(results)
        out = args.root / "reports" / f"stability-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        out.mkdir(parents=True, mode=0o700, exist_ok=True)
        document = {"first": args.first, "second": args.second, "results": results, "reading": verdict}
        ev.private_write(
            out / "stability.json", (json.dumps(document, indent=1, sort_keys=True) + "\n").encode()
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(ROW_FIELDS)
        writer.writerows(rows)
        ev.private_write(out / "changes.csv", buffer.getvalue().encode())
        print(json.dumps(document, indent=1, sort_keys=True))  # counts and impacts only
    except Exception as exc:  # the type only: a message could hold a value
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
