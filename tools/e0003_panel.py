"""T-0023 step 2 (OD-0177): one command that rebuilds the AUD defensive-sleeve panel and comparison.

    uv run --with xlrd==2.0.1 python tools/e0003_panel.py rebuild

Every step starts from retained bytes: E-0002's raw snapshot (never its store), the F1 receipt, H.10's
archive and the RBA's historical .xls, which is extracted again. Nothing is fetched. Each run writes a new
directory under ~/.hio-research/T-0023/runs/ and touches no earlier workspace. Values stay there; stdout and
the repository hold hashes, counts and classes only. Exploratory: this shows what ran, not that any input is
right.

Release ids hold the code revision, so they change at every commit. The panel id doesn't: it covers the input
bytes, the conventions and the panel's own text.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import sys
import zipfile
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import e0002_aud as aud_tool
import e0003_aud_cash as base
import e0003_extended as ext
import eodhd_eval as ev
import rba_history_fetch as history_tool
from hio.contracts.canonical import canonical_json, instant_str
from hio.contracts.observation import parse_instant
from hio.contracts.rights import Operation
from hio.contracts.temporal import KnowledgeMode
from hio.rights.gate import RightsGate
from hio.sources.datasets import parse_rba_f1
from hio.storage.objectstore import LocalObjectStore
from research_reader import Pin, read_panel

SCHEMA = "hio.t0023.aud_defensive_sleeve_panel/1"
SNAPSHOT = "s2"
XLRD = "2.0.1"
# The values file E-0003 V1 recorded, at 7d4ef02 and again at cae1318 (handoff 2026-11-04).
RECORDED_V1_VALUES_SHA256 = "8720540764da7151970e598ab7c671aa5c9b1bf47b557ec0f2a2339d5a6c6bc9"
FROZEN_PANEL_ID: str | None = "1aa2991815b03ba2acc908b0bf3655faae45199a04991181aeb8975ff2e58190"
CONVENTIONS = {
    "aonia_series": ext.AONIA,
    "cash": "ACT/365 simple accrual of published rates, joined to the TRI at its first level",
    "fx": "RA 4.1 on H.10 noon New York",
    "fx_max_stale_days": aud_tool.MAX_STALE_DAYS,
    "knowledge_mode": KnowledgeMode.LATEST.value,
    "max_stale_days": base.MAX_STALE_DAYS,
    "panel_columns": ["period_start", "period_end", *base.SLEEVES, "usd_bills", "fx_return"],
    "spec_version": ev.SPEC_VERSION,
    "tri_series": base.TRI_SERIES,
    "tri_start": ext.TRI_START.isoformat(),
    "vehicles": {sleeve: symbol for sleeve, (symbol, _) in ev.SLEEVES.items()},
}
Extract = Callable[[Path], list[tuple[str, str]]]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot_inputs(e0002: Path, manifest: Mapping[str, Any], snapshot: str) -> dict[str, str]:
    """The snapshot's manifest, naming every file's hash and retrieval time, and the files the panel reads."""
    used = {symbol for symbol, _ in ev.SLEEVES.values()} | {"EXCHANGE.US"}
    out = {"manifest.json": sha256((ev.snapshot_dir(e0002, snapshot) / "manifest.json").read_bytes())}
    out |= {f["path"]: f["sha256"] for f in manifest["files"] if f["symbol"] in used}
    return dict(sorted(out.items()))


def check_extract(history: Path, extract: Extract) -> tuple[str, str]:
    """The series extracted again from the retained .xls must equal the retained extract, byte for byte."""
    source = json.loads((history / "manifest.json").read_text())
    raw = (history / history_tool.FILE_NAME).read_bytes()
    if sha256(raw) != source["sha256"]:
        raise ev.Stop("the retained .xls doesn't match its manifest")
    meta = json.loads((history / "extract-manifest.json").read_text())
    if meta["from_file_sha256"] != source["sha256"]:
        raise ev.Stop("the retained extract names another .xls")
    rows = extract(history / history_tool.FILE_NAME)
    body = "date,rate_pct\n" + "".join(f"{d},{r}\n" for d, r in rows)
    if sha256(body.encode()) != meta["sha256"] or body.encode() != (history / "firmmcrid.csv").read_bytes():
        raise ev.Stop("extracting the .xls again doesn't give the retained extract")
    return source["sha256"], meta["sha256"]


def read_history(body: bytes) -> dict[date, Decimal]:
    rows = csv.DictReader(body.decode().splitlines())
    rates = {date.fromisoformat(r["date"]): Decimal(r["rate_pct"]) for r in rows}
    if not rates:
        raise ev.Stop("no historical rates")
    return rates


def panel_text(built: ext.Assembled) -> str:
    """Twelve decimals, so a last-bit difference in floating point between machines doesn't change the id."""
    lines = [",".join(CONVENTIONS["panel_columns"])]
    for i in range(built.returns.shape[0]):
        cells = [*built.returns[i], built.usd_bills[i], built.s[i]]
        lines.append(
            ",".join(
                [built.months[i].isoformat(), built.months[i + 1].isoformat(), *(f"{c:.12f}" for c in cells)]
            )
        )
    return "\n".join(lines) + "\n"


def panel_id(inputs: Mapping[str, Any], panel_sha256: str) -> str:
    """Input bytes, conventions and the panel's text; not the code revision, so an unchanged panel keeps it"""
    return sha256(
        canonical_json(
            {
                "schema": SCHEMA,
                "inputs": dict(inputs),
                "conventions": CONVENTIONS,
                "panel_sha256": panel_sha256,
            }
        )
    )


def build_usd_panel(
    e0002: Path,
    manifest: Mapping[str, Any],
    store: LocalObjectStore,
    *,
    gate: RightsGate,
    code: Mapping[str, str],
) -> tuple[Any, dict[str, str]]:
    """Each sleeve's return from raw closes and actions, into this run's own store, read back under the
    reader's checks. E-0002's own `run` isn't used: it deletes the store it writes to."""
    listing = ev._read(e0002, manifest, "EXCHANGE.US", "symbols")
    series = {}
    for symbol, _ in ev.SLEEVES.values():
        series[symbol] = ev.analyse(
            symbol,
            ev.ETFS[symbol],
            ev.quote_currency(listing, symbol),
            ev._read(e0002, manifest, symbol, "eod"),
            ev._read(e0002, manifest, symbol, "div"),
            ev._read(e0002, manifest, symbol, "splits"),
        )
        if not all(series[symbol].qualified.values()):
            raise ev.Stop(f"{symbol} didn't qualify")
    hashes, cutoff = ev.write_releases(e0002, store, manifest, series, gate=gate, code=code)
    panel, _ = read_panel(
        store,
        [Pin(sleeve, ev.SLEEVES[sleeve][1], sha) for sleeve, sha in hashes.items()],
        mode=KnowledgeMode.LATEST,
        cutoff=parse_instant(instant_str(cutoff)),
        gate=gate,
    )
    return panel, hashes


def release_data(store_root: Path, hashes: Mapping[str, str]) -> dict[str, str]:
    return {
        sleeve: sha256((store_root / "releases" / ev.SLEEVES[sleeve][1] / sha / "data.csv").read_bytes())
        for sleeve, sha in sorted(hashes.items())
    }


def versions(names: Iterable[str]) -> dict[str, str]:
    out = {"python": platform.python_version()}
    for name in names:
        out[name] = importlib.metadata.version(name)
    return out


def default_extract(path: Path) -> list[tuple[str, str]]:
    try:
        return history_tool.extract_series(path)
    except ImportError as exc:
        raise ev.Stop(f"run it under uv run --with xlrd=={XLRD}") from exc


def rebuild(
    root: Path,
    e0002: Path,
    e0003: Path,
    h10: Path,
    history: Path,
    *,
    gate: RightsGate,
    code: Mapping[str, str],
    extract: Extract = default_extract,
    frozen: str | None = FROZEN_PANEL_ID,
    recorded_values: str = RECORDED_V1_VALUES_SHA256,
    command: str = "",
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    tool_versions: Callable[[], dict[str, str]] = lambda: versions(("numpy", "xlrd")),
) -> dict[str, Any]:
    for path in (root, e0002, e0003):
        ev.check_root(path)
    for source in (ext.HISTORY_SOURCE, base.RBA_SOURCE, aud_tool.H10_SOURCE, ev.SOURCE_ID):
        gate.authorise(Operation.BUILD, [source])

    manifest = ev.load_snapshot(e0002, SNAPSHOT)
    f1_meta = json.loads((e0003 / "raw" / "manifest.json").read_text())
    f1 = (e0003 / "raw" / "rba_f1.csv").read_bytes()
    if sha256(f1) != f1_meta["receipt_id"]:
        raise ev.Stop("the retained F1 bytes don't match their manifest")
    h10_meta = json.loads((h10 / "manifest.json").read_text())
    h10_bytes = (h10 / "FRB_h10_xml.zip").read_bytes()
    if sha256(h10_bytes) != h10_meta["sha256"]:
        raise ev.Stop("the retained H.10 archive doesn't match its manifest")
    xls_sha, extract_sha = check_extract(history, extract)
    inputs = {
        "eodhd_snapshot": {"name": SNAPSHOT, "files": snapshot_inputs(e0002, manifest, SNAPSHOT)},
        "rba_f1_receipt": f1_meta["receipt_id"],
        "rba_f1_historical_xls": xls_sha,
        "rba_firmmcrid_extract": extract_sha,
        "frb_h10_zip": h10_meta["sha256"],
    }

    stamp = now().strftime("%Y%m%dT%H%M%SZ")
    run_dir = root / "runs" / f"{stamp}-{code['commit'][:8]}"
    run_dir.mkdir(mode=0o700, parents=True)
    store = LocalObjectStore(run_dir / "store")
    panel, hashes = build_usd_panel(e0002, manifest, store, gate=gate, code=code)
    ev.make_private(run_dir / "store")

    data = release_data(run_dir / "store", hashes)
    recorded = json.loads((e0002 / "summary.json").read_text())
    recorded_data = release_data(e0002 / "store", recorded["releases"])

    tri = base.parse_tri(f1)
    aonia = {row.valid_time: row.value for row in parse_rba_f1({ext.AONIA: "aonia"})(f1).rows}
    with zipfile.ZipFile(h10 / "FRB_h10_xml.zip") as archive:
        fx, _ = aud_tool.parse_h10(archive.read("H10_data.xml"))
    built = ext.assemble(panel, read_history((history / "firmmcrid.csv").read_bytes()), aonia, tri, fx)
    results = base.evaluate(built.months, built.returns, built.usd_bills, built.s, ext.WINDOWS)

    text = panel_text(built)
    panel_sha = sha256(text.encode())
    identity = panel_id(inputs, panel_sha)
    values = (json.dumps(results, indent=1, sort_keys=True) + "\n").encode()
    values_sha = sha256(values)
    report = ext.render(results, built.seam) + f"\nPanel id `{identity}`. Run `{run_dir.name}`.\n"
    checks = {
        "release_data_equals_recorded": data == recorded_data,
        "values_equal_recorded_v1": values_sha == recorded_values,
        "seam_check_passes": bool(built.seam["passes"]),
        "panel_id_equals_frozen": None if frozen is None else identity == frozen,
    }
    out = {
        "schema": SCHEMA,
        "panel_id": identity,
        "panel_sha256": panel_sha,
        "values_sha256": values_sha,
        "report_sha256": sha256(report.encode()),
        "run_dir": str(run_dir),
        "command": command,
        "started_at": now().isoformat(),
        "code": dict(code),
        "versions": tool_versions(),
        "conventions": CONVENTIONS,
        "inputs": inputs,
        "release_ids_this_run": hashes,
        "release_data_sha256": data,
        "first_month": built.months[0].isoformat(),
        "last_month": built.months[-1].isoformat(),
        "months": int(built.returns.shape[0]),
        "history_rates_used": built.history_rates_used,
        **{k: built.facts[k] for k in ("rates_not_on_the_day", "oldest_rate_days")},
        "seam_check": built.seam,
        "interval_classes": base.interval_classes(results),
        "checks": checks,
    }
    ev.private_write(run_dir / "panel.csv", text.encode())
    ev.private_write(run_dir / "values.json", values)
    ev.private_write(run_dir / "report.md", report.encode())
    ev.private_write(run_dir / "run.json", (json.dumps(out, indent=1, sort_keys=True) + "\n").encode())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["rebuild"])
    research = Path.home() / ".hio-research"
    parser.add_argument("--root", type=Path, default=research / "T-0023")
    parser.add_argument("--e0002", type=Path, default=research / "E-0002-eodhd")
    parser.add_argument("--e0003", type=Path, default=research / "E-0003")
    parser.add_argument("--h10", type=Path, default=research / "H10")
    parser.add_argument("--history", type=Path, default=research / "RBA-F1-history")
    args = parser.parse_args(argv)
    try:
        args.root.mkdir(mode=0o700, exist_ok=True)
        out = rebuild(
            args.root,
            args.e0002,
            args.e0003,
            args.h10,
            args.history,
            gate=ev.make_gate(),
            code=ev.code_commit(),
            command=f"uv run --with xlrd=={XLRD} python tools/e0003_panel.py rebuild",
        )
    except Exception as exc:  # the type only: a message could hold a value
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    keys = (
        "panel_id",
        "panel_sha256",
        "values_sha256",
        "report_sha256",
        "run_dir",
        "code",
        "versions",
        "first_month",
        "last_month",
        "months",
        "seam_check",
        "interval_classes",
        "checks",
    )
    print(json.dumps({k: out[k] for k in keys}, indent=1, sort_keys=True))
    failed = [name for name, passed in out["checks"].items() if passed is False]
    if failed:
        print(f"differs: {', '.join(failed)}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
