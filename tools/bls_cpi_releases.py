"""Archived BLS CPI news releases and the first-release comparison (OD-0197; finding e0004-1-1).

`fetch` downloads the archived releases listed in release-dates.csv (one GET each, at most `cap`), saving
every body verbatim under a manifest. The contact goes into the request User-Agent only and is never written.
A run that stops part-way (a refused request) leaves progress.json; running `fetch` again resumes from it,
keeps the pages already held and counts the requests already spent against the same cap.
`parse_release` always reads the table headed "Table 1."; the summary table before it is never read.
`parse_release` reads Table 1, "All items", unadjusted indexes, from three layouts: HTML tables (2013 on),
HTML <PRE> text (about 2008 to 2012) and PDF (2006-05 to 2008-01, text-extracted with pypdf, imported lazily).
`compare` sets every printed level against the flat-file level, exactly (Decimal).

Known limit: the <PRE>/PDF layout prints only the previous and the reference month's unadjusted indexes, not
the year-ago level; for it `parse_release` returns the year-ago month with a level of None (not printed).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("bls_cpi_fetch_for_releases", _HERE / "bls_cpi_fetch.py")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

REPO = _base.REPO
SOURCE_ID = _base.SOURCE_ID
Budget = _base.Budget
http_get = _base.http_get
USER_AGENT_TEMPLATE = _base.USER_AGENT_TEMPLATE
REDACTED_CONTACT = _base.REDACTED_CONTACT
NOTICE = _base.NOTICE
SERIES_ID = _base.SERIES_ID
FLAT_NAME = _base.FLAT_NAME
FLAT_HEADER = _base.FLAT_HEADER
_check_contact = _base._check_contact

DEFAULT_RAW = Path("~/.hio-research/E-0004/raw").expanduser()
DEFAULT_RELEASES = Path("~/.hio-research/E-0004/releases").expanduser()
DEFAULT_CAP = 250
PROGRESS = "progress.json"
MONTHS = {
    m: i
    for i, m in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1
    )
}
LABEL = re.compile(r"^([A-Za-z]{3,4})\.?\s+(\d{4})$")
LEVEL = re.compile(r"^\d+\.\d+$")
TABLE_1_TEXT = re.compile(r"^[ \t]*Table 1\.[ \t]", re.MULTILINE)

Getter = Callable[[str, str], tuple[int, bytes]]
Parsed = tuple[date, "Decimal | None", date, "Decimal | None"]


def _month(label: str, year: str) -> date:
    key = label[:3].lower()
    if key not in MONTHS:
        raise ValueError(f"unrecognised month label {label!r}")
    return date(int(year), MONTHS[key], 1)


def _year_ago(month: date) -> date:
    return date(month.year - 1, month.month, 1)


def _level(cell: str) -> Decimal | None:
    cell = cell.strip()
    if cell == "-":
        return None
    if not LEVEL.match(cell):
        raise ValueError(f"the All items row holds {cell!r}, not an index level")
    try:
        return Decimal(cell)
    except InvalidOperation as exc:  # pragma: no cover - guarded by LEVEL
        raise ValueError(f"bad index level {cell!r}") from exc


# ---------------------------------------------------------------- parsing


def _text(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", " ", fragment, flags=re.IGNORECASE)
    return " ".join(re.sub(r"<[^>]*>", "", fragment).split())


def _table_1_html(html: str) -> str:
    """The <table> whose caption starts "Table 1."; a release's first "All items" row is in Table A."""
    for table in re.finditer(r"<table\b.*?</table>", html, re.DOTALL | re.IGNORECASE):
        caption = re.search(r"<caption\b[^>]*>(.*?)</caption>", table.group(0), re.DOTALL | re.IGNORECASE)
        if caption and _text(caption.group(1)).startswith("Table 1."):
            return table.group(0)
    raise ValueError("no HTML table captioned 'Table 1.' was found")


FOOTNOTE_REFS = re.compile(
    r"<span\b[^>]*\bclass\s*=\s*[\"']footnoteRefs[\"'][^>]*>.*?</span>", re.DOTALL | re.IGNORECASE
)


def _parse_html(html: str) -> Parsed:
    # BLS marks revisions and footnotes with <span class="footnoteRefs">(<a>r</a>)</span>; they are not data.
    html = FOOTNOTE_REFS.sub("", _table_1_html(html))
    row = re.search(
        r"<tr\b[^>]*>\s*<th\b[^>]*>\s*(?:<p\b[^>]*>)?\s*All items\s*(?:</p>)?\s*</th>(.*?)</tr>",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if not row:
        raise ValueError("no 'All items' row found in the HTML table")
    labels = []
    for head in re.findall(r"<th\b[^>]*>(.*?)</th>", html[: row.start()], re.DOTALL | re.IGNORECASE):
        match = LABEL.match(_text(head))
        if match:
            labels.append(_month(*match.groups()))
    cells = [_text(c) for c in re.findall(r"<td\b[^>]*>(.*?)</td>", row.group(1), re.DOTALL | re.IGNORECASE)]
    if len(labels) < 3 or len(cells) < 4:
        raise ValueError("the unadjusted-index month labels or the 'All items' cells were not found")
    year_ago, _previous, reference = labels[:3]
    if year_ago != _year_ago(reference):
        raise ValueError("the first unadjusted-index column is not the reference month a year earlier")
    return reference, _level(cells[3]), year_ago, _level(cells[1])


def _parse_text(text: str) -> Parsed:
    """The <PRE> layout (also the text extracted from a PDF): previous and reference month, no year-ago."""
    start = TABLE_1_TEXT.search(text)
    if not start:
        raise ValueError("no 'Table 1.' heading found in the text")
    text = text[start.start() :]  # the release body has its own, earlier "All items" row
    row = re.search(r"^[ \t]*All items[ \t]*\.{2,}[ \t]+(\S.*)$", text, re.MULTILINE)
    if not row:
        raise ValueError("no 'All items' row found in the text table")
    head = text[: row.start()]
    label = re.search(r"\bto\s+([A-Za-z]{3,4})\.?\s+(\d{4})\b", head)
    if "Unadjusted" not in head or not label:
        raise ValueError("the reference-month label was not found in the text table header")
    tokens = row.group(1).split()
    if len(tokens) < 3:
        raise ValueError("the 'All items' text row is too short")
    reference = _month(*label.groups())
    return reference, _level(tokens[2]), _year_ago(reference), None


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader  # lazy: only the PDF layout needs it

    reader = PdfReader(io.BytesIO(data))
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
        start = TABLE_1_TEXT.search(text)
        if start and re.search(r"^[ \t]*All items[ \t]*\.{2,}", text[start.start() :], re.MULTILINE):
            break
    return text


def parse_release(name: str, data: bytes) -> Parsed:
    """(reference month, its level, year-ago month, its level) from Table 1 "All items", unadjusted.

    Months are the first of the month. A level shown as "-" (or not printed in the layout) is None.
    Raises ValueError rather than guess.
    """
    try:
        if name.lower().endswith(".pdf") or data[:5] == b"%PDF-":
            return _parse_text(_pdf_text(data))
        html = data.decode("utf-8", errors="replace")
        if "datavalue" in html or re.search(r"<th\b", html, re.IGNORECASE):
            return _parse_html(html)
        return _parse_text(html)
    except ValueError as exc:
        raise ValueError(f"{name}: {exc}") from exc


# ---------------------------------------------------------------- fetch


def _read_dates(raw_dir: Path) -> list[tuple[date, str]]:
    path = raw_dir / "release-dates.csv"
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        if next(reader, None) != ["date", "url"]:
            raise ValueError("release-dates.csv does not have the header date,url")
        return [(date.fromisoformat(row[0]), row[1]) for row in reader if row]


def fetch(
    raw_dir: Path,
    out_dir: Path,
    *,
    start: date = date(2006, 5, 1),
    end: date = date(2026, 10, 31),
    contact: str,
    gate: RightsGate,
    commit: str,
    get: Getter = http_get,
    cap: int = DEFAULT_CAP,
    now: datetime | None = None,
    pause: float = 0.0,
) -> dict:
    contact = _check_contact(contact)
    resolved = out_dir.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("the output directory must lie outside the repository")
    progress_path = out_dir / PROGRESS
    files: list[dict] = []
    spent = 0
    if progress_path.exists():  # an earlier run stopped part-way: keep its pages and its request count
        progress = json.loads(progress_path.read_text())
        spent, files = int(progress["requests"]), list(progress["files"])
        for entry in files:
            held = out_dir / entry["name"]
            if not held.is_file() or hashlib.sha256(held.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"{entry['name']} does not match progress.json; the run cannot resume")
    elif out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("the output directory must be absent or empty")
    selected = [(d, u) for d, u in _read_dates(raw_dir) if start <= d <= end]
    if not selected:
        raise ValueError("no release dates fall in the requested span")
    gate.authorise(Operation.FETCH, [SOURCE_ID])
    gate.authorise(Operation.STORE_RAW, [SOURCE_ID])
    moment = now or datetime.now(UTC)
    agent = USER_AGENT_TEMPLATE.format(contact=contact)
    budget = Budget(cap, get, agent)
    budget.count = spent
    needle = contact.encode()
    out_dir.mkdir(parents=True, exist_ok=True)
    held_urls = {entry["url"] for entry in files}
    for when, url in selected:
        if url in held_urls:
            continue
        if pause and budget.count > spent:
            time.sleep(pause)
        try:
            body = budget.get(url)  # refuses on the request past the cap and on any non-200
            if needle in body:
                raise ValueError("a response contains the contact string; it was not written")
            name = f"cpi_{when:%m%d%Y}{Path(url).suffix.lower()}"
            (out_dir / name).write_bytes(body)
            files.append(
                {"name": name, "url": url, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
            )
        finally:  # every request spent is recorded, whether or not it returned a page
            progress_path.write_text(json.dumps({"requests": budget.count, "files": files}, indent=1) + "\n")
    manifest = {
        "source_id": SOURCE_ID,
        "notice": NOTICE.format(date=moment.date().isoformat()),
        "retrieved_at": moment.isoformat(),
        "user_agent": USER_AGENT_TEMPLATE.format(contact=REDACTED_CONTACT),
        "code_commit": commit,
        "requests": budget.count,
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    progress_path.unlink(missing_ok=True)
    return manifest


# ---------------------------------------------------------------- compare


def compare(flat_levels: dict[date, Decimal], parsed: dict[str, Parsed]) -> dict:
    """Each printed level against the flat-file level, exactly. Counts and the differing observations only.

    `flat_levels` maps the first of a month to its level; `parsed` maps a release name to parse_release's
    result. A printed level of None is counted as not printed, not as a difference.
    """
    equal = not_printed = 0
    differences = []
    months = set()
    for name in sorted(parsed):
        ref, level, ago, ago_level = parsed[name]
        for role, month, printed in (("current", ref, level), ("year_ago", ago, ago_level)):
            months.add(month)
            if printed is None:
                not_printed += 1
                continue
            flat = flat_levels.get(month)
            if flat is not None and flat == printed:
                equal += 1
            else:
                differences.append(
                    {
                        "release": name,
                        "role": role,
                        "month": month.strftime("%Y-%m"),
                        "printed": str(printed),
                        "flat": None if flat is None else str(flat),
                    }
                )
    return {
        "releases": len(parsed),
        "months": len(months),
        "observations_equal": equal,
        "observations_different": len(differences),
        "observations_not_printed": not_printed,
        "differing_months": sorted({d["month"] for d in differences}),
        "differences": differences,
        "reading": "all equal" if not differences else "differences found",
    }


def read_flat(path: Path) -> dict[date, Decimal]:
    lines = path.read_text(errors="replace").splitlines()
    if not lines or [c.strip() for c in lines[0].split("\t")] != FLAT_HEADER:
        raise ValueError("the flat file header is not the expected tab-separated columns")
    levels: dict[date, Decimal] = {}
    for line in lines[1:]:
        cells = [c.strip() for c in line.split("\t")]
        if cells[0] != SERIES_ID or not (len(cells) >= 4 and re.fullmatch(r"M(0[1-9]|1[0-2])", cells[2])):
            continue
        if cells[3] == "-":  # a month BLS did not publish (October 2025)
            continue
        levels[date(int(cells[1]), int(cells[2][1:]), 1)] = Decimal(cells[3])
    if not levels:
        raise ValueError(f"the flat file has no monthly {SERIES_ID} rows")
    return levels


def run_compare(raw_dir: Path, releases_dir: Path) -> tuple[dict, list[str]]:
    flat = read_flat(raw_dir / FLAT_NAME)
    parsed: dict[str, Parsed] = {}
    failures: list[str] = []
    for path in sorted(releases_dir.glob("cpi_*")):
        try:
            parsed[path.name] = parse_release(path.name, path.read_bytes())
        except ValueError as exc:
            failures.append(str(exc))
    return compare(flat, parsed), failures


# ---------------------------------------------------------------- command line


def _code_commit() -> str:
    return _base.code_commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "compare"):
        p = sub.add_parser(name)
        p.add_argument("--raw", type=Path, default=DEFAULT_RAW)
        p.add_argument("--releases", type=Path, default=DEFAULT_RELEASES)
        if name == "fetch":
            p.add_argument("--contact", required=True, help="goes into the User-Agent only; never written")
            p.add_argument("--cap", type=int, default=DEFAULT_CAP)
            p.add_argument("--pause", type=float, default=1.0, help="seconds between requests")
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
            manifest = fetch(
                args.raw,
                args.releases,
                contact=args.contact,
                gate=gate,
                commit=_code_commit(),
                cap=args.cap,
                pause=args.pause,
            )
            print(f"requests {manifest['requests']}")
            print(f"files {len(manifest['files'])}")
            return 0
        result, failures = run_compare(args.raw, args.releases)
    except (RightsRefused, ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    if failures:
        print(f"refused: {len(failures)} release(s) could not be parsed", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 2
    args.releases.mkdir(parents=True, exist_ok=True)
    (args.releases / "comparison.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    with (args.releases / "differences.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["release", "role", "month", "printed", "flat"])
        writer.writerows(
            [d["release"], d["role"], d["month"], d["printed"], d["flat"]] for d in result["differences"]
        )
    print(f"releases {result['releases']}")
    print(f"months {result['months']}")
    print(f"observations equal {result['observations_equal']}")
    print(f"observations different {result['observations_different']}")
    print(f"observations not printed {result['observations_not_printed']}")
    print(f"reading: {result['reading']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
