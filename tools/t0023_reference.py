"""T-0023's public reference files, recorded (OD-0178). Files are read once by hand or with curl into
~/.hio-research/T-0023/reference/raw, then `record` hashes each against sources.json, and `extract` turns
State Street's NAV workbooks into date,nav CSVs. openpyxl isn't a HIO dependency, so run it with
`uv run --with openpyxl==3.1.5 python tools/t0023_reference.py extract`. Nothing here fetches.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import eodhd_eval as ev

NAV_FILES = {"navhist-spy.xlsx": "nav-spy.csv", "navhist-bil.xlsx": "nav-bil.csv"}


def nav_rows(rows: list[tuple[object, ...]]) -> list[tuple[str, str]]:
    """Date and NAV, oldest first, from a workbook's rows. Anything after the header that isn't both stops."""
    start = next((i for i, r in enumerate(rows) if r and r[0] == "Date" and r[1] == "NAV"), None)
    if start is None:
        raise ev.Stop("no Date and NAV header")
    out = {}
    for row in rows[start + 1 :]:
        if row[0] is None:
            continue
        try:
            day = datetime.strptime(str(row[0]), "%d-%b-%Y").replace(tzinfo=UTC).date()
        except ValueError:
            if row[1] is None:  # the issuer's footer text
                continue
            raise ev.Stop("a NAV row with no readable date") from None
        if not isinstance(row[1], int | float) or row[1] <= 0:
            raise ev.Stop(f"{day}: an impossible NAV")
        if day in out:
            raise ev.Stop(f"{day}: a repeated NAV row")
        out[day] = repr(row[1])
    if not out:
        raise ev.Stop("no NAV rows")
    return [(d.isoformat(), out[d]) for d in sorted(out)]


def nav_text(rows: list[tuple[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["date", "nav"])
    writer.writerows(rows)
    return buffer.getvalue()


def record(
    reference: Path, sources: dict[str, dict[str, str]], now: datetime | None = None
) -> dict[str, object]:
    """Hash each raw file against what's declared about it. A file that isn't declared stops."""
    raw = reference / "raw"
    found = sorted(p.name for p in raw.iterdir() if p.is_file())
    unknown = sorted(set(found) - set(sources))
    if unknown:
        raise ev.Stop(f"not declared: {', '.join(unknown)}")
    return {
        "recorded_at": (now or datetime.now(UTC)).isoformat(),
        "files": {
            name: {**sources[name], "sha256": hashlib.sha256((raw / name).read_bytes()).hexdigest()}
            for name in found
        },
    }


def extract(reference: Path) -> dict[str, int]:
    import openpyxl

    out = {}
    for source, target in NAV_FILES.items():
        path = reference / "raw" / source
        if not path.is_file():
            continue
        sheet = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
        rows = nav_rows([tuple(r) for r in sheet.iter_rows(values_only=True)])
        ev.private_write(reference / target, nav_text(rows).encode())
        out[target] = len(rows)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["record", "extract"])
    parser.add_argument(
        "--reference", type=Path, default=Path.home() / ".hio-research" / "T-0023" / "reference"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "record":
            sources = json.loads((args.reference / "sources.json").read_text())
            out = record(args.reference, sources)
            ev.private_write(
                args.reference / "manifest.json", (json.dumps(out, indent=1, sort_keys=True) + "\n").encode()
            )
            print(json.dumps({"files": len(out["files"])}))  # type: ignore[arg-type]
        else:
            print(json.dumps(extract(args.reference), sort_keys=True))
    except (ev.Stop, ValueError, ImportError) as exc:
        print(f"stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
