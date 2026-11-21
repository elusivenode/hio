"""E-0004 step 2 (OD-0191, preregistration "Step 2", "Decision rule", "Sensitivities"): the estimate.

One run: the point difference between accelerating and other periods in the benefit `b`, its circular
moving-block bootstrap interval (12-month primary; 6 and 24 as checks), the cluster-fragility deltas and
four sensitivities. The reading follows the decision rule exactly. Output is result.json under a new
directory and stdout; exit 2 on any refusal.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import e0004_info as info
import e0004_precision as prec
import eodhd_eval as ev
import t0023_common as common

ACCELERATING = prec.ACCELERATING
NOT = prec.NOT
UNAVAILABLE = prec.UNAVAILABLE
REPS = 10_000
SEED = 20260004
BLOCK = 12
THRESHOLD = 0.0020
PERSISTENCE_N = 3
STRESS_END = date(2008, 9, 30)
EODHD_MANIFEST_SHA = prec.EODHD_MANIFEST_SHA
CPI_MANIFEST_SHA = prec.CPI_MANIFEST_SHA
NOT_DISTINGUISHED = "not distinguished"
RELEVANT = "relevant state-dependent difference"
UNCERTAIN = "nonzero difference of uncertain relevance"


def estimate(
    b: Sequence[float], states: Sequence[str], *, block: int, reps: int = REPS, seed: int = SEED
) -> dict[str, Any]:
    """Point difference, the 2.5/97.5 interval and the number of dropped replications."""
    point = prec.delta(b, states)
    if point is None:
        raise ValueError("a state has no period")
    deltas, dropped = prec.bootstrap(b, states, block=block, reps=reps, seed=seed)
    if len(deltas) == 0:
        raise ValueError("every replication was dropped")
    lo, hi = prec.interval(deltas)
    return {"point": point, "lo": lo, "hi": hi, "dropped": dropped}


def fragility(
    b: Sequence[float], states: Sequence[str], clusters: Sequence[Sequence[int]]
) -> list[float | None]:
    """The point difference with each cluster's periods marked unavailable in turn."""
    out: list[float | None] = []
    for cluster in clusters:
        marked = list(states)
        for i in cluster:
            marked[i] = UNAVAILABLE
        out.append(prec.delta(b, marked))
    return out


def reading(
    lo: float, hi: float, frag: Sequence[float | None], point: float, threshold: float = THRESHOLD
) -> str:
    """The decision rule's three outcomes."""
    if lo <= 0 <= hi:
        return NOT_DISTINGUISHED
    beyond = lo > threshold or hi < -threshold
    fragile = any(f is None or f == 0 or f * point < 0 for f in frag)
    if beyond and not fragile:
        return RELEVANT
    return UNCERTAIN


def persistence(states: Sequence[str], n: int = PERSISTENCE_N) -> list[str]:
    """The state switches only once n consecutive available periods show the other raw state.

    It starts at the first available raw state. The nth such period already carries the new state.
    Unavailable periods pass through unchanged and neither count toward nor break a pending switch.
    """
    out: list[str] = []
    current: str | None = None
    run = 0
    for raw in states:
        if raw == UNAVAILABLE:
            out.append(raw)
            continue
        if current is None:
            current = raw
        elif raw == current:
            run = 0
        else:
            run += 1
            if run >= n:
                current = raw
                run = 0
        out.append(current)
    return out


def summarise(
    b: Sequence[float], states: Sequence[str], spy: Sequence[float], *, block: int
) -> dict[str, Any]:
    est = estimate(b, states, block=block)
    frag = fragility(b, states, info.clusters(states, spy))
    return {**est, "reading": reading(est["lo"], est["hi"], frag, est["point"])}


def sensitivity(b: Sequence[float], states: Sequence[str], spy: Sequence[float]) -> dict[str, Any]:
    out = summarise(b, states, spy, block=BLOCK)
    return {k: out[k] for k in ("point", "lo", "hi", "reading")}


def v1_overlap(
    periods: Sequence[tuple[date, date, Any]], month_ends: Sequence[date]
) -> tuple[int, int] | None:
    """First and last panel month-end index inside V1's coverage, or None if fewer than two."""
    first = min(p[0] for p in periods)
    last = max(p[1] for p in periods)
    inside = [i for i, m in enumerate(month_ends) if first <= m <= last]
    if len(inside) < 2:
        return None
    return inside[0], inside[-1]


def main(argv: list[str] | None = None) -> int:
    import e0004_state as state_tool  # here only
    import t0023_sleeves as sleeves

    parser = argparse.ArgumentParser(description=__doc__)
    research = Path.home() / ".hio-research"
    parser.add_argument("--t0023-root", type=Path, default=research / "T-0023")
    parser.add_argument("--cpi-raw", type=Path, default=research / "E-0004" / "raw")
    parser.add_argument("--runs", type=Path, default=research / "E-0004" / "runs")
    parser.add_argument("--e0001", type=Path, default=research / "E-0001")
    args = parser.parse_args(argv)
    try:
        ev.check_root(args.t0023_root)
        panel, run_dir = common.load_frozen(args.t0023_root)
        record = json.loads((run_dir / "run.json").read_text())
        if record["inputs"]["eodhd_snapshot"]["files"]["manifest.json"] != EODHD_MANIFEST_SHA:
            raise ev.Stop("the frozen run's snapshot manifest isn't the pinned one")
        if prec.file_sha256(args.cpi_raw / "manifest.json") != CPI_MANIFEST_SHA:
            raise ev.Stop("the CPI manifest isn't the pinned one")
        cpi = state_tool.load_cpi(args.cpi_raw / "cu.data.1.AllItems.txt")
        releases = state_tool.load_releases(args.cpi_raw / "release-dates.csv")
        month_ends = list(panel.months)
        usd = common.usd_columns(panel)
        spy = [float(x) for x in usd["equity"]]
        ief = [float(x) for x in usd["treasury"]]
        bil = [float(x) for x in usd["bills"]]
        states = state_tool.states(month_ends, releases, cpi)
        b = prec.benefit(spy, ief, bil)

        primary = summarise(b, states, spy, block=BLOCK)
        blocks = {str(k): summarise(b, states, spy, block=k) for k in (6, 24)}
        clusters = info.clusters(states, spy)
        frag = fragility(b, states, clusters)
        sens: dict[str, Any] = {}

        equal = state_tool.states(month_ends, releases, cpi, equal_is_accelerating=True)
        sens["equal_is_accelerating"] = sensitivity(b, equal, spy)

        periods, _ = sleeves.load_v1(args.e0001)
        span = v1_overlap(periods, month_ends)
        if span is None:
            sens["v1_ten_year"] = {"overlap": None}
        else:
            i0, i1 = span
            v1 = [float(x) for x in sleeves.compound_months(periods, month_ends[i0 : i1 + 1])]
            ief_v1 = [0.0] * i0 + v1 + [0.0] * (len(states) - i1)
            keep = [UNAVAILABLE if not i0 <= i < i1 else s for i, s in enumerate(states)]
            b_v1 = prec.benefit(spy, ief_v1, bil)
            sens["v1_ten_year"] = {
                **sensitivity(b_v1, keep, spy),
                "overlap_first": month_ends[i0].isoformat(),
                "overlap_last": month_ends[i1].isoformat(),
            }

        sens["persistence_3"] = sensitivity(b, persistence(states, PERSISTENCE_N), spy)

        ends = [i for i in range(len(states)) if month_ends[i + 1] == STRESS_END]
        if len(ends) != 1:
            raise ev.Stop("no unique period ends 2008-09-30")
        dropped_one = list(states)
        dropped_one[ends[0]] = UNAVAILABLE
        sens["without_2008_09_30"] = sensitivity(b, dropped_one, spy)

        result = {
            "n": {s: sum(1 for x in states if x == s) for s in (ACCELERATING, NOT, UNAVAILABLE)},
            "primary": {"block": BLOCK, **primary},
            "blocks": blocks,
            "block_disagreement": any(v["reading"] != primary["reading"] for v in blocks.values()),
            "fragility": [
                {"first": month_ends[c[0]].isoformat(), "last": month_ends[c[-1] + 1].isoformat(), "delta": f}
                for c, f in zip(clusters, frag, strict=True)
            ],
            "sensitivities": sens,
        }
        commit = ev.code_commit()["commit"]
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out = args.runs / f"{stamp}-{commit[:8]}"
        out.mkdir(mode=0o700, parents=True)
        text = json.dumps({"code": commit, **result}, indent=1, sort_keys=True) + "\n"
        ev.private_write(out / "result.json", text.encode())
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
