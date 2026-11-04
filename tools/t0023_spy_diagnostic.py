"""Why C5 failed for SPY (T-0023, OD-0179). Post hoc: declared after the failure, and it changes no bar.

The audited return is at NAV, and HIO's at the close. If that's the whole gap, SPY's NAV return, from the
issuer's NAV and EODHD's distributions, should land near the audited figure, and the close's premium to NAV at
each fiscal boundary should account for what's left. Values go only to the report.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import eodhd_eval as ev
import t0023_common as common
import t0023_sleeves as sleeves
from hio.library.numeric import CTX
from hio.library.vehicle_return import VehiclePeriod


def boundary_premium(close: Decimal, nav: Decimal) -> Decimal:
    return CTX.subtract(CTX.divide(close, nav), Decimal(1))


def year_row(
    fact: Any,
    market: Sequence[VehiclePeriod],
    at_nav: Sequence[VehiclePeriod],
    closes: Mapping[date, Decimal],
    nav: Mapping[date, Decimal],
) -> dict[str, Any]:
    days = sorted(nav)
    first = sleeves.anchor(days, fact.start, before=True)
    last = sleeves.anchor(days, fact.end, before=False)
    close_return = sleeves.period_return(market, first, last) * 100
    nav_return = sleeves.period_return(at_nav, first, last) * 100
    return {
        "fiscal_end": fact.end.isoformat(),
        "audited_pct": str(fact.total_return_pct),
        "hio_close_pct": f"{close_return:.4f}",
        "hio_nav_pct": f"{nav_return:.4f}",
        "close_gap_points": f"{close_return - fact.total_return_pct:.4f}",
        "nav_gap_points": f"{nav_return - fact.total_return_pct:.4f}",
        "premium_at_start_pct": f"{boundary_premium(closes[first], nav[first]) * 100:.4f}",
        "premium_at_end_pct": f"{boundary_premium(closes[last], nav[last]) * 100:.4f}",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    research = Path.home() / ".hio-research"
    parser.add_argument("--root", type=Path, default=research / "T-0023")
    parser.add_argument("--e0002", type=Path, default=research / "E-0002-eodhd")
    args = parser.parse_args(argv)
    try:
        code = ev.code_commit()
        ev.make_gate().authorise(sleeves.Operation.BUILD, [ev.SOURCE_ID])
        manifest = ev.load_snapshot(args.e0002, "s2")
        fund = sleeves.load_funds(args.e0002, manifest)["SPY"]
        reference = args.root / "reference"
        nav = sleeves.load_nav(reference / "nav-spy.csv")
        facts = [f for f in sleeves.load_facts(reference / "audited-facts.csv") if f.symbol == "SPY"]
        if nav is None or not facts:
            raise ev.Stop("no SPY NAV or audited facts")
        at_nav, _ = sleeves.nav_periods(nav, fund.dists, fund.splits)
        rows = [year_row(f, fund.periods, at_nav, fund.closes, nav) for f in facts]
        out = common.new_output(args.root, "spy-diagnostic", code["commit"])
        lines = ["# T-0023 SPY diagnostic, post hoc. Licensed-derived: don't commit or share.", ""]
        lines += [json.dumps(r, sort_keys=True) for r in rows]
        common.write_outputs(out, "\n".join(lines) + "\n", {"code": code, "rows": rows})
    except ev.Stop as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"output": out.name, "years": len(rows)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
