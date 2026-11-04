"""The one-off H.10 archive download for the AUD variant of E-0002 (T-0022, OD-0166, OD-0167).

One request for the Board's XML archive. --output must be absent or empty and outside the repository, so a
re-run can't download again, and a dirty tree refuses so the manifest names what ran. The archive holds other
currencies: they're retained as bytes and not used.
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
SOURCE_ID = "frb_h10.aud_usd"
URL = "https://www.federalreserve.gov/releases/h10/data/FRB_h10_xml.zip"
USER_AGENT = "HIO-research/0.1 (one-off historical download; non-commercial research)"
NOTICE = (
    "Source: Board of Governors of the Federal Reserve System, H.10. No endorsement by the Board is implied."
)
ZIP_MAGIC = b"PK\x03\x04"
Getter = Callable[[str], tuple[int, bytes]]


def http_get(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
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
    if not body.startswith(ZIP_MAGIC):
        raise ValueError("not a zip archive")
    output.mkdir(parents=True, exist_ok=True)
    (output / "FRB_h10_xml.zip").write_bytes(body)
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
    args = parser.parse_args(argv)
    gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
    try:
        manifest = fetch(args.output, gate=gate, commit=code_commit())
    except (RightsRefused, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"bytes {manifest['bytes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
