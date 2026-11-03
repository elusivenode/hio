"""Repeatable local cash rebuild from retained receipts (T-0018; base-camp criterion 3's tool).

It reads every object of the evidence store with the identity of whoever runs it, copies them to a new local
store under --output, builds the four S1b-1 outputs for a stated history window under the genuine rights gate,
and writes the cash evidence report, the releases and a summary to --output. It never writes to the evidence
store, and it establishes nothing by itself: its result needs a written disposition.

--output holds real values, so it must be empty or absent and must lie outside the repository. A dirty working
tree refuses, because `code_ref` must name what ran. Exit 0 when the report is written, whatever it says; 2
when none can be produced, naming the error's type and never provider text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from hio.contracts.observation import parse_instant
from hio.jobs.s1b1 import Calendars, build_releases, ingest_pending, sofr_calendar, vintage_store
from hio.jobs.s1b1_capture import ENV_ACCOUNT_URL, ENV_CONTAINER, merge_calendars
from hio.jobs.s1b1_cash_evidence import build_report, render_json, render_markdown
from hio.reference.calendar import load_reference_calendar
from hio.rights.gate import GateContext, RightsGate
from hio.rights.register import load_genuine
from hio.storage.blobstore import BlobBackend, BlobObjectStore
from hio.storage.objectstore import LocalObjectStore

REPO = Path(__file__).resolve().parent.parent
BackendBuilder = Callable[[Mapping[str, str]], BlobBackend]


def default_backend(environ: Mapping[str, str]) -> BlobBackend:
    from azure.identity import DefaultAzureCredential

    from hio.storage.azure_blob import AzureBlobBackend, container_client

    return AzureBlobBackend(
        container_client(environ[ENV_ACCOUNT_URL], environ[ENV_CONTAINER], DefaultAzureCredential())
    )


def code_identity() -> dict[str, str]:
    """What ran. A dirty tree refuses: a rebuild must name its code exactly."""
    git = ("git", "-C", str(REPO))
    if subprocess.run(
        (*git, "status", "--porcelain"), capture_output=True, text=True, check=True
    ).stdout.strip():
        raise ValueError("the working tree has uncommitted changes")
    commit = subprocess.run(
        (*git, "rev-parse", "HEAD"), capture_output=True, text=True, check=True
    ).stdout.strip()
    return {"commit": commit, "lock_sha256": hashlib.sha256((REPO / "uv.lock").read_bytes()).hexdigest()}


def check_output(output: Path) -> None:
    resolved = output.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--output must lie outside the repository: it holds real values")
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError("--output must be empty: a window is fixed when a store is first built")


def rebuild(
    backend: BlobBackend,
    output: Path,
    cutoff: Any,
    history_from: date,
    rits_files: Sequence[str],
    nsw_files: Sequence[str],
    code_ref: Mapping[str, str],
    sources: Path = REPO / "registers" / "sources.yaml",
) -> dict[str, Any]:
    source = BlobObjectStore(backend)
    local = LocalObjectStore(output / "store")
    keys = list(source.list(""))
    for key in keys:
        local.put(key, source.get(key))
    calendars = Calendars(
        merge_calendars([load_reference_calendar(p) for p in rits_files]),
        merge_calendars([load_reference_calendar(p) for p in nsw_files]),
        sofr_calendar(local, cutoff),
    )
    store = vintage_store(local, calendars, earliest=history_from)
    ingested = ingest_pending(store, cutoff)
    register = load_genuine(sources)
    releases = build_releases(
        store,
        RightsGate(register, GateContext(on_external_host=False)),
        register,
        calendars,
        cutoff,
        dict(code_ref),
        history_from=history_from,
    )
    evidence = build_report(releases)
    (output / "report.json").write_bytes(render_json(evidence))
    (output / "report.md").write_text(render_markdown(evidence))
    for dataset_id, release in releases.items():
        folder = output / "releases" / dataset_id
        folder.mkdir(parents=True)
        for name, data in release.files.items():
            (folder / name).write_bytes(data)
    summary = {
        "objects_read": len(keys),
        "receipts_ingested": ingested,
        "history_from": history_from.isoformat(),
        "cutoff": evidence["cutoff"],
        "code": dict(code_ref),
        "outputs": {
            dataset_id: {
                "release_id": release.release_id,
                "rows": release.core["quality_summary"]["periods"],
            }
            for dataset_id, release in sorted(releases.items())
        },
        "classes": {
            cash_id: dict(sorted(Counter(p["class"] for p in currency["periods"]).items()))
            for cash_id, currency in sorted(evidence["currencies"].items())
        },
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    backend_builder: BackendBuilder = default_backend,
    code: Callable[[], Mapping[str, str]] = code_identity,
    sources: Path = REPO / "registers" / "sources.yaml",
) -> int:
    parser = argparse.ArgumentParser(prog="tools/cash_rebuild.py")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cutoff", required=True, type=parse_instant, help="knowledge cutoff, a UTC instant")
    parser.add_argument("--history-from", required=True, type=date.fromisoformat)
    parser.add_argument("--rits-calendar", required=True, action="append")
    parser.add_argument("--nsw-calendar", required=True, action="append")
    args = parser.parse_args(argv)
    try:
        check_output(args.output)
        code_ref = code()
        backend = backend_builder(os.environ if environ is None else environ)
        summary = rebuild(
            backend,
            args.output,
            args.cutoff,
            args.history_from,
            args.rits_calendar,
            args.nsw_calendar,
            code_ref,
            sources,
        )
    except Exception as error:  # name the type, never provider text
        detail = f": {error}" if isinstance(error, ValueError | LookupError) else ""
        print(f"no rebuild produced: {type(error).__name__}{detail}", file=sys.stderr)
        return 2
    print(json.dumps(summary["classes"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
