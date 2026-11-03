"""Second copy of an evidence store, with a hash inventory (T-0014 P-3; base-camp criterion 5).

Copies every object of one store into a second store and writes a sealed inventory: one entry per
object (key, sha256, size), the PROVIDER METADATA of the original (blob version id and provider write
time, or the file's mtime for a local store), and the metadata of the copy kept in a separate field.
A copy's timestamps never replace the original's: the original provider write time is what a
HIO-ADR-0012 C5 check needs, and the copy's is only a record that the copy happened. The inventory also
carries a digest of the canonical catalogue rows (not DuckDB file bytes) derived from the source.

Objects are copied byte for byte, so audit references inside them (capture records, attempt records,
status events) are unchanged. Nothing here deletes or overwrites: the store layer cannot, and a
destination object that already exists with different bytes refuses.

    second_copy.py copy   --source DIR --dest DIR --inventory FILE --label NAME
    second_copy.py verify --store DIR --inventory FILE

Both take local directories; the library functions take any store with the object-store methods
(`LocalObjectStore`, `BlobObjectStore`). The destination is the owner's decision (T-0014 checklist 2);
this tool chooses none. Exit status: 0 complete and verified; 1 a check failed; 2 refused input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hio.contracts.canonical import canonical_json, instant_str, sha256_hex
from hio.storage.blobstore import _rank
from hio.storage.catalogue_index import dump, rebuild_index
from hio.storage.objectstore import IntegrityError, LocalObjectStore

FORMAT = "hio-second-copy-inventory/1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class InventoryError(ValueError):
    """The inventory is malformed, altered or not self-consistent."""


class CopyError(Exception):
    """The copy could not be made or did not verify."""


def provider_metadata(store: Any, key: str) -> dict[str, Any]:
    """What the store itself says about one object. For a blob store this is the provider-assigned
    version id and write time; a local file has only its mtime, which is not a provider witness."""
    backend = getattr(store, "backend", None)
    if backend is not None:
        info = backend.stat(key)
        if info is None:
            raise FileNotFoundError(key)
        return {
            "kind": "blob",
            "size": info.size,
            "version_id": info.version_id,
            "written_at": instant_str(info.written_at),
        }
    st = (store.root / key).stat()
    return {
        "kind": "local-file",
        "size": st.st_size,
        "written_at": instant_str(datetime.fromtimestamp(st.st_mtime, UTC)),
    }


def catalogue_rows(store: Any) -> dict[str, list[tuple]]:
    """The canonical catalogue rows (every table, canonical order) derived from the store's records."""
    con = rebuild_index(store)
    try:
        return dump(con)
    finally:
        con.close()


def catalogue_sha256(store: Any) -> str:
    return sha256_hex(canonical_json(catalogue_rows(store)))


def _totals(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_prefix: dict[str, int] = {}
    for e in entries:
        prefix = e["key"].split("/", 1)[0]
        by_prefix[prefix] = by_prefix.get(prefix, 0) + 1
    return {"objects": len(entries), "bytes": sum(e["size"] for e in entries), "by_prefix": by_prefix}


def seal(inventory: Mapping[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in inventory.items() if k != "inventory_sha256"}
    return {**body, "inventory_sha256": sha256_hex(canonical_json(body))}


def take_inventory(store: Any, *, label: str, clock: Callable[[], datetime] | None = None) -> dict[str, Any]:
    """Inventory every object of `store` (read through `get`, so the store's own integrity checks run)."""
    entries = []
    for key in sorted(store.list()):
        data = store.get(key)
        entries.append(
            {
                "key": key,
                "sha256": sha256_hex(data),
                "size": len(data),
                "provider": provider_metadata(store, key),
            }
        )
    return seal(
        {
            "format": FORMAT,
            "label": label,
            "created_at": instant_str((clock or (lambda: datetime.now(UTC)))()),
            "entries": entries,
            "totals": _totals(entries),
            "catalogue_sha256": catalogue_sha256(store),
        }
    )


def load_inventory(raw: bytes) -> dict[str, Any]:
    """Parse and validate a sealed inventory; any alteration (an edited, added or removed entry, or
    bytes that are not the canonical rendering) raises `InventoryError`."""
    try:
        inv = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InventoryError(f"inventory is not JSON: {exc}") from exc
    if not isinstance(inv, dict) or inv.get("format") != FORMAT:
        raise InventoryError("not a second-copy inventory of this format")
    if raw != canonical_json(inv):
        raise InventoryError("inventory bytes are not the canonical rendering")
    if seal(inv)["inventory_sha256"] != inv.get("inventory_sha256"):
        raise InventoryError("inventory hash does not match its content")
    entries = inv.get("entries")
    if not isinstance(entries, list):
        raise InventoryError("entries must be a list")
    keys = [e.get("key") for e in entries]
    if keys != sorted(set(keys)):
        raise InventoryError("entries must be unique and sorted by key")
    for e in entries:
        if not _HEX64.match(str(e.get("sha256"))) or not isinstance(e.get("size"), int):
            raise InventoryError(f"malformed entry: {e.get('key')!r}")
        if not isinstance(e.get("provider"), dict):
            raise InventoryError(f"entry has no original provider metadata: {e['key']}")
    if inv.get("totals") != _totals(entries):
        raise InventoryError("totals do not match the entries")
    if not _HEX64.match(str(inv.get("catalogue_sha256"))):
        raise InventoryError("catalogue_sha256 is missing or malformed")
    return inv


def write_inventory(path: Path, inventory: Mapping[str, Any]) -> None:
    """Write the canonical bytes; an existing inventory file is never replaced."""
    with open(path, "xb") as fh:
        fh.write(canonical_json(inventory))


def check_store(store: Any, inventory: Mapping[str, Any]) -> dict[str, Any]:
    """Compare every object of `store` with the inventory. Reports, and decides nothing else.

    `missing`: listed but absent. `tampered`: present but unreadable, multi-versioned or different bytes.
    `unlisted`: present but not in the inventory (an injected object). `ok` needs all three empty."""
    expected = {e["key"]: e for e in inventory["entries"]}
    missing, tampered = [], []
    for key, e in expected.items():
        try:
            data = store.get(key)
        except FileNotFoundError:
            missing.append(key)
            continue
        except (IntegrityError, OSError, ValueError) as exc:
            tampered.append({"key": key, "reason": f"{type(exc).__name__}: {exc}"})
            continue
        if sha256_hex(data) != e["sha256"] or len(data) != e["size"]:
            tampered.append({"key": key, "reason": "bytes differ from the inventory"})
    unlisted = sorted(k for k in store.list() if k not in expected)
    return {
        "checked": len(expected),
        "missing": sorted(missing),
        "tampered": sorted(tampered, key=lambda t: t["key"]),
        "unlisted": unlisted,
        "ok": not (missing or tampered or unlisted),
    }


def copy_store(
    source: Any,
    dest: Any,
    *,
    label: str,
    clock: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Copy `source` into `dest` and return the sealed inventory. Objects are written in the store's
    commit order (data before manifests before records), so an interrupted copy never has a record that
    points at missing bytes, and rerunning resumes it. The destination is verified before returning."""
    base = take_inventory(source, label=label, clock=clock)
    for e in sorted(base["entries"], key=lambda e: (_rank(e["key"]), e["key"])):
        data = source.get(e["key"])
        if sha256_hex(data) != e["sha256"]:
            raise CopyError(f"source object changed while copying: {e['key']}")
        dest.put_if_absent(e["key"], data)
    entries = [{**e, "copy": provider_metadata(dest, e["key"])} for e in base["entries"]]
    inventory = seal({**{k: v for k, v in base.items() if k != "entries"}, "entries": entries})
    report = check_store(dest, inventory)
    if not report["ok"]:
        raise CopyError(f"the copy does not match the inventory: {json.dumps(report, sort_keys=True)}")
    return inventory


def _open(path: str) -> LocalObjectStore:
    return LocalObjectStore(Path(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    cp = sub.add_parser("copy", help="copy a store into a second store and write the inventory")
    cp.add_argument("--source", required=True)
    cp.add_argument("--dest", required=True)
    cp.add_argument("--inventory", required=True, help="inventory file to create (never replaced)")
    cp.add_argument("--label", required=True, help="a name for the source, e.g. 'primary-2026-11'")
    vf = sub.add_parser("verify", help="check a store against an inventory")
    vf.add_argument("--store", required=True)
    vf.add_argument("--inventory", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "copy":
            if Path(args.inventory).exists():
                print(f"refused: {args.inventory} already exists", file=sys.stderr)
                return 2
            inventory = copy_store(_open(args.source), _open(args.dest), label=args.label)
            write_inventory(Path(args.inventory), inventory)
            print(json.dumps({"inventory_sha256": inventory["inventory_sha256"], **inventory["totals"]}))
            return 0
        report = check_store(_open(args.store), load_inventory(Path(args.inventory).read_bytes()))
    except (InventoryError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except CopyError as exc:
        print(f"failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
