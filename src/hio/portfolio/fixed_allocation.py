"""Descriptive calculations for fixed hypothetical allocations (T-0021, OD-0159).

They describe the returns they are given. Nothing here forecasts, optimises, recommends or prices a cost.

Conventions, all simple returns:
- **Alignment.** A panel's dates are the dates every sleeve has as a period boundary. Each sleeve is
  compounded
  between consecutive common dates, exactly, and converted to float once, in `align`. Nothing is filled.
- **Wealth.** Starts at 1 in the target weights, drifts with fractional holdings and no costs, and is
  reset to the
  weights at the last common date of each calendar month.
- **Period returns.** Measured between the last common dates of consecutive calendar months or ISO weeks.
  The first
  and last periods are dropped as possibly partial.
- **Annualisation.** Volatility is the sample standard deviation (ddof 1) times the square root of 12 or
  52. Return
  is geometric, on 365.25 days a year.
- **Drawdown.** Measured from the running peak. A drawdown not recovered by the end has no recovery date,
  and its
  underwater time runs to the end.
- **Bootstrap.** Circular blocks of whole months, the same rows for every sleeve, with the rebalance
  rerun. Its
  drawdowns have monthly resolution. Its intervals are conditional on this history: resampling can't create
  independent crises that did not occur.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Context, Decimal
from itertools import pairwise

import numpy as np
from numpy.typing import NDArray

_CTX = Context(prec=50)
DAYS_PER_YEAR = 365.25
PERIODS_PER_YEAR = {"monthly": 12, "weekly": 52}
RECONCILE_TOLERANCE = 1e-12
Floats = NDArray[np.float64]


class AlignmentError(ValueError):
    """A sleeve's periods don't join, or the sleeves share too few dates. Nothing is filled."""


@dataclass(frozen=True)
class Interval:
    start: date
    end: date
    r: Decimal


@dataclass(frozen=True)
class Panel:
    sleeves: tuple[str, ...]
    dates: tuple[date, ...]  # n + 1 common dates
    returns: Floats  # n rows, one column per sleeve
    omitted_dates: Mapping[
        str, int
    ]  # per sleeve: its own boundaries that aren't common, or lie outside the span


@dataclass(frozen=True)
class WealthPath:
    dates: tuple[date, ...]
    wealth: Floats  # n + 1 values, starting at 1
    holdings: Floats  # n + 1 rows: the value in each sleeve, after any rebalance on that date


@dataclass(frozen=True)
class Drawdown:
    max_drawdown: float  # a positive fraction of the peak
    peak: date
    trough: date
    recovery: date | None  # None: not recovered by the end
    longest_underwater_days: int
    underwater_fraction: float  # the share of calendar days spent below the running peak


@dataclass(frozen=True)
class BootstrapInterval:
    estimate: float  # on the observed months
    low: float  # 2.5th percentile
    high: float  # 97.5th percentile


@dataclass(frozen=True)
class PairedBootstrap:
    block_months: int
    replications: int
    seed: int
    volatility: BootstrapInterval  # portfolio b minus portfolio a, in each case
    annualised_return: BootstrapInterval
    max_drawdown: BootstrapInterval


def _check_joined(name: str, intervals: Sequence[Interval]) -> None:
    if not intervals:
        raise AlignmentError(f"sleeve {name} has no periods")
    for period in intervals:
        if period.end <= period.start:
            raise AlignmentError(f"sleeve {name}: a period ends on or before its start, at {period.start}")
    for a, b in pairwise(intervals):
        if a.end != b.start:
            raise AlignmentError(f"sleeve {name}: its periods don't join between {a.end} and {b.start}")


def align(series: Mapping[str, Sequence[Interval]]) -> Panel:
    """The one Decimal-to-float boundary. A gap inside a sleeve refuses: the caller decides which span to
    ask for."""
    if not series:
        raise AlignmentError("no sleeves")
    ordered = {name: sorted(series[name], key=lambda p: p.start) for name in sorted(series)}
    for name, intervals in ordered.items():
        _check_joined(name, intervals)
    boundaries = {name: {p.start for p in iv} | {iv[-1].end} for name, iv in ordered.items()}
    common = sorted(set.intersection(*boundaries.values()))
    if len(common) < 2:
        raise AlignmentError("the sleeves share fewer than two dates")

    columns = []
    for intervals in ordered.values():
        growth = {p.start: _CTX.add(Decimal(1), p.r) for p in intervals}
        ends = {p.start: p.end for p in intervals}
        column = []
        for start, end in pairwise(common):
            level, cursor = Decimal(1), start
            while cursor != end:
                level, cursor = _CTX.multiply(level, growth[cursor]), ends[cursor]
            column.append(float(_CTX.subtract(level, Decimal(1))))
        columns.append(column)
    omitted = {name: len(boundaries[name] - set(common)) for name in ordered}
    return Panel(tuple(ordered), tuple(common), np.array(columns, dtype=np.float64).T, omitted)


def window(panel: Panel, start: date, end: date) -> Panel:
    """One contiguous span. Excluding a period from inside a wealth path is deliberately not offered."""
    kept = [i for i, d in enumerate(panel.dates) if start <= d <= end]
    if len(kept) < 2:
        raise AlignmentError(f"fewer than two dates between {start} and {end}")
    dates = tuple(panel.dates[i] for i in kept)
    return Panel(panel.sleeves, dates, panel.returns[kept[0] : kept[-1]], panel.omitted_dates)


def _weights(panel: Panel, weights: Mapping[str, float]) -> Floats:
    if set(weights) != set(panel.sleeves):
        raise ValueError(f"weights must name exactly the sleeves {panel.sleeves}")
    vector = np.array([weights[s] for s in panel.sleeves], dtype=np.float64)
    if (vector < 0).any() or abs(vector.sum() - 1) > RECONCILE_TOLERANCE:
        raise ValueError("weights must be non-negative and sum to 1")
    return vector


def _period_key(day: date, frequency: str) -> tuple[int, int]:
    if frequency == "monthly":
        return day.year, day.month
    if frequency == "weekly":
        iso = day.isocalendar()
        return iso.year, iso.week
    raise ValueError(f"unknown frequency {frequency}")


def period_ends(dates: Sequence[date], frequency: str) -> list[int]:
    """Indices of the last date of each calendar period, without the final period, which may be partial."""
    return [
        i
        for i, (a, b) in enumerate(pairwise(dates))
        if _period_key(a, frequency) != _period_key(b, frequency)
    ]


def wealth_path(panel: Panel, weights: Mapping[str, float]) -> WealthPath:
    target = _weights(panel, weights)
    rebalance = set(period_ends(panel.dates, "monthly"))
    holdings = np.zeros((len(panel.dates), len(panel.sleeves)), dtype=np.float64)
    holdings[0] = target
    for i, row in enumerate(panel.returns, start=1):
        grown = holdings[i - 1] * (1 + row)
        holdings[i] = target * grown.sum() if i in rebalance else grown
    return WealthPath(panel.dates, holdings.sum(axis=1), holdings)


def reconcile(panel: Panel, weights: Mapping[str, float], path: WealthPath) -> float:
    """Rebuild final wealth independently: between rebalances, each sleeve compounds on its own weight.
    Raises on a
    break, and returns the relative difference."""
    target = _weights(panel, weights)
    marks = [0, *period_ends(panel.dates, "monthly"), len(panel.dates) - 1]
    level = 1.0
    for a, b in pairwise(sorted(set(marks))):
        level *= float(target @ np.prod(1 + panel.returns[a:b], axis=0))
    difference = abs(level / float(path.wealth[-1]) - 1)
    if difference > RECONCILE_TOLERANCE:
        raise ArithmeticError(f"wealth doesn't reconcile: relative difference {difference}")
    return difference


def period_returns(dates: Sequence[date], levels: Floats, frequency: str) -> Floats:
    """Simple returns of a level series, or of each column of one, between calendar-period ends."""
    ends = period_ends(dates, frequency)
    if len(ends) < 2:
        raise ValueError(f"fewer than two complete {frequency} marks")
    marks = levels[ends]
    return marks[1:] / marks[:-1] - 1


def sleeve_levels(panel: Panel) -> Floats:
    """Each sleeve's own compounded level, one row per date, starting at 1."""
    start = np.ones((1, len(panel.sleeves)), dtype=np.float64)
    return np.vstack((start, np.cumprod(1 + panel.returns, axis=0)))


def annualised_volatility(returns: Floats, frequency: str) -> float:
    return float(np.std(returns, ddof=1) * np.sqrt(PERIODS_PER_YEAR[frequency]))


def annualised_return(path: WealthPath) -> float:
    days = (path.dates[-1] - path.dates[0]).days
    return float((path.wealth[-1] / path.wealth[0]) ** (DAYS_PER_YEAR / days) - 1)


def covariance(returns: Floats) -> tuple[Floats, Floats]:
    """Sample covariance (ddof 1) and correlation, of the columns as given, not annualised."""
    return np.cov(returns, rowvar=False, ddof=1), np.corrcoef(returns, rowvar=False)


def drawdown(dates: Sequence[date], levels: Floats) -> Drawdown:
    peaks = np.maximum.accumulate(levels)
    depth = 1 - levels / peaks
    trough = int(np.argmax(depth))
    peak = int(np.argmax(levels[: trough + 1]))
    later = np.flatnonzero(levels[trough:] >= levels[peak])
    recovery = dates[trough + int(later[0])] if depth[trough] > 0 and later.size else None

    longest, underwater, opened = 0, 0, None
    for i in range(1, len(dates)):
        span = (dates[i] - dates[i - 1]).days
        if depth[i] > 0:
            underwater += span
            opened = i - 1 if opened is None else opened
            longest = max(longest, (dates[i] - dates[opened]).days)
        else:
            if opened is not None:
                underwater += span  # the period that recovered was still under water when it began
                longest = max(longest, (dates[i] - dates[opened]).days)
            opened = None
    total = (dates[-1] - dates[0]).days
    return Drawdown(float(depth[trough]), dates[peak], dates[trough], recovery, longest, underwater / total)


def _max_drawdowns(levels: Floats) -> Floats:
    return (1 - levels / np.maximum.accumulate(levels, axis=1)).max(axis=1)


def _summaries(portfolio: Floats) -> tuple[Floats, Floats, Floats]:
    """Rows of monthly returns: annualised volatility, geometric annualised return, monthly-resolution
    drawdown."""
    levels = np.cumprod(1 + portfolio, axis=1)
    with_base = np.hstack((np.ones((portfolio.shape[0], 1), dtype=np.float64), levels))
    volatility = np.std(portfolio, axis=1, ddof=1) * np.sqrt(12)
    growth = levels[:, -1] ** (12 / portfolio.shape[1]) - 1
    return volatility, growth, _max_drawdowns(with_base)


def paired_block_bootstrap(
    monthly: Floats,
    weights_a: Floats,
    weights_b: Floats,
    *,
    block_months: int,
    replications: int,
    seed: int,
) -> PairedBootstrap:
    """Portfolio b minus portfolio a, on the same resampled months. `monthly` holds sleeve returns, one
    row per
    month. Monthly rebalancing makes each month's portfolio return the weighted sum of its sleeves."""
    months = monthly.shape[0]
    if not 1 <= block_months <= months:
        raise ValueError(f"a block of {block_months} doesn't fit {months} months")
    if replications < 1:
        raise ValueError("at least one replication")
    rng = np.random.default_rng(seed)
    blocks = months // block_months + 1
    starts = rng.integers(0, months, size=(replications, blocks))
    rows = (starts[:, :, None] + np.arange(block_months)).reshape(replications, -1)[:, :months] % months

    def differences(selected: NDArray[np.int64]) -> list[Floats]:
        sampled = monthly[selected]
        first, second = _summaries(sampled @ weights_a), _summaries(sampled @ weights_b)
        return [b - a for a, b in zip(first, second, strict=True)]

    observed = differences(np.arange(months)[None, :])
    resampled = differences(rows)
    intervals = [
        BootstrapInterval(float(o[0]), float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5)))
        for o, r in zip(observed, resampled, strict=True)
    ]
    return PairedBootstrap(block_months, replications, seed, *intervals)
