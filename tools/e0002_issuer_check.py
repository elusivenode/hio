"""An independent check of E-0002's three sleeves (T-0022, OD-0162): HIO's return against the issuer's.

HIO compounds its market-price total return, built from EODHD's raw closes and actions, and compares it with
the market-price returns in each fund's public fact sheet, read once into a local reference file. Pass: within
0.10 percentage points a year, declared before any comparison. Conventions differ a little (a fund's market
value may be a bid/offer midpoint, and reinvestment timing), so a small gap is expected. A pass says income is
about right in aggregate. It can't show every record is right: one small missing payment over ten years stays
inside the bar. Stdout holds counts and pass or fail; detail goes to reports/ for the owner.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import eodhd_eval as ev
from hio.contracts.rights import Operation
from hio.library.numeric import CTX

TOLERANCE_PCT = 0.10
REFERENCE = "issuer-market-returns.csv"


@dataclass(frozen=True)
class Check:
    symbol: str
    kind: str
    start: date
    end: date
    years: int
    percent: float


def load_checks(path: Path) -> list[Check]:
    return [
        Check(
            row["symbol"],
            row["kind"],
            date.fromisoformat(row["start"]),
            date.fromisoformat(row["end"]),
            int(row["years"]),
            float(row["percent"]),
        )
        for row in csv.DictReader(path.open())
    ]


def compounded(periods: Sequence[Any], start: date, end: date) -> Decimal | None:
    """The chained return between the last observed dates on or before each end. None if out of range."""
    ends = [p.end for p in periods]
    first = periods[0].start
    if start < first or end > ends[-1]:
        return None
    a = bisect_right(ends, start)
    b = bisect_right(ends, end)
    level = Decimal(1)
    for period in periods[a:b]:
        level = CTX.multiply(level, CTX.add(Decimal(1), period.total_return))
    return CTX.subtract(level, Decimal(1))


def annual_percent(total: Decimal, years: int) -> float:
    return ((1 + float(total)) ** (1 / years) - 1) * 100


def evaluate(checks: Sequence[Check], series: Mapping[str, Sequence[Any]]) -> list[dict[str, Any]]:
    out = []
    for check in checks:
        total = compounded(series[check.symbol], check.start, check.end)
        row: dict[str, Any] = {
            "symbol": check.symbol,
            "kind": check.kind,
            "end": check.end.isoformat(),
            "years": check.years,
            "issuer": check.percent,
        }
        if total is None:
            row |= {"hio": None, "passes": False, "why": "out of range"}
        else:
            hio = annual_percent(total, check.years)
            row |= {"hio": hio, "passes": abs(hio - check.percent) <= TOLERANCE_PCT}
        out.append(row)
    return out


def tally(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        counts = out.setdefault(row["symbol"], {"checks": 0, "pass": 0})
        counts["checks"] += 1
        counts["pass"] += int(row["passes"])
    return out


def render(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# E-0002 issuer check: for the owner only. Licensed-derived: don't commit, share or paste into AI.",
        "",
        f"HIO's return against the issuer's published one. Pass: within {TOLERANCE_PCT} points a year.",
        "A pass says income is about right in aggregate, not that every record is right.\n",
        "| Fund | Type | Period to | Years | Issuer % | HIO % | Gap | Pass |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        hio = "n/a" if r["hio"] is None else f"{r['hio']:.2f}"
        gap = "n/a" if r["hio"] is None else f"{r['hio'] - r['issuer']:+.2f}"
        lines.append(
            f"| {r['symbol']} | {r['kind']} | {r['end']} | {r['years']} | {r['issuer']:.2f} | {hio} | "
            f"{gap} | "
            f"{'yes' if r['passes'] else '**no**'} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.home() / ".hio-research" / "E-0002-eodhd")
    parser.add_argument("--snapshot", default="s2")
    args = parser.parse_args(argv)
    try:
        ev.check_root(args.root)
        ev.make_gate().authorise(Operation.BUILD, [ev.SOURCE_ID])
        manifest = ev.load_snapshot(args.root, args.snapshot)
        checks = load_checks(args.root / "reference" / REFERENCE)
        series = {}
        for symbol in sorted({c.symbol for c in checks}):
            built = ev.analyse(
                symbol,
                ev.ETFS[symbol],
                ev.ETFS[symbol],
                ev._read(args.root, manifest, symbol, "eod"),
                ev._read(args.root, manifest, symbol, "div"),
                ev._read(args.root, manifest, symbol, "splits"),
            )
            series[symbol] = built.periods
        rows = evaluate(checks, series)
        ev.private_write(args.root / "reports" / "owner-report-issuer.md", render(rows).encode())
        failed = [{k: r[k] for k in ("symbol", "kind", "end", "years")} for r in rows if not r["passes"]]
        print(json.dumps({"tally": tally(rows), "failed": failed}, sort_keys=True))
    except Exception as exc:
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
