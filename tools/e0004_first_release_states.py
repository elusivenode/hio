"""E-0004 finding F-1, CPI-only check (OD-0200): do the states change when each CPI month is the level printed
in its own (first) release rather than the flat-file level?

`first_release_series` reads the level printed for a month in that month's own release (never the year-ago
column). `compare_states` recomputes the E-0004 states (primary rule, and the equality sensitivity) from the
flat file and from the first-release series, and compares both with the states the run recorded. A month the
state rule reads from the first-release series and does not find is reported, never replaced by an older rate.
No re-estimation, no design change; this tool writes nothing but its two output files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

_HERE = Path(__file__).resolve().parent
REPO = _HERE.parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_state = _load("e0004_state_for_first_release", "e0004_state.py")
_releases = _load("bls_cpi_releases_for_first_release", "bls_cpi_releases.py")

DEFAULT_RAW = Path("~/.hio-research/E-0004/raw").expanduser()
STATES_HEADER = ["period_start", "period_end", "state"]
LEDGER_HEADER = ["month", "release", "sha256", "printed", "flat", "equal"]
RELEASE_DATES_NAME = "release-dates.csv"
# BLS never published October 2025; it is absent from the flat file by design.
UNPUBLISHED = frozenset({(2025, 10)})

Month = tuple[int, int]


def _label(month: Month) -> str:
    return f"{month[0]:04d}-{month[1]:02d}"


def _parse_all(release_dirs: list[Path]) -> list[tuple[str, str, tuple]]:
    """(file name, sha256, parse_release result) for every cpi_* file in the directories."""
    out = []
    for directory in release_dirs:
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"{directory} is not a directory")
        for path in sorted(directory.glob("cpi_*")):
            if not path.is_file():
                continue
            data = path.read_bytes()
            out.append(
                (path.name, hashlib.sha256(data).hexdigest(), _releases.parse_release(path.name, data))
            )
    if not out:
        raise ValueError("no cpi_* release files were found")
    return out


def first_release_series(release_dirs: list[Path]) -> tuple[dict[Month, Decimal], list[dict]]:
    """(levels, ledger): the level printed for each reference month in its own release."""
    levels: dict[Month, Decimal] = {}
    ledger: dict[Month, dict] = {}
    for name, digest, (ref, level, _ago, _ago_level) in _parse_all(release_dirs):
        key = (ref.year, ref.month)
        if level is None:
            raise ValueError(f"{name}: no level is printed for reference month {_label(key)}")
        if key in levels:
            raise ValueError(f"{name} and {ledger[key]['release']} both give reference month {_label(key)}")
        levels[key] = level
        ledger[key] = {"month": _label(key), "release": name, "sha256": digest, "printed": str(level)}
    ordered = sorted(levels)
    return {k: levels[k] for k in ordered}, [ledger[k] for k in ordered]


def year_ago_checks(release_dirs: list[Path], levels: dict[Month, Decimal]) -> list[dict]:
    """Year-ago levels that differ from the month's own first-release level (corroboration only).

    A year-ago month with no first-release level cannot be corroborated and is not listed."""
    rows = []
    for name, _digest, (_ref, _level, ago, ago_level) in _parse_all(release_dirs):
        key = (ago.year, ago.month)
        if ago_level is None or key not in levels:
            continue
        if ago_level != levels[key]:
            rows.append(
                {"release": name, "month": _label(key), "year_ago": str(ago_level), "first": str(levels[key])}
            )
    return rows


def month_ends_from_states_csv(path: Path) -> tuple[list[date], list[str]]:
    """The run's states.csv: (every period_start then the last period_end, the recorded states)."""
    with Path(path).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows or [c.strip() for c in rows[0]] != STATES_HEADER:
        raise ValueError(f"states.csv header must be {','.join(STATES_HEADER)}")
    body = [r for r in rows[1:] if r]
    if not body:
        raise ValueError("states.csv has no periods")
    starts, ends, states = [], [], []
    for row in body:
        if len(row) != 3:
            raise ValueError("states.csv has a row that is not three fields")
        starts.append(date.fromisoformat(row[0].strip()))
        ends.append(date.fromisoformat(row[1].strip()))
        states.append(row[2].strip())
    for i in range(len(body) - 1):
        if ends[i] != starts[i + 1]:
            raise ValueError(f"states.csv periods do not chain at {ends[i].isoformat()}")
    return [*starts, ends[-1]], states


class _Lookups(dict):
    """A level table that records every month asked for with .get and not found."""

    def __init__(self, data: dict):
        super().__init__(data)
        self.missed: set[Month] = set()

    def get(self, key, default=None):
        if key not in self:
            self.missed.add(key)
        return super().get(key, default)


def _differences(month_ends: list[date], a: list[str], b: list[str]) -> list[dict]:
    return [
        {
            "period_start": month_ends[i].isoformat(),
            "period_end": month_ends[i + 1].isoformat(),
            "flat": a[i],
            "first_release": b[i],
        }
        for i in range(len(a))
        if a[i] != b[i]
    ]


def compare_states(
    month_ends: list[date],
    releases: list[date],
    flat: dict[Month, Decimal],
    first: dict[Month, Decimal],
    recorded: list[str],
) -> dict:
    """Recompute the states from the flat and first-release series under both rules and compare."""
    tracked = _Lookups(first)
    result: dict = {"periods": len(month_ends) - 1}
    states: dict[str, tuple[list[str], list[str]]] = {}
    for rule, equal in (("primary", False), ("equal_is_accelerating", True)):
        from_flat = _state.states(month_ends, releases, dict(flat), equal_is_accelerating=equal)
        from_first = _state.states(month_ends, releases, tracked, equal_is_accelerating=equal)
        states[rule] = (from_flat, from_first)
        diffs = _differences(month_ends, from_flat, from_first)
        result[rule] = {"periods": len(from_flat), "differing": len(diffs), "differing_periods": diffs}
    flat_primary, first_primary = states["primary"]
    reproduces = flat_primary == list(recorded)
    unpublished = {m for m in tracked.missed if m in UNPUBLISHED and m not in flat}
    missing = tracked.missed - unpublished
    result["reproduces_run"] = reproduces
    result["unavailable"] = {
        "flat": flat_primary.count("unavailable"),
        "first_release": first_primary.count("unavailable"),
    }
    result["missing_first_release_months"] = [_label(m) for m in sorted(missing)]
    result["unpublished_months"] = [_label(m) for m in sorted(unpublished)]
    any_diff = result["primary"]["differing"] or result["equal_is_accelerating"]["differing"]
    if any_diff:
        result["reading"] = "differences found"
    elif reproduces and not missing:
        result["reading"] = "identical"
    else:
        result["reading"] = "incomplete"
    return result


def _outside_repo(out: Path) -> Path:
    resolved = Path(out).expanduser().resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("the output directory must lie outside the repository")
    return resolved


def run(raw: Path, release_dirs: list[Path], states_csv: Path, out: Path) -> dict:
    out = _outside_repo(out)
    raw = Path(raw).expanduser()
    flat_dates = _releases.read_flat(raw / _releases.FLAT_NAME)
    flat = {(d.year, d.month): v for d, v in flat_dates.items()}
    release_days = _state.load_releases(raw / RELEASE_DATES_NAME)
    levels, ledger = first_release_series(release_dirs)
    checks = year_ago_checks(release_dirs, levels)
    month_ends, recorded = month_ends_from_states_csv(states_csv)
    result = compare_states(month_ends, release_days, flat, levels, recorded)
    result["year_ago_differences"] = checks
    out.mkdir(parents=True, exist_ok=True)
    with (out / "ledger.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(LEDGER_HEADER)
        for row in ledger:
            year, month = int(row["month"][:4]), int(row["month"][5:])
            level = flat.get((year, month))
            same = level is not None and str(level) == row["printed"]
            writer.writerow(
                [
                    row["month"],
                    row["release"],
                    row["sha256"],
                    row["printed"],
                    "" if level is None else str(level),
                    "yes" if same else "no",
                ]
            )
    (out / "state-comparison.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--releases", type=Path, nargs="+", required=True)
    parser.add_argument("--states", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.raw, args.releases, args.states, args.out)
    except (ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"periods {result['periods']}")
    print(f"reproduces run {result['reproduces_run']}")
    for rule in ("primary", "equal_is_accelerating"):
        print(f"{rule} differing periods {result[rule]['differing']}")
    unavailable = result["unavailable"]
    print(f"unavailable flat {unavailable['flat']}, first release {unavailable['first_release']}")
    print(f"missing first-release months {len(result['missing_first_release_months'])}")
    print(f"unpublished months {len(result['unpublished_months'])}")
    print(f"year-ago differences {len(result['year_ago_differences'])}")
    print(f"reading: {result['reading']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
