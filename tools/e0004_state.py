"""E-0004 step 1: the CPI state (preregistration-1, "The state"). Pure functions; no network, no writes.

Accelerating for the period after a month end: the latest year-on-year CPI-U rate published on or before
that day is greater than the latest one published as of the same day a year earlier. Equality is "not".
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

SERIES_ID = "CUUR0000SA0"
FLAT_HEADER = ["series_id", "year", "period", "value", "footnote_codes"]
RELEASE_HEADER = ["date", "url"]


def load_cpi(path: Path) -> dict[tuple[int, int], Decimal]:
    """Read the BLS flat file; keep CUUR0000SA0 months M01..M12 with numeric values. Refuse repeats."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError("CPI file is empty")
    header = [f.strip() for f in lines[0].split("\t")]
    if header != FLAT_HEADER:
        raise ValueError(f"CPI file header is {header!r}, expected {FLAT_HEADER!r}")
    out: dict[tuple[int, int], Decimal] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        fields = [f.strip() for f in line.split("\t")]
        if len(fields) < 4 or fields[0] != SERIES_ID:
            continue
        period = fields[2]
        if len(period) != 3 or period[0] != "M" or not period[1:].isdigit():
            continue
        month = int(period[1:])
        if not 1 <= month <= 12:
            continue
        key = (int(fields[1]), month)
        if key in out:
            raise ValueError(f"repeated CPI month {key[0]}-{key[1]:02d}")
        try:
            value = Decimal(fields[3])
        except InvalidOperation:
            continue
        if not value.is_finite():
            continue
        out[key] = value
    return out


def load_releases(path: Path) -> list[date]:
    """Read release-dates.csv (header date,url); return the sorted unique dates."""
    with Path(path).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows or [c.strip() for c in rows[0]] != RELEASE_HEADER:
        raise ValueError(f"release file header must be {','.join(RELEASE_HEADER)}")
    return sorted({date.fromisoformat(r[0].strip()) for r in rows[1:] if r and r[0].strip()})


def reference_month(release: date) -> tuple[int, int]:
    """The calendar month before the release's month."""
    if release.month == 1:
        return (release.year - 1, 12)
    return (release.year, release.month - 1)


def yoy(cpi: dict[tuple[int, int], Decimal], ref: tuple[int, int]) -> Decimal | None:
    """Level at ref over level a year earlier, minus one, unrounded; None if either level is missing."""
    now = cpi.get(ref)
    before = cpi.get((ref[0] - 1, ref[1]))
    if now is None or before is None:
        return None
    with localcontext() as ctx:
        ctx.prec = 28
        return now / before - 1


def latest_rate(
    asof: date, releases: list[date], cpi: dict[tuple[int, int], Decimal]
) -> tuple[date, tuple[int, int], Decimal] | None:
    """The latest release on or before asof with a computable rate: (release, reference month, rate)."""
    for rel in sorted((r for r in releases if r <= asof), reverse=True):
        ref = reference_month(rel)
        rate = yoy(cpi, ref)
        if rate is not None:
            return rel, ref, rate
    return None


def year_earlier(asof: date) -> date:
    """The last calendar day of the same month a year before. CPI is released mid-month, so this sees the
    same releases as that month's last trading close; it needn't be a month end of the panel."""
    first_next = date(asof.year - 1 + asof.month // 12, asof.month % 12 + 1, 1)
    return first_next - timedelta(days=1)


def states(
    month_ends: list[date],
    releases: list[date],
    cpi: dict[tuple[int, int], Decimal],
    *,
    equal_is_accelerating: bool = False,
) -> list[str]:
    """State labelling each period month_ends[i] to month_ends[i+1]: accelerating, not or unavailable.

    Equality is "not" unless `equal_is_accelerating` (a step 2 sensitivity)."""
    out: list[str] = []
    for i in range(len(month_ends) - 1):
        now = month_ends[i]
        prior = year_earlier(now)
        a = latest_rate(now, releases, cpi)
        b = latest_rate(prior, releases, cpi)
        if a is None or b is None:
            out.append("unavailable")
        else:
            up = a[2] >= b[2] if equal_is_accelerating else a[2] > b[2]
            out.append("accelerating" if up else "not")
    return out
