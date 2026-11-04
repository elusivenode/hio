"""The one-off RBA historical F1 download (OD-0172), and a read of its header rows only.

One request, no retries. --output must be absent or empty and outside the repository, so a re-run can't
download again. A dirty tree refuses, so the manifest names what ran. `headers` needs an .xls reader, which
isn't a HIO dependency, so it runs with `uv run --with xlrd`. It prints each series' title, id and source, and
no rate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine

REPO = Path(__file__).resolve().parent.parent
SOURCE_ID = "rba.f1_historical"
URL = "https://www.rba.gov.au/statistics/tables/xls-hist/f01dhist.xls"
USER_AGENT = "HIO-research/0.1 (one-off historical download; non-commercial research)"
NOTICE = "Source: Reserve Bank of Australia. No endorsement by the RBA is implied."
FILE_NAME = "f01dhist.xls"
EXTRACT_NAME = "firmmcrid.csv"
XLS_MAGIC = bytes.fromhex("D0CF11E0")
XLSX_MAGIC = b"PK\x03\x04"
HEADER_LABELS = (
    "title",
    "description",
    "frequency",
    "type",
    "units",
    "source",
    "publication date",
    "series id",
)
Getter = Callable[[str], tuple[int, bytes]]


def http_get(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def fetch(output: Path, *, gate: RightsGate, commit: str, get: Getter = http_get) -> dict:
    resolved = output.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--output must lie outside the repository")
    if output.exists() and any(output.iterdir()):
        raise ValueError("--output must be absent or empty")
    gate.authorise(Operation.FETCH, [SOURCE_ID])
    gate.authorise(Operation.STORE_RAW, [SOURCE_ID])
    at = datetime.now(UTC).isoformat()
    status, body = get(URL)
    if status != 200:
        raise ValueError(f"HTTP {status}")
    if not body.startswith((XLS_MAGIC, XLSX_MAGIC)):
        raise ValueError("not a spreadsheet")
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    (output / FILE_NAME).write_bytes(body)
    manifest = {
        "source_id": SOURCE_ID,
        "url": URL,
        "retrieved_at": at,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "notice": NOTICE,
        "knowledge": "reconstructed(T): one one-off download",
        "user_agent": USER_AGENT,
        "code_commit": commit,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def header_rows(rows: list[list[object]]) -> list[dict[str, str]]:
    """One dict per column, from the labelled rows above the data. Data rows are never read into it."""
    labelled = {}
    for row in rows:
        label = str(row[0]).strip().lower() if row else ""
        if label in HEADER_LABELS:
            labelled[label] = row
    width = max((len(r) for r in labelled.values()), default=0)
    return [
        {label: str(r[i]).strip() if i < len(r) else "" for label, r in labelled.items()}
        for i in range(1, width)
    ]


def read_headers(path: Path) -> list[dict[str, str]]:
    import xlrd

    book = xlrd.open_workbook(path)
    out = []
    for name in book.sheet_names():
        sheet = book.sheet_by_name(name)
        rows = [sheet.row_values(i) for i in range(min(sheet.nrows, 15))]
        out += [{"sheet": name, **column} for column in header_rows(rows)]
    return out


def extract_series(path: Path, series_id: str = "FIRMMCRID") -> list[tuple[str, str]]:
    """The RBA-sourced overnight series, as date and rate text. Refuses if its source isn't the RBA."""
    import datetime as dt

    import xlrd

    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_name("Data")
    head = {str(sheet.cell_value(i, 0)).strip().lower(): i for i in range(min(sheet.nrows, 15))}
    ids = sheet.row_values(head["series id"])
    column = ids.index(series_id)
    if str(sheet.cell_value(head["source"], column)).strip() != "RBA":
        raise ValueError(f"{series_id} isn't RBA-sourced")
    out = []
    for i in range(head["series id"] + 1, sheet.nrows):
        when, cell = sheet.cell(i, 0), sheet.cell(i, column)
        if when.ctype == xlrd.XL_CELL_DATE and cell.ctype == xlrd.XL_CELL_NUMBER:
            day = dt.date(*xlrd.xldate_as_tuple(when.value, book.datemode)[:3])
            out.append((day.isoformat(), repr(cell.value)))
    return out


def code_commit() -> str:
    git = ("git", "-C", str(REPO))
    status = subprocess.run((*git, "status", "--porcelain"), capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise ValueError("the working tree has uncommitted changes")
    return subprocess.run(
        (*git, "rev-parse", "HEAD"), capture_output=True, text=True, check=True
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch", "headers", "extract"])
    parser.add_argument("--output", type=Path, default=Path.home() / ".hio-research" / "RBA-F1-history")
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
            print(f"bytes {fetch(args.output, gate=gate, commit=code_commit())['bytes']}")
        elif args.command == "extract":
            rows = extract_series(args.output / FILE_NAME)
            body = "date,rate_pct\n" + "".join(f"{d},{r}\n" for d, r in rows)
            (args.output / EXTRACT_NAME).write_text(body)
            source = hashlib.sha256((args.output / FILE_NAME).read_bytes()).hexdigest()
            meta = {
                "rows": len(rows),
                "from_file_sha256": source,
                "sha256": hashlib.sha256(body.encode()).hexdigest(),
            }
            (args.output / "extract-manifest.json").write_text(
                json.dumps(meta, indent=1, sort_keys=True) + "\n"
            )
            print(json.dumps({"rows": len(rows), "first": rows[0][0], "last": rows[-1][0]}))
        else:
            for column in read_headers(args.output / FILE_NAME):
                print(json.dumps({k: column.get(k, "") for k in ("sheet", "title", "series id", "source")}))
    except (RightsRefused, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
