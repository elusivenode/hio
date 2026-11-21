"""E-0004 step 1 (OD-0190, preregistration 1): the information count, before any outcome.

Reads the CPI state of each month and SPY's monthly USD total return only. It computes no `b`, no `D`
and no `Δ`. Counts go to counts.json and the per-period states to states.csv (no returns) under a new
output directory; stdout holds the counts. A failed screen is a result, not an error.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import eodhd_eval as ev
import t0023_common as common

STATES = ("accelerating", "not")
UNAVAILABLE = "unavailable"
STRESS = -0.05  # SPY's monthly total return at or below this is a stress month
CLUSTER_GAP = 3  # stress months with fewer than this many months between them join one cluster
MIN_MONTHS = 48
MIN_RUNS = 4
MIN_CLUSTERS = 3
MAX_CONCENTRATION = 0.5
EODHD_MANIFEST_SHA = "bb40a84650a8b7104e3d116a5d0773619dd4870ee20190a80bab370135fee38d"
CPI_MANIFEST_SHA = "bbc64011760adae3deec14dabeae850b0e8b40be94cfe6b769bda03518fdd501"


def clusters_of(states: Sequence[str], spy: Sequence[float]) -> list[list[int]]:
    """Indices of stress periods (available only), grouped in time order into clusters."""
    out: list[list[int]] = []
    last_stress: int | None = None
    for i, (state, r) in enumerate(zip(states, spy, strict=True)):
        if state == UNAVAILABLE:
            continue
        if r <= STRESS:
            joined = (
                last_stress is not None
                and i - last_stress - 1 < CLUSTER_GAP
                and UNAVAILABLE not in states[last_stress + 1 : i]
            )
            if joined:
                out[-1].append(i)
            else:
                out.append([i])
            last_stress = i
    return out


def runs_of(states: Sequence[str], state: str) -> int:
    """Maximal spells of consecutive periods in `state`."""
    count = 0
    previous = None
    for s in states:
        if s == state and previous != state:
            count += 1
        previous = s
    return count


def count(states: Sequence[str], spy: Sequence[float]) -> dict[str, Any]:
    """Per-state counts and the minimum screen. Unavailable periods are excluded and break everything."""
    if len(states) != len(spy):
        raise ValueError("states and spy must have the same length")
    unknown = sorted({s for s in states if s not in (*STATES, UNAVAILABLE)})
    if unknown:
        raise ValueError(f"unknown state: {unknown[0]}")
    clusters = clusters_of(states, spy)
    per_state: dict[str, dict[str, Any]] = {}
    for state in STATES:
        stress = sum(1 for s, r in zip(states, spy, strict=True) if s == state and r <= STRESS)
        held = [sum(1 for i in c if states[i] == state) for c in clusters]
        per_state[state] = {
            "months": sum(1 for s in states if s == state),
            "runs": runs_of(states, state),
            "stress_months": stress,
            "clusters": sum(1 for h in held if h > 0),
            "concentration": max(held) / stress if stress else 0.0,
        }
    failed = [
        f"{state}: {name}"
        for state, c in per_state.items()
        for name, ok in (
            ("months", c["months"] >= MIN_MONTHS),
            ("runs", c["runs"] >= MIN_RUNS),
            ("clusters", c["clusters"] >= MIN_CLUSTERS),
            ("concentration", c["concentration"] <= MAX_CONCENTRATION),
        )
        if not ok
    ]
    return {
        **per_state,
        "unavailable": sum(1 for s in states if s == UNAVAILABLE),
        "screen": {"pass": not failed, "failed": failed},
    }


def file_sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def states_csv(month_ends: Sequence[Any], states: Sequence[str]) -> str:
    """period_start, period_end, state. No returns."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["period_start", "period_end", "state"])
    for i, state in enumerate(states):
        writer.writerow([month_ends[i].isoformat(), month_ends[i + 1].isoformat(), state])
    return buffer.getvalue()


def main(argv: list[str] | None = None) -> int:
    import e0004_state as state_tool  # here only: the count above needs nothing else

    parser = argparse.ArgumentParser(description=__doc__)
    research = Path.home() / ".hio-research"
    parser.add_argument("--t0023-root", type=Path, default=research / "T-0023")
    parser.add_argument("--cpi-raw", type=Path, default=research / "E-0004" / "raw")
    parser.add_argument("--runs", type=Path, default=research / "E-0004" / "runs")
    args = parser.parse_args(argv)
    try:
        ev.check_root(args.t0023_root)
        panel, run_dir = common.load_frozen(args.t0023_root)
        record = json.loads((run_dir / "run.json").read_text())
        if record["inputs"]["eodhd_snapshot"]["files"]["manifest.json"] != EODHD_MANIFEST_SHA:
            raise ev.Stop("the frozen run's snapshot manifest isn't the pinned one")
        if file_sha256(args.cpi_raw / "manifest.json") != CPI_MANIFEST_SHA:
            raise ev.Stop("the CPI manifest isn't the pinned one")
        cpi = state_tool.load_cpi(args.cpi_raw / "cu.data.1.AllItems.txt")
        releases = state_tool.load_releases(args.cpi_raw / "release-dates.csv")
        month_ends = list(panel.months)
        spy = [float(x) for x in common.usd_columns(panel)["equity"]]
        states = state_tool.states(month_ends, releases, cpi)
        counts = count(states, spy)
        commit = ev.code_commit()["commit"]
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out = args.runs / f"{stamp}-{commit[:8]}"
        out.mkdir(mode=0o700, parents=True)
        text = json.dumps({"code": commit, **counts}, indent=1, sort_keys=True) + "\n"
        ev.private_write(out / "counts.json", text.encode())
        ev.private_write(out / "states.csv", states_csv(month_ends, states).encode())
    except ev.Stop as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # the type only: a message could hold a value
        print(f"stopped: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
