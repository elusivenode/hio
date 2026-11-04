"""The one-off Treasury par yield curve download for E-0001 (T-0020 X-3, OD-0157, OD-0161).

One request per calendar year, at most MAX_REQUESTS, from the published XML feed. It stops at the first
surprise and keeps what it has, because a retry or a re-run would be a second download. The genuine rights
gate must allow fetch and raw storage first. --output holds real values, so it must be absent or empty, and
outside the repository. A dirty tree refuses, so the manifest names exactly what ran. It never prints a value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine

REPO = Path(__file__).resolve().parent.parent
SOURCE_ID = "us_treasury.par_yield_curve"
FEED = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
    "?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
)
USER_AGENT = "HIO-research/0.1 (one-off historical download; non-commercial research)"
NOTICE = "Source: US Department of the Treasury. No endorsement by the Treasury is implied."
FIRST_YEAR = 1990
MAX_REQUESTS = 40
PAUSE_SECONDS = 2.0
Getter = Callable[[str], tuple[int, bytes]]


def http_get(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:  # a fixed https URL
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def check_output(output: Path) -> None:
    resolved = output.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--output must lie outside the repository")
    if output.exists() and any(output.iterdir()):
        raise ValueError("--output must be absent or empty")


def code_commit() -> str:
    git = ("git", "-C", str(REPO))
    status = subprocess.run((*git, "status", "--porcelain"), capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise ValueError("the working tree has uncommitted changes")
    return subprocess.run(
        (*git, "rev-parse", "HEAD"), capture_output=True, text=True, check=True
    ).stdout.strip()


def fetch(
    output: Path,
    years: list[int],
    *,
    gate: RightsGate,
    commit: str,
    get: Getter = http_get,
    pause: float = PAUSE_SECONDS,
) -> dict:
    """Returns the manifest, also written to --output. `stopped` names why it stopped early, if it did."""
    if len(years) > MAX_REQUESTS:
        raise ValueError(f"{len(years)} requests is over the limit of {MAX_REQUESTS}")
    check_output(output)
    gate.authorise(Operation.FETCH, [SOURCE_ID])
    gate.authorise(Operation.STORE_RAW, [SOURCE_ID])
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    files, stopped = [], None
    for index, year in enumerate(years):
        if index:
            time.sleep(pause)
        url = FEED.format(year=year)
        at = datetime.now(UTC).isoformat()
        try:
            status, body = get(url)
        except OSError as exc:
            stopped = f"{year}: {type(exc).__name__}"
            break
        if status != 200:
            stopped = f"{year}: HTTP {status}"
            break
        if b"<entry" not in body and b"<feed" not in body:
            stopped = f"{year}: not the expected feed"
            break
        path = raw / f"{year}.xml"
        path.write_bytes(body)
        files.append(
            {
                "year": year,
                "url": url,
                "retrieved_at": at,
                "path": f"raw/{year}.xml",
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )
    manifest = {
        "experiment": "E-0001",
        "source_id": SOURCE_ID,
        "notice": NOTICE,
        "knowledge": "reconstructed(T): one one-off download; no publication instant is claimed",
        "user_agent": USER_AGENT,
        "code_commit": commit,
        "requested_years": years,
        "files": files,
        "stopped": stopped,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--last-year", type=int, required=True)
    args = parser.parse_args(argv)
    gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
    try:
        manifest = fetch(
            args.output, list(range(FIRST_YEAR, args.last_year + 1)), gate=gate, commit=code_commit()
        )
    except (RightsRefused, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    done, asked = len(manifest["files"]), len(manifest["requested_years"])
    print(f"files {done} of {asked}; stopped: {manifest['stopped']}")
    return 0 if manifest["stopped"] is None else 1


if __name__ == "__main__":
    sys.exit(main())
