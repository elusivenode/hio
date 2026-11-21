"""The one bounded BLS CPI download (OD-0189, under the bls_cpi rights record, OD-0188).

One run makes at most 20 HTTP requests: the CPI-U all-items series (CUUR0000SA0) from the BLS public API v1
in spans of at most ten years, the CPI release archive page, and up to 12 archived releases chosen evenly
across the dates parsed from that page. Every response is saved verbatim. --output must be absent or empty
and outside the repository, so a re-run can't download again, and a dirty tree refuses so the manifest names
what ran. The contact given in --contact goes into the request User-Agent only: it is never written to a
file, the manifest, a message or stdout.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine

REPO = Path(__file__).resolve().parent.parent
SOURCE_ID = "bls_cpi"
SERIES_ID = "CUUR0000SA0"
API_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
ARCHIVE_URL = "https://www.bls.gov/bls/news-release/cpi.htm"
SITE = "https://www.bls.gov"
FIRST_YEAR = 2005
SPAN_YEARS = 10
MAX_REQUESTS = 20
MAX_RELEASES = 12
REDACTED_CONTACT = "<owner contact>"
USER_AGENT_TEMPLATE = (
    "HIO-research/0.1 (one-off CPI download for non-commercial research; contact: {contact})"
)
NOTICE = (
    "Source: U.S. Bureau of Labor Statistics, CPI-U (CUUR0000SA0), retrieved {date}. BLS.gov cannot vouch "
    "for the data or analyses derived from these data after the data have been retrieved from BLS.gov."
)
LINK = re.compile(r"/news\.release/archives/cpi_(\d{2})(\d{2})(\d{4})\.(htm|pdf)", re.IGNORECASE)

Getter = Callable[[str, str], tuple[int, bytes]]
Poster = Callable[[str, bytes, str], tuple[int, bytes]]


def http_get(url: str, user_agent: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def http_post(url: str, payload: bytes, user_agent: str) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url, data=payload, headers={"User-Agent": user_agent, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def year_spans(last_year: int, first_year: int = FIRST_YEAR) -> list[tuple[int, int]]:
    if last_year < first_year:
        raise ValueError("the last year precedes the first")
    return [(y, min(y + SPAN_YEARS - 1, last_year)) for y in range(first_year, last_year + 1, SPAN_YEARS)]


def parse_release_links(html: str) -> list[tuple[date, str]]:
    """Sorted, de-duplicated (date, url) pairs; links with an impossible date are ignored.

    When a date has both an .htm and a .pdf link the .htm is kept.
    """
    found: dict[date, str] = {}
    for month, day, year, ext in LINK.findall(html):
        try:
            when = date(int(year), int(month), int(day))
        except ValueError:
            continue
        url = f"{SITE}/news.release/archives/cpi_{month}{day}{year}.{ext.lower()}"
        if when not in found or ext.lower() == "htm":
            found[when] = url
    return sorted(found.items())


def choose_evenly(items: list, count: int) -> list:
    """`count` items evenly spaced across `items`, first and last included (a single pick is the last)."""
    if count < 1:
        raise ValueError("the number of releases must be at least 1")
    count = min(count, len(items))
    if count == 0:
        return []
    if count == 1:
        return [items[-1]]
    last = len(items) - 1
    return [items[round(i * last / (count - 1))] for i in range(count)]


class Budget:
    """Counts HTTP requests and refuses the one past the limit."""

    def __init__(self, limit: int, get: Getter, post: Poster, user_agent: str) -> None:
        self.limit = limit
        self.count = 0
        self._get = get
        self._post = post
        self._user_agent = user_agent

    def _spend(self) -> None:
        if self.count >= self.limit:
            raise ValueError(f"more than {self.limit} requests would be needed")
        self.count += 1

    def get(self, url: str) -> bytes:
        self._spend()
        status, body = self._get(url, self._user_agent)
        if status != 200:
            raise ValueError(f"HTTP {status} for {url}")
        return body

    def post(self, url: str, payload: dict) -> bytes:
        self._spend()
        status, body = self._post(url, json.dumps(payload).encode(), self._user_agent)
        if status != 200:
            raise ValueError(f"HTTP {status} for {url}")
        return body


def _check_contact(contact: str) -> str:
    contact = contact.strip()
    if not contact or any(ch in contact for ch in "\r\n\t") or not contact.isprintable():
        raise ValueError("--contact must be a non-empty single printable line")
    return contact


def fetch(
    output: Path,
    *,
    gate: RightsGate,
    commit: str,
    contact: str,
    get: Getter = http_get,
    post: Poster = http_post,
    releases: int = MAX_RELEASES,
    now: datetime | None = None,
    max_requests: int = MAX_REQUESTS,
) -> dict:
    contact = _check_contact(contact)
    if not 1 <= releases <= MAX_RELEASES:
        raise ValueError(f"--releases must be between 1 and {MAX_RELEASES}")
    resolved = output.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--output must lie outside the repository")
    if output.exists() and any(output.iterdir()):
        raise ValueError("--output must be absent or empty")
    gate.authorise(Operation.FETCH, [SOURCE_ID])
    gate.authorise(Operation.STORE_RAW, [SOURCE_ID])
    moment = now or datetime.now(UTC)
    agent = USER_AGENT_TEMPLATE.format(contact=contact)
    budget = Budget(max_requests, get, post, agent)
    files: list[tuple[str, str, bytes]] = []  # name, url, body

    for first, last in year_spans(moment.year):
        body = budget.post(API_URL, {"seriesid": [SERIES_ID], "startyear": str(first), "endyear": str(last)})
        try:
            status = json.loads(body).get("status")
        except (ValueError, AttributeError):
            raise ValueError(f"the API answer for {first}-{last} is not a JSON object") from None
        if status != "REQUEST_SUCCEEDED":
            raise ValueError(f"the API answer for {first}-{last} has status {status!r}")
        files.append((f"cpi_series_{first}_{last}.json", API_URL, body))

    archive = budget.get(ARCHIVE_URL)
    files.append(("cpi_release_archive.htm", ARCHIVE_URL, archive))
    dated = parse_release_links(archive.decode("utf-8", errors="replace"))
    if not dated:
        raise ValueError("no release dates were parsed from the archive page")
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["date", "url"])
    writer.writerows((when.isoformat(), url) for when, url in dated)
    csv_bytes = out.getvalue().encode()

    for when, url in choose_evenly(dated, releases):
        files.append((f"cpi_{when:%m%d%Y}{Path(url).suffix}", url, budget.get(url)))

    needle = contact.encode()
    if any(needle in body for _n, _u, body in files):
        raise ValueError("a response contains the contact string; nothing was written")

    at = moment.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    listing = [*files, ("release-dates.csv", ARCHIVE_URL, csv_bytes)]
    for name, _url, body in listing:
        (output / name).write_bytes(body)
    manifest = {
        "source_id": SOURCE_ID,
        "retrieved_at": at,
        "notice": NOTICE.format(date=moment.date().isoformat()),
        "user_agent": USER_AGENT_TEMPLATE.format(contact=REDACTED_CONTACT),
        "code_commit": commit,
        "requests": budget.count,
        "release_dates_parsed": len(dated),
        "knowledge": "reconstructed(T): one one-off download",
        "files": [
            {
                "name": name,
                "url": url if name != "release-dates.csv" else "derived from cpi_release_archive.htm",
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
            for name, url, body in listing
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contact", required=True, help="goes into the User-Agent only; never written")
    parser.add_argument("--releases", type=int, default=MAX_RELEASES)
    args = parser.parse_args(argv)
    gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
    try:
        manifest = fetch(
            args.output, gate=gate, commit=code_commit(), contact=args.contact, releases=args.releases
        )
    except (RightsRefused, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"requests {manifest['requests']}")
    print(f"files {len(manifest['files'])}")
    print(f"release dates parsed {manifest['release_dates_parsed']}")
    for entry in manifest["files"]:
        print(f"{entry['sha256']}  {entry['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
