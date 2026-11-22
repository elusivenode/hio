"""Build one instrument's silver set from a pinned bronze snapshot and an observation spec (OD-0231).

Silver is the cleaned layer between bronze (bytes as fetched) and gold (series): one instrument's closes,
distributions and splits as CSV, with the corrections its observation spec declares applied once. The
contract is `docs/decisions/local-data-layers-proposal.md` (proposed; version 1 of the format).

The observation spec (`specs/observations/<SYMBOL>.<EXCHANGE>.yaml`) names the instrument, its source and
quote currency, and any `exclude_distribution` corrections. This tool verifies the pin and every retained
snapshot file, reads the three vendor files (`eod`, `div`, `splits`) and the exchange listing, applies the
corrections, and writes `closes.csv`, `distributions.csv`, `splits.csv` and `manifest.json` under
`<out>/<instrument>/<silver_id>/`. The files are written in a temporary directory beside the target and
renamed into place, so a failure leaves no half-written set. Values are exact text: a JSON number is written
as `format(Decimal, "f")` of its literal, a string as it is, null or an absent field as an empty cell.

The output is never overwritten: the same inputs give the same bytes ("already built"), and a different set
at the same `silver_id` is refused. The command prints counts, ids and hashes only: never a date, a price,
an amount or a return from the data.

Where the contract is silent (choices made here): dates must be ISO strings in every file, and unique and
ascending in the closes only (a duplicate distribution is exactly what a correction removes); a close must
be a positive number, `adjusted_close` may be empty; a snapshot manifest that names a `source_id` must agree
with the spec's; the quote currency must be settled by the listing and equal the spec's.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("eodhd_eval_for_silver_build", _HERE / "eodhd_eval.py")
_base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _base
_spec.loader.exec_module(_base)

REPO = _base.REPO
SCHEMA = "hio.silver/1"
CORRECTION_ACTION = "exclude_distribution"  # the only action (OD-0230, OD-0231)
SPEC_KEYS = frozenset({"identity", "source", "corrections", "changelog"})
IDENTITY_KEYS = frozenset({"instrument", "version", "status"})
SOURCE_KEYS = frozenset({"source_id", "quote_currency"})
CORRECTION_KEYS = frozenset({"action", "ex_date", "reason", "evidence"})
INSTRUMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+)+")
HEX = re.compile(r"[0-9a-f]{64}")

CLOSES_HEADER = ("date", "close", "adjusted_close")
DISTRIBUTIONS_HEADER = (
    "ex_date",
    "amount",
    "split_adjusted_amount",
    "currency",
    "payment_date",
    "record_date",
    "declaration_date",
    "period",
)
SPLITS_HEADER = ("date", "ratio")
CLOSES_FILE = "closes.csv"
DISTRIBUTIONS_FILE = "distributions.csv"
SPLITS_FILE = "splits.csv"
MANIFEST_FILE = "manifest.json"
CSV_FILES = (CLOSES_FILE, DISTRIBUTIONS_FILE, SPLITS_FILE)
# vendor key for each distributions.csv column after ex_date
DISTRIBUTION_FIELDS = (
    ("date", "ex_date"),
    ("unadjustedValue", "amount"),
    ("value", "split_adjusted_amount"),
    ("currency", "currency"),
    ("paymentDate", "payment_date"),
    ("recordDate", "record_date"),
    ("declarationDate", "declaration_date"),
    ("period", "period"),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_iso_date(value: object) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def read_observation_spec(path: Path) -> dict:
    """The fields of an observation spec, validated, with the file's sha256. Refuses with ValueError."""
    raw = Path(path).read_bytes()
    try:
        spec = yaml.safe_load(raw)
    except yaml.YAMLError:
        raise ValueError("the observation spec is not valid YAML") from None
    if not isinstance(spec, dict) or set(spec) != SPEC_KEYS:
        raise ValueError(f"the observation spec must have exactly the keys {', '.join(sorted(SPEC_KEYS))}")
    identity, source = spec["identity"], spec["source"]
    if not isinstance(identity, dict) or set(identity) != IDENTITY_KEYS:
        raise ValueError(f"identity must have exactly the keys {', '.join(sorted(IDENTITY_KEYS))}")
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        raise ValueError(f"source must have exactly the keys {', '.join(sorted(SOURCE_KEYS))}")
    for owner, keys in ((identity, IDENTITY_KEYS), (source, SOURCE_KEYS)):
        for key in keys:
            if not _nonempty_string(owner[key]):
                raise ValueError(f"{key} must be a non-empty string")
    instrument = identity["instrument"]
    if not INSTRUMENT.fullmatch(instrument) or ".." in instrument:
        raise ValueError("instrument must be <SYMBOL>.<EXCHANGE> and a safe directory name")
    changelog = spec["changelog"]
    if not isinstance(changelog, list) or not all(isinstance(line, str) for line in changelog):
        raise ValueError("changelog must be a list of strings")
    return {
        "instrument": instrument,
        "version": identity["version"],
        "status": identity["status"],
        "source_id": source["source_id"],
        "quote_currency": source["quote_currency"],
        "corrections": _read_corrections(spec["corrections"]),
        "changelog": changelog,
        "sha256": _sha(raw),
    }


def _read_corrections(corrections: object) -> list[dict]:
    if not isinstance(corrections, list) or not all(isinstance(c, dict) for c in corrections):
        raise ValueError("corrections must be a list of mappings")
    seen: set[str] = set()
    for correction in corrections:
        if set(correction) != CORRECTION_KEYS:
            raise ValueError(
                f"each correction must have exactly the keys {', '.join(sorted(CORRECTION_KEYS))}"
            )
        if correction["action"] != CORRECTION_ACTION:
            raise ValueError(f"a correction's action must be {CORRECTION_ACTION}")
        if not _is_iso_date(correction["ex_date"]):
            raise ValueError("a correction's ex_date must be an ISO date string")
        for key in ("reason", "evidence"):
            if not _nonempty_string(correction[key]):
                raise ValueError(f"a correction's {key} must be a non-empty string")
        if correction["ex_date"] in seen:
            raise ValueError("two corrections share an ex_date")
        seen.add(correction["ex_date"])
    return corrections


def check_out(out: Path) -> Path:
    resolved = Path(out).resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--out must lie outside the repository")
    return resolved


def _cell(value: object) -> str:
    """Exact text: a number as `format(Decimal, "f")`, a string as it is, null or absent as empty."""
    if value is None:
        return ""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("a vendor number is not finite")
        return format(value, "f")
    if isinstance(value, str):
        return value
    raise ValueError("a vendor field is neither a number, a string nor null")


def _csv_bytes(header: tuple[str, ...], rows: list[list[str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _require_records(records: object, kind: str) -> list[dict]:
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError(f"the {kind} file must be a list of records")
    for record in records:
        if not _is_iso_date(record.get("date")):
            raise ValueError(f"every {kind} record needs an ISO date")
    return records


def _positive_amount(record: dict) -> bool:
    raw = record.get("unadjustedValue")
    if raw is None:
        return False
    try:
        return Decimal(str(raw)) > 0
    except ArithmeticError:
        return False


def apply_corrections(dividends: list[dict], corrections: list[dict]) -> tuple[list[dict], list[dict]]:
    """Remove, for each correction, the one distribution record on its `ex_date` with a positive
    `unadjustedValue`. Returns (kept records in their original order, the applied list). Refuses with
    ValueError unless exactly one record matches; the message has the count, never an amount."""
    drop: set[int] = set()
    applied = []
    for correction in corrections:
        ex_date = correction["ex_date"]
        matches = [
            i for i, r in enumerate(dividends) if str(r.get("date")) == ex_date and _positive_amount(r)
        ]
        if len(matches) != 1:
            raise ValueError(f"a correction must match exactly one distribution record, not {len(matches)}")
        drop.add(matches[0])
        digest = _sha(json.dumps(dividends[matches[0]], sort_keys=True, default=str).encode("utf-8"))
        applied.append({"action": correction["action"], "ex_date": ex_date, "record_sha256": digest})
    return [r for i, r in enumerate(dividends) if i not in drop], applied


def _closes_rows(eod: list[dict]) -> list[list[str]]:
    if not eod:
        raise ValueError("the eod file has no rows")
    previous = None
    for record in eod:
        close = record.get("close")
        if not isinstance(close, Decimal) or not close.is_finite() or close <= 0:
            raise ValueError("a close must be a positive number")
        if previous is not None and record["date"] <= previous:
            raise ValueError("close dates must be unique and ascending")
        previous = record["date"]
    return [[_cell(r["date"]), _cell(r["close"]), _cell(r.get("adjusted_close"))] for r in eod]


def _expected_files(spec: dict, root: Path, manifest: dict) -> dict:
    instrument = spec["instrument"]
    entries = {}
    for kind in _base.KINDS:
        found = [f for f in manifest["files"] if f["symbol"] == instrument and f["kind"] == kind]
        if not found:
            raise ValueError(f"the snapshot has no {kind} file for the instrument")
        entries[kind] = found[0]
    exchange = f"EXCHANGE.{instrument.rsplit('.', 1)[1]}"
    listing = [f for f in manifest["files"] if f["symbol"] == exchange and f["kind"] == "symbols"]
    if not listing:
        raise ValueError("the snapshot has no exchange symbol list for the instrument")
    if "source_id" in manifest and manifest["source_id"] != spec["source_id"]:
        raise ValueError("the snapshot's source_id differs from the spec's")
    listed = _base.quote_currency(_base._read(root, manifest, exchange, "symbols"), instrument)
    if listed is None or listed != spec["quote_currency"]:
        raise ValueError("the snapshot's listed quote currency differs from the spec's")
    eod = _require_records(_base._read(root, manifest, instrument, "eod"), "eod")
    dividends = _require_records(_base._read(root, manifest, instrument, "div"), "div")
    splits = _require_records(_base._read(root, manifest, instrument, "splits"), "splits")
    closes = _closes_rows(eod)
    kept, applied = apply_corrections(dividends, spec["corrections"])
    distributions = [[_cell(r.get(vendor)) for vendor, _column in DISTRIBUTION_FIELDS] for r in kept]
    split_rows = [[_cell(r["date"]), _cell(r.get("split"))] for r in splits]
    files = {
        CLOSES_FILE: (_csv_bytes(CLOSES_HEADER, closes), len(closes)),
        DISTRIBUTIONS_FILE: (_csv_bytes(DISTRIBUTIONS_HEADER, distributions), len(distributions)),
        SPLITS_FILE: (_csv_bytes(SPLITS_HEADER, split_rows), len(split_rows)),
    }
    inputs = sorted(
        ({"path": e["path"], "sha256": e["sha256"]} for e in [*entries.values(), *listing]),
        key=lambda i: i["path"],
    )
    return {
        "files": files,
        "inputs": inputs,
        "corrections": applied,
        "first": closes[0][0],
        "last": closes[-1][0],
    }


def _make_dirs(target: Path) -> None:
    """Create `target` and any missing parents, each mode 0o700."""
    missing, directory = [], target
    while not directory.exists():
        missing.append(directory)
        directory = directory.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        directory.chmod(0o700)


def _write_new(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    path.chmod(0o600)


def build(spec_path, root, snapshot, manifest_sha256, out, *, commit) -> tuple[dict, bool]:
    """Build one silver set; returns (manifest, already_built). `commit` is the code commit, given by the
    caller (only `main` looks it up). Refuses with ValueError."""
    out = check_out(Path(out))
    if not isinstance(commit, str) or not commit.strip():
        raise ValueError("the code commit must be a non-empty string")
    root = Path(root)
    spec = read_observation_spec(Path(spec_path))
    manifest_path = _base.snapshot_dir(root, snapshot) / "manifest.json"
    manifest_hash = _sha(manifest_path.read_bytes())
    if not HEX.fullmatch(str(manifest_sha256).lower()) or manifest_hash != str(manifest_sha256).lower():
        raise ValueError("the snapshot manifest does not match the pin")
    snapshot_manifest = _base.load_snapshot(root, snapshot)  # verifies every retained file
    built = _expected_files(spec, root, snapshot_manifest)
    silver_id = _sha((spec["sha256"] + manifest_hash + commit).encode())[:16]
    files = built["files"]
    manifest = {
        "schema": SCHEMA,
        "instrument": spec["instrument"],
        "quote_currency": spec["quote_currency"],
        "source_id": spec["source_id"],
        "observation_spec": {"version": spec["version"], "sha256": spec["sha256"]},
        "snapshot": snapshot,
        "snapshot_manifest_sha256": manifest_hash,
        "inputs": built["inputs"],
        "corrections": built["corrections"],
        "code_commit": commit,
        "files": {name: {"sha256": _sha(data), "rows": rows} for name, (data, rows) in files.items()},
        "first": built["first"],
        "last": built["last"],
        "silver_id": silver_id,
    }
    contents = {name: data for name, (data, _rows) in files.items()}
    contents[MANIFEST_FILE] = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    target = out / spec["instrument"] / silver_id
    if target.exists() or target.is_symlink():
        present = {p.name: p for p in target.iterdir()} if target.is_dir() and not target.is_symlink() else {}
        if set(present) != set(contents) or any(
            not present[n].is_file() or present[n].is_symlink() or present[n].read_bytes() != data
            for n, data in contents.items()
        ):
            raise ValueError("the silver set exists with different bytes")
        return manifest, True
    _make_dirs(target.parent)
    staging = Path(tempfile.mkdtemp(dir=target.parent, prefix=".tmp-"))  # mode 0o700
    try:
        staging.chmod(0o700)
        for name, data in contents.items():
            _write_new(staging / name, data)
        os.rename(staging, target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest, False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        check_out(args.out)  # before any git lookup
        commit = _base.code_commit()["commit"]
        manifest, existed = build(
            args.spec, args.root, args.snapshot, args.manifest_sha256, args.out, commit=commit
        )
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print(f"instrument: {manifest['instrument']}")
    print(f"silver_id: {manifest['silver_id']}")
    for name in CSV_FILES:
        print(f"{name}: {manifest['files'][name]['rows']} rows")
    print(f"corrections: {len(manifest['corrections'])} applied")
    for name in CSV_FILES:
        print(f"{name} sha256: {manifest['files'][name]['sha256']}")
    manifest_bytes = (
        check_out(args.out) / manifest["instrument"] / manifest["silver_id"] / MANIFEST_FILE
    ).read_bytes()
    print(f"{MANIFEST_FILE} sha256: {_sha(manifest_bytes)}")
    if existed:
        print("already built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
