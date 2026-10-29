"""Restore exercise (T-0014 P-3; base-camp criterion 5): restore a second copy into an EMPTY store with no
access to the primary, then rebuild the releases and compare. Also rehearses state restoration with
dummy state. Non-live: it reads two local stores and an inventory; it contacts nothing.

    restore  verify the second copy against its sealed inventory, refuse a non-empty target, write every
             object, verify the target, and compare the canonical catalogue rows with the inventory's.
             There is no parameter for the primary store: the restore cannot read it.
    rebuild  rebuild the S1b-1 releases at a cutoff from the restored store, using the code reference and
             spec references PINNED in the stored manifests, and compare the manifest and every payload
             file byte for byte. The catalogue is compared as canonical rows, never as DuckDB file bytes.
    state    rehearse restoring an infrastructure-state backup into an isolated directory. It accepts
             only a file marked as dummy state, runs no infrastructure command and applies nothing.

Original provider metadata (blob version ids and provider write times) lives in the inventory and is never
overwritten: the restored objects get fresh timestamps from the target store, and those are not witnesses.
Every command reports and decides nothing about approval. Exit status: 0 all checks identical; 1 a check
differs; 2 refused input.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from hio.contracts.canonical import canonical_json, sha256_hex
from hio.contracts.observation import parse_instant
from hio.jobs.s1a import current_code_ref
from hio.jobs.s1b1 import Calendars, build_releases, sofr_calendar, vintage_store
from hio.jobs.s1b1_capture import SOURCES_REGISTER, merge_calendars
from hio.publish.release import Release
from hio.reference.calendar import BusinessCalendar, load_reference_calendar
from hio.rights.gate import RightsGate
from hio.rights.register import load_genuine
from hio.storage.blobstore import _rank
from hio.storage.objectstore import LocalObjectStore

REPO = Path(__file__).resolve().parent.parent
REPORT_FORMAT = "hio-restore-exercise-report/1"
DUMMY_MARKER = "hio_dummy_state"
STATE_FILE = "terraform.tfstate"


def _sibling(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


second_copy = _sibling("second_copy")


class ExerciseError(Exception):
    """The exercise was refused before it wrote anything."""


# --- restore -------------------------------------------------------------------------------------


def restore(second: Any, inventory_raw: bytes, target: Any) -> dict[str, Any]:
    """Restore `second` into the empty `target`. Nothing is written unless the second copy matches the
    inventory exactly. The primary is not a parameter: it is not needed and not available."""
    inventory = second_copy.load_inventory(inventory_raw)
    before = second_copy.check_store(second, inventory)
    if not before["ok"]:
        raise ExerciseError(f"the second copy does not match its inventory: {json.dumps(before)}")
    if next(iter(target.list()), None) is not None:
        raise ExerciseError("the target store is not empty")
    for e in sorted(inventory["entries"], key=lambda e: (_rank(e["key"]), e["key"])):
        target.put(e["key"], second.get(e["key"]))
    after = second_copy.check_store(target, inventory)
    restored_catalogue = second_copy.catalogue_sha256(target)
    originals = {e["key"]: e["provider"] for e in inventory["entries"]}
    return {
        "inventory_sha256": inventory["inventory_sha256"],
        "second_copy_check": before,
        "restored_objects": len(inventory["entries"]),
        "target_check": after,
        "catalogue": {
            "inventory_sha256": inventory["catalogue_sha256"],
            "restored_sha256": restored_catalogue,
            "identical": restored_catalogue == inventory["catalogue_sha256"],
        },
        "provider_metadata": {
            "original_entries": len(originals),
            "original_sha256": sha256_hex(canonical_json(originals)),
            "restored_write_times_are_witnesses": False,
        },
        "ok": after["ok"] and restored_catalogue == inventory["catalogue_sha256"],
    }


# --- rebuild -------------------------------------------------------------------------------------


def release_pins(store: Any, cutoff: str) -> dict[str, Any]:
    """The code reference, spec references and release hashes pinned by the manifests built at `cutoff`."""
    manifests: dict[str, tuple[str, dict[str, Any]]] = {}
    for key in store.list("releases/"):
        if key.endswith("/manifest.json"):
            core = json.loads(store.get(key))
            if core["knowledge_cutoff"] == cutoff:
                if core["dataset_id"] in manifests:
                    raise ExerciseError(f"two {core['dataset_id']} releases at cutoff {cutoff}")
                manifests[core["dataset_id"]] = (key.split("/")[2], core)
    if not manifests:
        raise ExerciseError(f"no release manifest at cutoff {cutoff}")
    code_refs = [core["code_ref"] for _, core in manifests.values()]
    if len({canonical_json(c) for c in code_refs}) != 1:
        raise ExerciseError("the manifests at this cutoff pin different code references")
    return {
        "cutoff": cutoff,
        "code_ref": code_refs[0],
        "spec_refs": {ds: core["spec_ref"] for ds, (_, core) in sorted(manifests.items())},
        "releases": {ds: sha for ds, (sha, _) in sorted(manifests.items())},
    }


def compare_rebuild(store: Any, rebuilt: Mapping[str, Release], pins: Mapping[str, Any]) -> dict[str, Any]:
    """Compare rebuilt releases with the stored ones: manifest bytes and every payload file."""
    results = []
    for ds in sorted(set(rebuilt) | set(pins["releases"])):
        entry: dict[str, Any] = {"dataset_id": ds, "stored_content_sha256": pins["releases"].get(ds)}
        release = rebuilt.get(ds)
        if release is None:
            results.append(
                {**entry, "rebuilt_content_sha256": None, "identical": False, "note": "not rebuilt"}
            )
            continue
        entry["rebuilt_content_sha256"] = release.content_sha256
        # The rebuild must reproduce the release the cutoff pins, not just any stored release: a store can
        # hold several releases of one dataset (F-REVIEW-2026-10-29-t0014-1-1).
        if release.content_sha256 != entry["stored_content_sha256"]:
            results.append({**entry, "identical": False, "note": "rebuilt hash differs from the cutoff pin"})
            continue
        manifest_key = f"{release.prefix}/manifest.json"
        if not store.exists(manifest_key):
            results.append({**entry, "identical": False, "note": "no stored manifest with the rebuilt hash"})
            continue
        manifest_same = store.get(manifest_key) == canonical_json(release.core)
        files = {
            name: store.exists(f"{release.prefix}/{name}") and store.get(f"{release.prefix}/{name}") == data
            for name, data in sorted(release.files.items())
        }
        results.append(
            {
                **entry,
                "manifest_identical": manifest_same,
                "files": files,
                "identical": manifest_same and all(files.values()),
            }
        )
    return {"releases": results, "identical": bool(results) and all(r["identical"] for r in results)}


def rebuild_s1b1(
    store: Any,
    *,
    rits: BusinessCalendar,
    nsw: BusinessCalendar,
    rights: Mapping[str, Any],
    gate: Any,
    pins: Mapping[str, Any],
    cutoff_at: datetime,
) -> dict[str, Release]:
    """Rebuild every S1b-1 release at the cutoff with the pinned code reference."""
    cals = Calendars(rits, nsw, sofr_calendar(store, cutoff_at))
    return build_releases(vintage_store(store, cals), gate, rights, cals, cutoff_at, dict(pins["code_ref"]))


def rebuild_and_compare(
    store: Any,
    rebuild: Callable[[Mapping[str, Any]], Mapping[str, Release]],
    cutoff: str,
    running_code_ref: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """`rebuild(pins)` returns the rebuilt releases. `running_code_ref` is the code actually running. A
    rebuild is a success only from the pinned code and lockfile: an absent or different running reference
    is never `ok` (F-REVIEW-2026-10-29-t0014-1-2)."""
    pins = release_pins(store, cutoff)
    rebuilt = rebuild(pins)
    comparison = compare_rebuild(store, rebuilt, pins)
    matches = None if running_code_ref is None else dict(running_code_ref) == dict(pins["code_ref"])
    return {
        "pins": pins,
        "running_code_matches_pin": matches,
        **comparison,
        "ok": comparison["identical"] and matches is True,
    }


# --- state rehearsal -------------------------------------------------------------------------------


def dummy_state(serial: int = 1) -> dict[str, Any]:
    """A state-shaped document that holds nothing real and is marked as dummy."""
    return {
        DUMMY_MARKER: True,
        "version": 4,
        "terraform_version": "dummy",
        "serial": serial,
        "lineage": "00000000-0000-0000-0000-000000000000",
        "outputs": {},
        "resources": [],
    }


def rehearse_state_restore(backup: Path, expected_sha256: str, workdir: Path) -> dict[str, Any]:
    """Restore a DUMMY state backup into an isolated directory. Refused unless: the file is marked as
    dummy state (unknown means deny, since real state can hold secrets); its hash is the expected one; and
    the directory is outside this repository and contains nothing yet (so it holds no infrastructure code).
    Nothing is run or applied: this reads one file and writes one file."""
    raw = Path(backup).read_bytes()
    if sha256_hex(raw) != expected_sha256:
        raise ExerciseError("the backup does not match its recorded hash")
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExerciseError(f"the backup is not JSON: {exc}") from exc
    if not isinstance(state, dict) or state.get(DUMMY_MARKER) is not True:
        raise ExerciseError("only dummy state may be rehearsed here; real state is restored by the owner")
    if not isinstance(state.get("version"), int) or not isinstance(state.get("serial"), int):
        raise ExerciseError("the backup does not have a state shape (version, serial)")
    target = Path(workdir).resolve()
    if target == REPO or REPO in target.parents:
        raise ExerciseError("the isolated directory must be outside this repository")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ExerciseError("the isolated directory must be empty")
    target.mkdir(parents=True, exist_ok=True)
    path = target / STATE_FILE
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(raw)
    restored = sha256_hex(path.read_bytes())
    return {
        "state_file": STATE_FILE,
        "sha256": restored,
        "identical": restored == expected_sha256,
        "serial": state["serial"],
        "resources": len(state.get("resources", [])),
        "infrastructure_applied": False,
        "ok": restored == expected_sha256,
    }


# --- command line --------------------------------------------------------------------------------


def _rebuild_command(args: argparse.Namespace) -> dict[str, Any]:
    store = LocalObjectStore(Path(args.store))
    rights = load_genuine(args.rights_register or SOURCES_REGISTER)
    rits = merge_calendars(
        [load_reference_calendar(p, allow_synthetic=args.allow_synthetic) for p in args.rits_calendar]
    )
    nsw = merge_calendars(
        [load_reference_calendar(p, allow_synthetic=args.allow_synthetic) for p in args.nsw_calendar]
    )
    cutoff_at = parse_instant(args.cutoff)

    def rebuild(pins: Mapping[str, Any]) -> dict[str, Release]:
        return rebuild_s1b1(
            store, rits=rits, nsw=nsw, rights=rights, gate=RightsGate(rights), pins=pins, cutoff_at=cutoff_at
        )

    return rebuild_and_compare(store, rebuild, args.cutoff, current_code_ref())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    rs = sub.add_parser("restore", help="restore a second copy into an empty store")
    rs.add_argument("--second", required=True, help="the second copy (a local directory)")
    rs.add_argument("--inventory", required=True)
    rs.add_argument("--target", required=True, help="the empty store to restore into")
    rb = sub.add_parser("rebuild", help="rebuild the S1b-1 releases from the restored store and compare")
    rb.add_argument("--store", required=True, help="the restored store")
    rb.add_argument(
        "--cutoff", required=True, help="the knowledge cutoff of the releases, as in the manifest"
    )
    rb.add_argument("--rits-calendar", nargs="+", required=True)
    rb.add_argument("--nsw-calendar", nargs="+", required=True)
    rb.add_argument("--rights-register", help="default: registers/sources.yaml")
    rb.add_argument("--allow-synthetic", action="store_true", help="accept synthetic calendars (tests only)")
    st = sub.add_parser("state", help="rehearse restoring DUMMY state into an isolated directory")
    st.add_argument("--backup", required=True)
    st.add_argument("--sha256", required=True, help="the recorded hash of the backup")
    st.add_argument("--into", required=True, help="an empty directory outside the repository")
    mk = sub.add_parser("dummy-state", help="write a dummy state backup and print its hash")
    mk.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "restore":
            report = restore(
                LocalObjectStore(Path(args.second)),
                Path(args.inventory).read_bytes(),
                LocalObjectStore(Path(args.target)),
            )
        elif args.command == "rebuild":
            report = _rebuild_command(args)
        elif args.command == "state":
            report = rehearse_state_restore(Path(args.backup), args.sha256, Path(args.into))
        else:
            raw = canonical_json(dummy_state())
            with open(args.out, "xb") as fh:
                fh.write(raw)
            report = {"sha256": sha256_hex(raw), "ok": True}
    except (ExerciseError, second_copy.InventoryError, OSError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"format": REPORT_FORMAT, "command": args.command, **report}, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
