"""E-0004 step 1b (OD-0190, preregistration 1): the precision check, before any outcome.

Estimates how wide the step 2 bootstrap interval for the difference would be when the state sequence is
shifted away from the real alignment. Only the median half-width is recorded. No difference, shifted or
not, no `b` value and no per-state mean is returned, printed, written or logged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

import eodhd_eval as ev
import t0023_common as common

ACCELERATING = "accelerating"
NOT = "not"
UNAVAILABLE = "unavailable"
STOCK_WEIGHT = 0.6
BOND_WEIGHT = 0.4
BLOCK = 12
REPS = 1000
SEED = 20260004
MIN_SHIFT = 13
MAX_HALF_WIDTH = 0.0020  # 0.20 percentage points
EODHD_MANIFEST_SHA = "bb40a84650a8b7104e3d116a5d0773619dd4870ee20190a80bab370135fee38d"
CPI_MANIFEST_SHA = "bbc64011760adae3deec14dabeae850b0e8b40be94cfe6b769bda03518fdd501"


def benefit(spy: Sequence[float], ief: Sequence[float], bil: Sequence[float]) -> np.ndarray:
    """Per period b = L(R_B) - L(R_T), with L(R) = max(0, -R), R_T on IEF and R_B on BIL."""
    s, i, c = (np.asarray(x, dtype=float) for x in (spy, ief, bil))
    if not (s.shape == i.shape == c.shape) or s.ndim != 1:
        raise ValueError("spy, ief and bil must be one-dimensional and the same length")
    r_t = STOCK_WEIGHT * s + BOND_WEIGHT * i
    r_b = STOCK_WEIGHT * s + BOND_WEIGHT * c
    return np.maximum(0.0, -r_b) - np.maximum(0.0, -r_t)


def delta(b: Sequence[float], states: Sequence[str]) -> float | None:
    """Mean of b in accelerating periods minus mean in the others; None if a state has no period."""
    values = np.asarray(b, dtype=float)
    if len(values) != len(states):
        raise ValueError("b and states must have the same length")
    marks = np.asarray(states)
    accelerating = values[marks == ACCELERATING]
    other = values[marks == NOT]
    if len(accelerating) == 0 or len(other) == 0:
        return None
    return float(accelerating.mean() - other.mean())


def segments(states: Sequence[str]) -> list[range]:
    """Maximal runs of available periods."""
    out: list[range] = []
    start: int | None = None
    for i, s in enumerate(states):
        if s != UNAVAILABLE and start is None:
            start = i
        elif s == UNAVAILABLE and start is not None:
            out.append(range(start, i))
            start = None
    if start is not None:
        out.append(range(start, len(states)))
    return out


def bootstrap(
    b: Sequence[float], states: Sequence[str], *, block: int, reps: int, seed: int
) -> tuple[np.ndarray, int]:
    """Circular moving-block bootstrap within segments. Returns the deltas and the dropped count."""
    values = np.asarray(b, dtype=float)
    if len(values) != len(states):
        raise ValueError("b and states must have the same length")
    if block < 1 or reps < 1:
        raise ValueError("block and reps must be positive")
    segs = segments(states)
    seg_start = np.concatenate([np.full(len(r), r.start) for r in segs]) if segs else np.empty(0, int)
    seg_len = np.concatenate([np.full(len(r), len(r)) for r in segs]) if segs else np.empty(0, int)
    available = np.concatenate([np.arange(r.start, r.stop) for r in segs]) if segs else np.empty(0, int)
    m = len(available)
    if m == 0:
        return np.empty(0), reps
    rng = np.random.default_rng(seed)
    blocks = -(-m // block)
    picks = rng.integers(0, m, size=(reps, blocks))
    start = seg_start[picks]
    length = seg_len[picks]
    offset = available[picks] - start
    steps = np.arange(block)
    index = start[:, :, None] + (offset[:, :, None] + steps) % length[:, :, None]
    index = index.reshape(reps, blocks * block)[:, :m]
    marks = np.asarray(states)[index]
    drawn = values[index]
    accelerating = marks == ACCELERATING
    other = marks == NOT
    n_a = accelerating.sum(axis=1)
    n_o = other.sum(axis=1)
    keep = (n_a > 0) & (n_o > 0)
    sum_a = np.where(accelerating, drawn, 0.0).sum(axis=1)
    sum_o = np.where(other, drawn, 0.0).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        deltas = sum_a / n_a - sum_o / n_o
    return deltas[keep], int(reps - keep.sum())


def interval(deltas: Sequence[float]) -> tuple[float, float]:
    """The 2.5% and 97.5% quantiles, linear."""
    lo, hi = np.quantile(np.asarray(deltas, dtype=float), [0.025, 0.975], method="linear")
    return float(lo), float(hi)


def shifted(states: Sequence[str], k: int) -> list[str]:
    """The states rotated circularly by k against the returns; breaks move with them."""
    n = len(states)
    if n == 0:
        return []
    k %= n
    return list(states[n - k :]) + list(states[: n - k])


def precision(
    b: Sequence[float],
    states: Sequence[str],
    *,
    block: int = BLOCK,
    reps: int = REPS,
    seed: int = SEED,
) -> dict[str, Any]:
    """Median half-width of the interval over every shift from 13 to n-13. Never returns a delta."""
    n = len(states)
    widths: list[float] = []
    dropped = 0
    for k in range(MIN_SHIFT, n - MIN_SHIFT + 1):
        deltas, lost = bootstrap(b, shifted(states, k), block=block, reps=reps, seed=seed)
        dropped += lost
        if len(deltas) == 0:
            raise ValueError("every replication was dropped at one shift")
        lo, hi = interval(deltas)
        widths.append((hi - lo) / 2)
    if not widths:
        raise ValueError("too few periods for any shift")
    median = float(np.median(widths))
    return {
        "shifts": len(widths),
        "median_half_width": median,
        "pass": bool(median <= MAX_HALF_WIDTH),
        "dropped": dropped,
    }


def file_sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main(argv: list[str] | None = None) -> int:
    import e0004_state as state_tool  # here only

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
        usd = common.usd_columns(panel)
        states = state_tool.states(month_ends, releases, cpi)
        b = benefit(usd["equity"], usd["treasury"], usd["bills"])
        result = precision(b, states)
        commit = ev.code_commit()["commit"]
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out = args.runs / f"{stamp}-{commit[:8]}"
        out.mkdir(mode=0o700, parents=True)
        text = json.dumps({"code": commit, **result}, indent=1, sort_keys=True) + "\n"
        ev.private_write(out / "precision.json", text.encode())
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
