"""Local results store: byte-exact copies of repository files at named git revisions (OD-0210).

The store is a directory outside the repository:
- `records/<record_id>/<revision[:12]>/<file name>` holds the bytes of `git show <revision>:<path>`;
- `manifest.json` ({"entries": [...]}) is the source of truth, written atomically;
- `catalogue.duckdb` has one table, `records`, rebuilt from the manifest on every change.

`archive` is idempotent: an entry already held with the same bytes is left alone; the same key with
different bytes is refused, never overwritten. `verify` checks files, manifest and catalogue against
each other. `list` prints one line per entry and nothing from the files' contents.

A source is written PATH@REV; the split is at the last "@".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import duckdb

REPO = Path(__file__).resolve().parent.parent
MANIFEST = "manifest.json"
CATALOGUE = "catalogue.duckdb"
RECORDS = "records"
RECORD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
COLUMNS = ("record_id", "path", "revision", "blob", "sha256", "bytes", "stored_as", "archived_at", "note")
CREATE_TABLE = (
    "CREATE TABLE records (record_id VARCHAR, path VARCHAR, revision VARCHAR, blob VARCHAR, "
    "sha256 VARCHAR, bytes BIGINT, stored_as VARCHAR, archived_at VARCHAR, note VARCHAR)"
)


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"git {args[0]} failed: {detail}")
    return result.stdout


def _key(entry: dict) -> tuple[str, str, str]:
    return (entry["record_id"], entry["path"], entry["revision"])


def _read_manifest(store: Path) -> list[dict]:
    path = store / MANIFEST
    if not path.exists():
        return []
    try:
        entries = json.loads(path.read_text())["entries"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"manifest unreadable: {exc}") from exc
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise ValueError("manifest unreadable: entries is not a list of objects")
    return entries


def _write_private(path: Path, data: bytes, *, exclusive: bool) -> None:
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    os.chmod(path, 0o600)


def _write_manifest(store: Path, entries: list[dict]) -> None:
    ordered = sorted(entries, key=_key)
    data = (json.dumps({"entries": ordered}, indent=1, sort_keys=True) + "\n").encode()
    tmp = store / (MANIFEST + ".tmp")
    _write_private(tmp, data, exclusive=False)
    os.replace(tmp, store / MANIFEST)


def _rebuild_catalogue(store: Path, entries: list[dict]) -> None:
    final = store / CATALOGUE
    tmp = store / (CATALOGUE + ".tmp")
    for stale in (tmp, Path(str(tmp) + ".wal")):
        stale.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    try:
        con.execute(CREATE_TABLE)
        for entry in sorted(entries, key=_key):
            con.execute("INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [entry[c] for c in COLUMNS])
    finally:
        con.close()
    os.chmod(tmp, 0o600)
    os.replace(tmp, final)
    Path(str(tmp) + ".wal").unlink(missing_ok=True)


def _mkdir_private(path: Path, stop: Path) -> None:
    """Create `path` and any missing directory down from `stop`, each with mode 0o700."""
    missing = []
    current = path
    while not current.exists() and current != stop.parent:
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        os.chmod(directory, 0o700)


def _check_path(path: str) -> None:
    pure = PurePosixPath(path)
    if not path or pure.is_absolute() or ".." in pure.parts or path.startswith("-"):
        raise ValueError(f"bad repository path {path!r}")


def _resolve_source(repo: Path, source: str) -> tuple[str, str]:
    path, sep, rev = source.rpartition("@")
    if not sep or not path or not rev:
        raise ValueError(f"source {source!r} is not PATH@REV")
    _check_path(path)
    if rev.startswith("-"):
        raise ValueError(f"bad revision {rev!r}")
    try:
        commit = _git(repo, "rev-parse", "--verify", f"{rev}^{{commit}}").decode().strip()
    except ValueError as exc:
        raise ValueError(f"revision {rev!r} does not resolve: {exc}") from exc
    return path, commit


def archive(
    store: Path,
    record_id: str,
    sources: list[str],
    *,
    note: str = "",
    repo: Path = REPO,
    now: datetime | None = None,
) -> list[dict]:
    store = Path(store).expanduser().resolve()
    repo = Path(repo).resolve()
    if store == repo or repo in store.parents:
        raise ValueError("the store must be outside the repository")
    if not RECORD_ID.fullmatch(record_id):
        raise ValueError(f"bad record id {record_id!r}")
    if not sources:
        raise ValueError("no source given")
    stamp = (now or datetime.now(UTC)).astimezone(UTC).isoformat(timespec="seconds")
    existing = {_key(e): e for e in _read_manifest(store)}

    plan = []
    seen = set()
    names = {}
    for source in sources:
        path, revision = _resolve_source(repo, source)
        if (path, revision) in seen:
            raise ValueError(f"source given twice: {path} at {revision[:12]}")
        seen.add((path, revision))
        spec = f"{revision}:{path}"
        try:
            blob = _git(repo, "rev-parse", "--verify", spec).decode().strip()
            kind = _git(repo, "cat-file", "-t", spec).decode().strip()
        except ValueError as exc:
            raise ValueError(f"path {path!r} does not resolve at {revision[:12]}: {exc}") from exc
        if kind != "blob":
            raise ValueError(f"{path!r} at {revision[:12]} is a {kind}, not a file")
        data = _git(repo, "show", spec)
        name = PurePosixPath(path).name
        if names.setdefault((revision, name), path) != path:
            raise ValueError(f"two sources share the file name {name!r} at {revision[:12]}")
        stored_as = f"{RECORDS}/{record_id}/{revision[:12]}/{name}"
        entry = {
            "record_id": record_id,
            "path": path,
            "revision": revision,
            "blob": blob,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "stored_as": stored_as,
            "archived_at": stamp,
            "note": note,
        }
        held = existing.get(_key(entry))
        if held is not None:
            if held["sha256"] != entry["sha256"]:
                raise ValueError(f"{path} at {revision[:12]} is held with different bytes; refusing")
            target = store / held["stored_as"]
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != held["sha256"]:
                raise ValueError(f"stored file for {path} at {revision[:12]} does not match; refusing")
            plan.append((dict(held), data, False))
            continue
        for other in existing.values():
            if other["stored_as"] == stored_as:
                raise ValueError(f"{stored_as} is already held for another path; refusing")
        if (store / stored_as).exists():
            raise ValueError(f"{stored_as} already exists outside the manifest; refusing")
        plan.append((entry, data, True))

    new = [(entry, data) for entry, data, fresh in plan if fresh]
    if new:
        _mkdir_private(store / RECORDS / record_id, store)
        for entry, data in new:
            directory = (store / entry["stored_as"]).parent
            _mkdir_private(directory, store)
            _write_private(store / entry["stored_as"], data, exclusive=True)
        entries = list(existing.values()) + [entry for entry, _ in new]
        _write_manifest(store, entries)
        _rebuild_catalogue(store, entries)
    results = []
    for entry, _, fresh in plan:
        results.append({**entry, "status": "stored" if fresh else "held"})
    return results


def _catalogue_rows(store: Path) -> list[tuple]:
    con = duckdb.connect(str(store / CATALOGUE), read_only=True)
    try:
        return con.execute(f"SELECT {', '.join(COLUMNS)} FROM records").fetchall()
    finally:
        con.close()


def verify(store: Path) -> dict:
    store = Path(store).expanduser().resolve()
    problems: list[str] = []
    try:
        entries = _read_manifest(store)
    except ValueError as exc:
        return {"entries": 0, "files": 0, "problems": [str(exc)]}
    if not (store / MANIFEST).exists():
        problems.append("manifest.json is missing")
    listed = set()
    for entry in entries:
        try:
            stored_as = entry["stored_as"]
            target = (store / stored_as).resolve()
            if store not in target.parents:
                problems.append(f"{stored_as}: outside the store")
                continue
            listed.add(stored_as)
            if not target.is_file():
                problems.append(f"{stored_as}: stored file missing")
                continue
            data = target.read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                problems.append(f"{stored_as}: sha256 differs from the manifest")
            if len(data) != entry["bytes"]:
                problems.append(f"{stored_as}: byte count differs from the manifest")
        except (KeyError, TypeError) as exc:
            problems.append(f"manifest entry malformed: {exc!r}")
    files = 0
    records = store / RECORDS
    if records.is_dir():
        for found in sorted(p for p in records.rglob("*") if not p.is_dir()):
            files += 1
            rel = found.relative_to(store).as_posix()
            if rel not in listed:
                problems.append(f"{rel}: file not listed in the manifest")
    if not (store / CATALOGUE).exists():
        problems.append("catalogue.duckdb is missing")
    else:
        try:
            rows = sorted(_catalogue_rows(store))
            expected = sorted(tuple(e.get(c) for c in COLUMNS) for e in entries)
            if rows != expected:
                problems.append("catalogue rows differ from the manifest entries")
        except duckdb.Error as exc:
            problems.append(f"catalogue unreadable: {exc}")
    return {"entries": len(entries), "files": files, "problems": problems}


def listing(store: Path) -> list[dict]:
    entries = _read_manifest(Path(store).expanduser().resolve())
    return sorted(entries, key=_key)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("archive", "verify", "list"):
        p = sub.add_parser(name)
        p.add_argument("--store", type=Path, required=True)
        if name == "archive":
            p.add_argument("--record-id", required=True)
            p.add_argument("--source", action="append", required=True, metavar="PATH@REV")
            p.add_argument("--note", default="")
            p.add_argument("--repo", type=Path, default=REPO, help="repository to read (default: this one)")
    args = parser.parse_args(argv)
    try:
        if args.command == "archive":
            for entry in archive(args.store, args.record_id, args.source, note=args.note, repo=args.repo):
                print(f"{entry['status']} {entry['record_id']} {entry['path']} {entry['revision'][:12]}")
            return 0
        if args.command == "verify":
            result = verify(args.store)
            print(f"entries {result['entries']}")
            print(f"files {result['files']}")
            for problem in result["problems"]:
                print(f"problem: {problem}", file=sys.stderr)
            return 2 if result["problems"] else 0
        for entry in listing(args.store):
            print(f"{entry['record_id']} {entry['path']} {entry['revision'][:12]} {entry['sha256']}")
        return 0
    except (ValueError, OSError, duckdb.Error) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
