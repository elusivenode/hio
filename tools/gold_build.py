"""Gold marts: plan, build and verify a panel, a portfolio path, a covariance or a risk contribution
(OD-0233, OD-0234).

    gold_build.py plan|run|verify --target PATH --lock PATH --factor-store PATH --gold-root PATH

`plan` shows what exists, `run` builds what is missing (and nothing else), `verify` refuses unless every mart
exists and verifies. Contract: docs/decisions/gold-marts-contract.md §7 and §6a; the logic is `hio.jobs.gold`.

The two float kinds record the NumPy and Python versions in their recipe (§6a): `{"numpy": numpy.__version__,
"python": "<major>.<minor>"}`, so another version is another build id.

The code commit is the repository's `HEAD`, and only when `git status --porcelain` is empty: a build is never
labelled with a commit that does not describe its code. `--gold-root` may not lie inside the repository.

The output is one line per node, `<kind> <name> <status> <build_id or ->`, then `pass`. A refusal prints
`refused: ...` to stderr and returns 2. **It never prints a date, a return or a weight from the data**: a
refusal message has every digit masked (`#`) before it is printed, except inside a build id or a sha256.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy  # noqa: E402
from hio.models.risk import build_covariance, build_risk_contribution  # noqa: E402

from hio.jobs import gold  # noqa: E402
from hio.models.panels import build_panel  # noqa: E402
from hio.portfolio.paths import build_portfolio_path  # noqa: E402

# `hio.jobs` may not import the calculations (tools/check_repo.py), so this tool passes them in.
BUILDERS = {
    "panel": build_panel,
    "portfolio_path": build_portfolio_path,
    "covariance": build_covariance,
    "risk_contribution": build_risk_contribution,
}
COMMANDS = {"plan": gold.plan, "run": gold.run, "verify": gold.verify}

# A build id or a sha256 (16 or 64 lower-case hex, with at least one letter) is kept whole; every other
# digit is masked, because a refusal from the calculation may quote a date, a return or a weight.
_KEEP_OR_DIGIT = re.compile(
    r"(?<![0-9A-Za-z])(?=[0-9]*[a-f])(?:[0-9a-f]{64}|[0-9a-f]{16})(?![0-9A-Za-z])|[0-9]"
)


def _scrub(message: str) -> str:
    """The message with every digit masked as `#`, except inside a build id or a sha256."""
    return _KEEP_OR_DIGIT.sub(lambda m: "#" if len(m.group(0)) == 1 else m.group(0), message)


def _git(*args: str) -> str:
    done = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise ValueError(f"git {args[0]} failed")
    return done.stdout


def _commit() -> str:
    """The repository's HEAD, refused unless the working tree is clean."""
    if _git("status", "--porcelain").strip():
        raise ValueError("the working tree is not clean: commit or stash before building")
    head = _git("rev-parse", "HEAD").strip()
    if not head:
        raise ValueError("git rev-parse HEAD returned nothing")
    return head


def _environment() -> dict[str, str]:
    """What the two float kinds record in their recipe (§6a): another library version is another build."""
    return {"numpy": numpy.__version__, "python": f"{sys.version_info.major}.{sys.version_info.minor}"}


def _outside_repo(gold_root: Path) -> Path:
    resolved = Path(gold_root).expanduser().resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--gold-root must lie outside the repository")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=sorted(COMMANDS))
    for flag in ("target", "lock", "factor-store", "gold-root"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        gold_root = _outside_repo(args.gold_root)
        commit = _commit()
        result = COMMANDS[args.command](
            args.target,
            args.lock,
            args.factor_store,
            gold_root,
            commit=commit,
            builders=BUILDERS,
            environment=_environment(),
        )
    except (ValueError, OSError) as exc:
        print(f"refused: {_scrub(str(exc))}", file=sys.stderr)
        return 2
    for node in result.nodes:
        print(f"{node.kind} {node.name} {node.status} {node.build_id or '-'}")
    print("pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
