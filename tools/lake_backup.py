"""Backup and restore for the local data lake (OD-0231; docs/decisions/local-data-layers-proposal.md).

    lake_backup.py backup  --source DIR --target DIR [--exclude NAME ...]
    lake_backup.py verify  --backup DIR
    lake_backup.py restore --backup DIR --into DIR
    lake_backup.py compare --source DIR --backup DIR [--exclude NAME ...]

A backup is the directory `<target>/<backup_id>/` holding `inventory.json` and `data/` (a copy of the
source). The inventory lists every file as `{path (POSIX, relative), bytes, sha256}`, sorted by path.
`backup_id` is `<UTC time, YYYYMMDDTHHMMSSZ>-<first 12 hex of the sha256 of the canonical inventory>`,
where the canonical inventory is `json.dumps(files, sort_keys=True, separators=(",", ":"))` over that
list. Two backups of the same tree share the hash part whatever the time.

A backup is built in `<backup_id>.partial` and renamed only after every copied file has been re-read
and matched. A failure leaves the `.partial` directory in place and is a refusal; an existing backup
is never written into. Files are mode 0o600 and directories 0o700. **Empty directories are not
preserved** (the inventory lists files only), and neither are modes, owners or times.

The source must not contain a symlink or a special file, and neither source nor target may lie inside
the repository (the target also not inside the source). `restore` goes only into a directory that does
not exist or is empty, and verifies the restored tree against the inventory.

The tool prints ids, counts and pass or fail, never a file's contents or name.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA = "hio.backup/1"
INVENTORY = "inventory.json"
DATA = "data"
CHUNK = 1024 * 1024
_HEX64 = re.compile(r"[0-9a-f]{64}")
_ID = re.compile(r"(\d{8}T\d{6}Z)-([0-9a-f]{12})")
_KEYS = {"schema", "backup_id", "source", "created_at", "files", "total_bytes"}


def _inside(path: Path, other: Path) -> bool:
    return path == other or other in path.parents


def _refuse_repository(path: Path, option: str) -> Path:
    resolved = path.resolve()
    if _inside(resolved, REPO):
        raise ValueError(f"{option} must lie outside the repository")
    return resolved


def _check_excludes(exclude) -> frozenset[str]:
    names = frozenset(exclude)
    for name in names:
        if not name or "/" in name or "\\" in name or name in {".", ".."}:
            raise ValueError("--exclude takes one path component")
    return names


def _check_source(source: Path) -> Path:
    path = Path(os.path.abspath(source))
    if path.is_symlink():
        raise ValueError("--source is a symlink")
    resolved = _refuse_repository(path, "--source")
    if not resolved.is_dir():
        raise ValueError("--source is not a directory")
    return resolved


def _scan(root: Path, excludes: frozenset[str] = frozenset()):
    """Return (files, odd): the POSIX relative paths of regular files, and of symlinks and special files.
    Directories are walked, never followed through a link. A name that is not valid UTF-8 is refused."""
    files: list[str] = []
    odd: list[str] = []

    def visit(directory: Path, prefix: str) -> None:
        with os.scandir(directory) as entries:
            ordered = sorted(entries, key=lambda e: e.name)
        for entry in ordered:
            if entry.name in excludes:
                continue
            try:
                entry.name.encode("utf-8")
            except UnicodeEncodeError:
                raise ValueError("a file name is not valid UTF-8") from None
            relative = prefix + entry.name
            mode = entry.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                odd.append(relative)
            elif stat.S_ISDIR(mode):
                visit(Path(entry.path), relative + "/")
            elif stat.S_ISREG(mode):
                files.append(relative)
            else:
                odd.append(relative)

    visit(root, "")
    return sorted(files), sorted(odd)


def _hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        while chunk := handle.read(CHUNK):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def _inventory(source: Path, excludes: frozenset[str]) -> list[dict]:
    files, odd = _scan(source, excludes)
    if odd:
        raise ValueError(f"--source holds {len(odd)} symlink(s) or special file(s)")
    records = []
    for relative in files:
        size, sha = _hash_file(source / relative)
        records.append({"path": relative, "bytes": size, "sha256": sha})
    return records


def _inventory_hash(files: list[dict]) -> str:
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _stamp(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("now must carry a time zone")
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _mkdir(path: Path) -> None:
    if not path.is_dir():
        os.mkdir(path, 0o700)
        os.chmod(path, 0o700)


def _copy_file(src: Path, dst: Path, base: Path) -> tuple[int, str]:
    """Copy `src` to a new `dst` (0o600, directories 0o700 below `base`); return its size and sha256."""
    for parent in reversed([p for p in dst.parents if _inside(p, base) and p != base]):
        _mkdir(parent)
    digest = hashlib.sha256()
    size = 0
    descriptor = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as out, open(src, "rb") as handle:
        os.fchmod(out.fileno(), 0o600)
        while chunk := handle.read(CHUNK):
            size += len(chunk)
            digest.update(chunk)
            out.write(chunk)
    return size, digest.hexdigest()


def _write_new(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as out:
        os.fchmod(out.fileno(), 0o600)
        out.write(data)


def _safe_path(text: object) -> bool:
    if not isinstance(text, str) or not text or text.startswith("/") or "\\" in text:
        return False
    return all(part not in {"", ".", ".."} for part in text.split("/"))


def _check_tree(root: Path, files: list[dict]) -> list[tuple[str, str]]:
    """Problems of the tree at `root` against the inventory: missing, changed, extra."""
    problems: list[tuple[str, str]] = []
    if root.is_symlink() or not root.is_dir():
        return [("missing", record["path"]) for record in files] + [("not_a_directory", DATA)]
    found, odd = _scan(root)
    present = set(found)
    expected = {record["path"] for record in files}
    for record in files:
        if record["path"] not in present:
            problems.append(("missing", record["path"]))
            continue
        size, sha = _hash_file(root / record["path"])
        if size != record["bytes"] or sha != record["sha256"]:
            problems.append(("changed", record["path"]))
    problems += [("extra", path) for path in sorted((present - expected) | set(odd))]
    return problems


def _read_inventory(directory: Path) -> tuple[dict | None, list[tuple[str, str]]]:
    """Load and validate `inventory.json` of a backup directory. Returns (inventory or None, problems)."""
    problems: list[tuple[str, str]] = []
    if directory.is_symlink() or not directory.is_dir():
        return None, [("not_a_backup", "")]
    names = {entry.name for entry in os.scandir(directory)}
    problems += [("unexpected_entry", name) for name in sorted(names - {INVENTORY, DATA})]
    path = directory / INVENTORY
    if path.is_symlink() or not path.is_file():
        return None, [*problems, ("inventory", "missing")]
    try:
        inventory = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None, [*problems, ("inventory", "unparseable")]
    if not isinstance(inventory, dict) or set(inventory) != _KEYS or inventory["schema"] != SCHEMA:
        return None, [*problems, ("inventory", "schema")]
    files = inventory["files"]
    valid = isinstance(files, list)
    previous = None
    total = 0
    for record in files if valid else []:
        if not (
            isinstance(record, dict)
            and set(record) == {"path", "bytes", "sha256"}
            and _safe_path(record["path"])
            and isinstance(record["bytes"], int)
            and not isinstance(record["bytes"], bool)
            and record["bytes"] >= 0
            and isinstance(record["sha256"], str)
            and _HEX64.fullmatch(record["sha256"])
            and (previous is None or record["path"] > previous)
        ):
            valid = False
            break
        previous = record["path"]
        total += record["bytes"]
    if not valid:
        return None, [*problems, ("inventory", "files")]
    if inventory["total_bytes"] != total:
        problems.append(("inventory", "total_bytes"))
    match = _ID.fullmatch(str(inventory["backup_id"]))
    created = inventory["created_at"]
    try:
        stamp = _stamp(datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC))
    except (TypeError, ValueError):
        stamp = None
    if match is None or match.group(2) != _inventory_hash(files)[:12] or match.group(1) != stamp:
        problems.append(("backup_id", "inventory"))
    if inventory["backup_id"] != directory.name:
        problems.append(("backup_id", "directory"))
    return inventory, problems


def _verify(backup_dir: Path) -> tuple[dict | None, list[tuple[str, str]]]:
    directory = Path(os.path.abspath(backup_dir))
    inventory, problems = _read_inventory(directory)
    if inventory is not None:
        problems += _check_tree(directory / DATA, inventory["files"])
    return inventory, problems


def _report(inventory: dict | None, problems: list[tuple[str, str]], **extra) -> dict:
    files = inventory["files"] if inventory else []
    report = {
        "backup_id": inventory["backup_id"] if inventory else None,
        "files": len(files),
        "bytes": sum(record["bytes"] for record in files),
        "problems": problems,
        "passed": not problems,
    }
    return report | extra


def verify(backup_dir: Path) -> dict:
    """Check a backup: every inventory file present with the right bytes and sha256, no extra file under
    `data/`, and a `backup_id` consistent with the directory name and the inventory."""
    inventory, problems = _verify(backup_dir)
    return _report(inventory, problems)


def backup(source: Path, target: Path, *, now: datetime, exclude=()) -> dict:
    """Copy `source` into `<target>/<backup_id>/`, verified, via `<backup_id>.partial`. Refuses with
    ValueError. A failure after the copy began leaves the `.partial` directory behind (and says so)."""
    excludes = _check_excludes(exclude)
    src = _check_source(source)
    tgt = _refuse_repository(Path(os.path.abspath(target)), "--target")
    if _inside(tgt, src):
        raise ValueError("--target must lie outside --source")
    stamp = _stamp(now)
    files = _inventory(src, excludes)
    backup_id = f"{stamp}-{_inventory_hash(files)[:12]}"
    final = tgt / backup_id
    partial = tgt / f"{backup_id}.partial"
    if tgt.exists() and (tgt.is_symlink() or not tgt.is_dir()):
        raise ValueError("--target is not a directory")
    if os.path.lexists(final):
        inventory, problems = _verify(final)
        if problems:
            raise ValueError("a different backup exists under this backup_id")
        return _report(inventory, [], existed=True)
    if os.path.lexists(partial):
        raise ValueError("a partial backup exists under this backup_id: remove it first")
    inventory = {
        "schema": SCHEMA,
        "backup_id": backup_id,
        "source": src.name,
        "created_at": now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": files,
        "total_bytes": sum(record["bytes"] for record in files),
    }
    if not tgt.exists():
        if not tgt.parent.is_dir():
            raise ValueError("--target's parent directory does not exist")
        _mkdir(tgt)
    try:
        os.mkdir(partial, 0o700)
        os.chmod(partial, 0o700)
        data = partial / DATA
        _mkdir(data)
        for record in files:
            size, sha = _copy_file(src / record["path"], data / record["path"], data)
            if (size, sha) != (record["bytes"], record["sha256"]):
                raise ValueError("a source file changed while it was copied")
        _write_new(
            partial / INVENTORY, (json.dumps(inventory, indent=1, sort_keys=True) + "\n").encode("utf-8")
        )
        problems = _check_tree(data, files)
        if problems:
            raise ValueError(f"the copy does not match the inventory ({len(problems)} problem(s))")
        os.rename(partial, final)
    except (OSError, ValueError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        raise ValueError(f"backup failed, partial directory left in place: {detail}") from exc
    return _report(inventory, [], existed=False)


def restore(backup_dir: Path, into: Path) -> dict:
    """Verify `backup_dir`, then copy its `data/` into `into` (absent, or an empty directory; its parent must
    exist) and verify the restored tree. A failure part-way leaves what was written: it is not cleaned up."""
    target = _refuse_repository(Path(os.path.abspath(into)), "--into")
    directory = Path(os.path.abspath(backup_dir))
    if _inside(target, directory):
        raise ValueError("--into must lie outside the backup")
    inventory, problems = _verify(directory)
    if problems:
        raise ValueError(f"the backup does not verify ({len(problems)} problem(s))")
    if os.path.lexists(target):
        if target.is_symlink() or not target.is_dir():
            raise ValueError("--into exists and is not a directory")
        if any(target.iterdir()):
            raise ValueError("--into is not empty")
    else:
        if not target.parent.is_dir():
            raise ValueError("--into's parent directory does not exist")
        _mkdir(target)
    files = inventory["files"]
    try:
        for record in files:
            size, sha = _copy_file(directory / DATA / record["path"], target / record["path"], target)
            if (size, sha) != (record["bytes"], record["sha256"]):
                raise ValueError("a backup file changed while it was restored")
    except OSError as exc:
        raise ValueError(f"restore failed: {type(exc).__name__}") from exc
    problems = _check_tree(target, files)
    if problems:
        raise ValueError(f"the restored tree does not match the inventory ({len(problems)} problem(s))")
    return _report(inventory, [])


def compare(source: Path, backup_dir: Path, *, exclude=()) -> dict:
    """Count files identical, changed, only in the source and only in the backup, against the backup's
    inventory (the backup's own bytes are `verify`'s business). `exclude` should match the backup's."""
    excludes = _check_excludes(exclude)
    src = _check_source(source)
    inventory, problems = _read_inventory(Path(os.path.abspath(backup_dir)))
    if inventory is None or problems:
        raise ValueError(f"the backup inventory is not valid ({len(problems)} problem(s))")
    mine = {record["path"]: record for record in _inventory(src, excludes)}
    theirs = {record["path"]: record for record in inventory["files"]}
    both = mine.keys() & theirs.keys()
    identical = sum(1 for path in both if mine[path] == theirs[path])
    report = {
        "backup_id": inventory["backup_id"],
        "identical": identical,
        "changed": len(both) - identical,
        "only_in_source": len(mine.keys() - theirs.keys()),
        "only_in_backup": len(theirs.keys() - mine.keys()),
    }
    report["passed"] = not (report["changed"] or report["only_in_source"] or report["only_in_backup"])
    return report


def _print_counts(report: dict) -> None:
    print(f"backup_id: {report['backup_id']}")
    print(f"files: {report['files']}")
    print(f"bytes: {report['bytes']}")
    kinds: dict[str, int] = {}
    for kind, _ in report["problems"]:
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f"problems: {len(report['problems'])}")
    for kind in sorted(kinds):
        print(f"  {kind}: {kinds[kind]}")


def main(argv: list[str] | None = None, *, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("backup")
    one.add_argument("--source", type=Path, required=True)
    one.add_argument("--target", type=Path, required=True)
    one.add_argument("--exclude", action="append", default=[])
    two = commands.add_parser("verify")
    two.add_argument("--backup", type=Path, required=True)
    three = commands.add_parser("restore")
    three.add_argument("--backup", type=Path, required=True)
    three.add_argument("--into", type=Path, required=True)
    four = commands.add_parser("compare")
    four.add_argument("--source", type=Path, required=True)
    four.add_argument("--backup", type=Path, required=True)
    four.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            when = now or datetime.now(UTC)
            report = backup(args.source, args.target, now=when, exclude=args.exclude)
            _print_counts(report)
            if report["existed"]:
                print("already built")
        elif args.command == "verify":
            report = verify(args.backup)
            _print_counts(report)
        elif args.command == "restore":
            report = restore(args.backup, args.into)
            _print_counts(report)
        else:
            report = compare(args.source, args.backup, exclude=args.exclude)
            print(f"backup_id: {report['backup_id']}")
            for name in ("identical", "changed", "only_in_source", "only_in_backup"):
                print(f"{name}: {report[name]}")
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print("pass" if report["passed"] else "fail")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
