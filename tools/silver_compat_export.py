"""Write or check the silver version 1 files of a silver version 2 release (OD-0233).

`--silver-root`, `--release`, `--selection` (a name or an id) and `--source-symbol` choose one
member instrument of one selection. The release is verified first (`hio.marketdata.silver_reader`);
then the three version 1 files (`closes.csv`, `distributions.csv`, `splits.csv`) are

- written into a new directory with `--out DIR` (directory mode 0700, files 0600; an existing
  directory, or one inside the repository, is refused), or
- compared with the files of the same name in `DIR` with `--compare DIR` (exit 0 only when all
  three are identical).

The command prints each file's sha256 and row count, and `identical` or `differs` under
`--compare`: never a date, a price or an amount from the data. A refusal prints `refused: ...` to
stderr and returns 2.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
import sys
from pathlib import Path

from hio.marketdata.silver_reader import COMPAT_FILES, open_release

REPO = Path(__file__).resolve().parent.parent


def check_out(out: Path) -> Path:
    """The resolved output directory; refuses one inside the repository or one that exists."""
    resolved = Path(out).resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--out must lie outside the repository")
    if os.path.lexists(out):
        raise ValueError("--out already exists")
    return resolved


def _write_new(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
    path.chmod(0o600)


def _rows(data: bytes) -> int:
    """Data rows of a rendered file: its records less the header."""
    return len(list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))) - 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--silver-root", type=Path, required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--source-symbol", required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--compare", type=Path)
    args = parser.parse_args(argv)
    try:
        out = check_out(args.out) if args.out is not None else None  # before anything is read
        release = open_release(args.silver_root, args.release)
        selection_id = release.selection_id(args.selection)
        files = release.compat_files(selection_id, args.source_symbol)
        if out is not None:
            out.mkdir(mode=0o700)
            out.chmod(0o700)
            for name in COMPAT_FILES:
                _write_new(out / name, files[name])
        verdicts = {}
        if args.compare is not None:
            for name in COMPAT_FILES:
                path = args.compare / name
                present = path.is_file() and not path.is_symlink()
                verdicts[name] = present and path.read_bytes() == files[name]
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print(f"release_id: {release.release_id}")
    print(f"selection_id: {selection_id}")
    for name in COMPAT_FILES:
        data = files[name]
        print(f"{name}: sha256 {hashlib.sha256(data).hexdigest()} rows {_rows(data)}")
    if args.compare is not None:
        for name in COMPAT_FILES:
            print(f"{name}: {'identical' if verdicts[name] else 'differs'}")
        return 0 if all(verdicts.values()) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
