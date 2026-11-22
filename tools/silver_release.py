"""Build and verify a silver version 2 release (OD-0233).

`build` reads a release spec, the instrument register, the observation specs and the pinned bronze
snapshots, and writes `<silver-root>/v2/<release_id>/` (contract: `docs/decisions/silver-v2-contract.md`,
proposed). The tree must be clean: the code commit is `git rev-parse HEAD` of this repository, looked up
here and nowhere else. The silver root must lie outside the repository. `verify` re-checks a release.

The command prints counts, ids, hashes and pass or fail only: never a date, a price, an amount or a name
from the data. A refusal prints `refused: ...` to stderr and returns 2.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from hio.contracts import silver
from hio.marketdata.silver_build import build_release, check_output_path

REPO = Path(__file__).resolve().parent.parent
_RELEASE_ID = re.compile(r"[0-9a-f]{64}")


def code_commit() -> str:
    """The repository's HEAD commit; refused unless the working tree is clean."""
    git = ("git", "-C", str(REPO))
    status = subprocess.run((*git, "status", "--porcelain"), capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise ValueError("the working tree has uncommitted changes")
    head = subprocess.run((*git, "rev-parse", "HEAD"), capture_output=True, text=True, check=True)
    return head.stdout.strip()


def _build(args: argparse.Namespace) -> int:
    check_output_path(args.silver_root)  # before any git lookup
    release_dir, core, existed = build_release(
        args.spec,
        args.register,
        args.observations,
        args.bronze_root,
        args.silver_root,
        commit=code_commit(),
    )
    print(f"release_id: {release_dir.name}")
    for table in core["tables"]:
        print(f"{table['name']}: {table['rows']}")
    for entry in core["selections"]:
        rows = silver.parse_selection(
            (release_dir / "selections" / f"{entry['selection_id']}.csv").read_bytes()
        )
        excluded = sum(1 for row in rows if row["disposition"] == "excluded")
        print(
            f"selection {entry['name']}: {entry['selection_id']} ({entry['rows']} rows, {excluded} excluded)"
        )
    if existed:
        print("already built")
    return 0


def _verify(args: argparse.Namespace) -> int:
    if not _RELEASE_ID.fullmatch(args.release):
        raise ValueError("--release must be a release_id: 64 lower-case hex characters")
    silver.verify_release(Path(args.silver_root) / "v2" / args.release)
    print("pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build a release")
    build.add_argument("--spec", type=Path, required=True)
    build.add_argument("--register", type=Path, required=True)
    build.add_argument("--observations", type=Path, required=True)
    build.add_argument("--bronze-root", type=Path, required=True)
    build.add_argument("--silver-root", type=Path, required=True)
    verify = commands.add_parser("verify", help="verify a release")
    verify.add_argument("--silver-root", type=Path, required=True)
    verify.add_argument("--release", required=True)
    args = parser.parse_args(argv)
    try:
        return _build(args) if args.command == "build" else _verify(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else ""
        print(f"refused: {type(exc).__name__}: {detail}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
