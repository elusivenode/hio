"""HIO repository checks (operating model §8 CI list; OD-0019 and OD-0020 public-repository safeguards).

Usage:
    python tools/check_repo.py [check ...]          # default: all static checks
    python tools/check_repo.py trailers <base> <head>

Static checks:
    links         relative Markdown links resolve inside the repository
    frontmatter   per-record-type front-matter schema (verbatim history files are exempt)
    yaml          factor specs and registers parse and satisfy their schemas
    status        STATUS.md is within its line limit
    public        no secrets, no downloaded data, no local databases, no non-releasable artefacts
    imports       architecture §1 import rules, plus no network client and no macsmsf import in src/
    valid_time    OBS-INV-005 lint: no UTC-instant-to-date conversion in src/

Exit status 1 on any failure. Reads tracked and staged files only (git ls-files).
"""

from __future__ import annotations

import ast
import posixpath
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STATUS_MAX_LINES = 150
MAX_FILE_BYTES = 512 * 1024

errors: list[str] = []


def fail(check: str, msg: str) -> None:
    errors.append(f"[{check}] {msg}")


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(p for p in out.splitlines() if p and (ROOT / p).is_file())


def front_matter(text: str) -> dict | None:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {"__invalid__": True}
    return data if isinstance(data, dict) else {"__invalid__": True}


# --- links -------------------------------------------------------------------------------------


def check_links(files: list[str]) -> None:
    present = set(files)
    dirs = set()
    for f in files:
        d = posixpath.dirname(f)
        while d:
            dirs.add(d)
            d = posixpath.dirname(d)
    for f in (x for x in files if x.endswith(".md")):
        text = re.sub(r"```.*?```", "", (ROOT / f).read_text(), flags=re.S)
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            path = target.split("#")[0]
            if not path:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(f), path))
            if resolved not in present and resolved not in dirs:
                fail("links", f"{f}: unresolved link -> {target}")


# --- front matter -------------------------------------------------------------------------------

# Required keys per record type, matching each type's template. Verbatim owner messages and
# superseded inputs in docs/history/ carry no front matter by design and are exempt.
FM_RULES: list[tuple[str, tuple[str, ...]]] = [
    (r"^docs/history/(?!README\.md$)", ()),  # exempt
    (r"^CLAUDE\.md$", ()),  # an @import shim
    (r"^\.github/", ()),  # GitHub configuration, not records
    (r"^\.claude/skills/.+/SKILL\.md$", ("name", "description")),
    (r"^docs/decisions/owner/OD-\d{4}-.+\.md$", ("id", "title", "decision", "record_status")),
    (r"^handoffs/.+\.md$", ("id", "date")),  # the first handoff predates the template
    (r"^reviews/handoffs/.+\.md$", ("id",)),
    (r"^reviews/(records|responses|reports)/(?!README\.md$).+\.md$", ("id",)),
    (r"^registers/tasks/T-\d{4}-.+\.md$", ("id", "title", "status")),
    (r"^templates/", ()),  # templates hold placeholders
    (r".*\.md$", ("id", "status", "owner")),  # canonical documents
]


def check_frontmatter(files: list[str]) -> None:
    for f in (x for x in files if x.endswith(".md")):
        if f.startswith("tests/"):
            continue
        required = next(req for pat, req in FM_RULES if re.search(pat, f))
        if not required:
            continue
        fm = front_matter((ROOT / f).read_text())
        if fm is None:
            fail("frontmatter", f"{f}: no front matter")
            continue
        if fm.get("__invalid__"):
            fail("frontmatter", f"{f}: front matter is not a YAML mapping")
            continue
        missing = [k for k in required if k not in fm]
        if missing:
            fail("frontmatter", f"{f}: missing {', '.join(missing)}")


# --- YAML schemas ----------------------------------------------------------------------------------

SPEC_SECTIONS = (
    "identity",
    "economics",
    "classification",
    "return_convention",
    "observations",
    "availability",
    "construction",
    "invariants",
    "triangulation",
    "limitations",
    "rights_required",
    "changelog",
)
SERIES_CLASSES = {
    "total_return",
    "excess_return",
    "strategy_return",
    "price_only",
    "state_indicator",
    "reference_academic",
}
PERMISSION_VALUE = re.compile(r"^(allow|deny|unknown|conditional\(.+\))$")
VERIFICATIONS = {"unverified", "vendor_asserted", "owner_verified", "contract"}


def check_yaml(files: list[str]) -> None:
    for f in (x for x in files if x.startswith("specs/factors/") and x.endswith(".yaml")):
        if f.endswith("_template.yaml"):
            continue
        spec = yaml.safe_load((ROOT / f).read_text())
        missing = [s for s in SPEC_SECTIONS if s not in spec]
        if missing:
            fail("yaml", f"{f}: missing sections {missing}")
            continue
        ident = spec["identity"]
        if Path(f).stem != ident.get("factor_id"):
            fail("yaml", f"{f}: factor_id {ident.get('factor_id')!r} does not match the file name")
        if not re.match(r"^\d+\.\d+\.\d+$", str(ident.get("version", ""))):
            fail("yaml", f"{f}: version is not semver")
        if spec["classification"].get("series_class") not in SERIES_CLASSES:
            fail("yaml", f"{f}: unknown series_class")

    sources = yaml.safe_load((ROOT / "registers/sources.yaml").read_text())
    seen: set[str] = set()
    for src in sources.get("sources", []):
        sid = src.get("id")
        if not sid or sid in seen:
            fail("yaml", f"registers/sources.yaml: missing or duplicate id {sid!r}")
        seen.add(sid)
        if sid and sid.startswith("synthetic"):
            fail("yaml", f"registers/sources.yaml: synthetic source {sid!r} in the genuine register")
        ver = src.get("verification")
        if ver not in VERIFICATIONS:
            fail("yaml", f"registers/sources.yaml: {sid}: verification {ver!r} not allowed")
        recorded = re.match(r"^OD-\d{4}$", str(src.get("verified_by", "")))
        if ver in {"owner_verified", "contract"} and not recorded:
            fail("yaml", f"registers/sources.yaml: {sid}: {ver} needs verified_by: OD-NNNN (owner action)")
        for key, value in _flatten(src.get("rights") or {}):
            if key.endswith("attribution_required"):
                continue
            if not PERMISSION_VALUE.match(str(value)):
                fail("yaml", f"registers/sources.yaml: {sid}: rights.{key} = {value!r}")

    for reg in ("registers/hypotheses.yaml", "registers/experiments.yaml"):
        data = yaml.safe_load((ROOT / reg).read_text()) or []
        if not isinstance(data, list):
            fail("yaml", f"{reg}: must be a list")
            continue
        ids = [d.get("id") for d in data]
        if len(ids) != len(set(ids)) or any(not i for i in ids):
            fail("yaml", f"{reg}: missing or duplicate ids")


def _flatten(d: dict, prefix: str = ""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _flatten(v, f"{prefix}{k}.")
        else:
            yield f"{prefix}{k}", v


# --- STATUS length ------------------------------------------------------------------------------------


def check_status(files: list[str]) -> None:  # noqa: ARG001 (uniform signature)
    n = len((ROOT / "STATUS.md").read_text().splitlines())
    if n > STATUS_MAX_LINES:
        fail("status", f"STATUS.md has {n} lines (limit {STATUS_MAX_LINES})")


# --- public-repository safeguards (OD-0019, OD-0020 item 4) ----------------------------------------------

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    (r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}", "GitHub token"),
    (r"sk-[A-Za-z0-9_-]{20,}", "API secret key"),
    (r"xox[abprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"tid_[A-Za-z0-9]{20,}|tsec_[A-Za-z0-9]{10,}", "Tigris key"),
    (r"FlyV1 [A-Za-z0-9+/=]{20,}", "Fly token"),
    (r"npg_[A-Za-z0-9]{8,}", "Neon password"),
    (r"[a-z]+://[^\s:/@'\"]+:[^\s@'\"]{6,}@(?!localhost)[^\s'\"]+", "URL with embedded credentials"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9/+_-]{16,}['\"]", "assigned secret"),
]
# Downloaded data, local databases and build outputs never enter git. Synthetic fixtures live
# only under tests/fixtures/synthetic/ and declare themselves on line 1.
FORBIDDEN_PATHS = [
    (r"(^|/)\.env($|\.(?!example$)[^/]*$)", "environment file"),
    (r"\.(pem|key|p12|pfx|jks)$", "key material"),
    (r"\.(duckdb|db|sqlite3?|wal)$", "local database"),
    (r"\.(parquet|feather|arrow|h5|hdf5|pkl|pickle|npz?)$", "binary data or artefact"),
    (r"\.(xlsx?|zip|gz|tgz|bz2|7z)$", "archive or spreadsheet"),
    (r"^(data|receipts|releases|artefacts|catalogue|\.hio-store)/", "object-store or data directory"),
]
DATA_SUFFIXES = (".csv", ".json", ".jsonl", ".xml", ".txt", ".tsv")
SYNTHETIC_DIR = "tests/fixtures/synthetic/"
SYNTHETIC_MARKER = "SYNTHETIC"
SELF = "tools/check_repo.py"


def check_public(files: list[str]) -> None:
    for f in files:
        for pat, what in FORBIDDEN_PATHS:
            if re.search(pat, f):
                fail("public", f"{f}: {what} must not be committed")
        size = (ROOT / f).stat().st_size
        if size > MAX_FILE_BYTES:
            fail("public", f"{f}: {size} bytes exceeds {MAX_FILE_BYTES}")
        if f.endswith(DATA_SUFFIXES) and not f.startswith(".github/"):
            if not f.startswith(SYNTHETIC_DIR):
                fail("public", f"{f}: data files belong under {SYNTHETIC_DIR} and must be synthetic")
            elif SYNTHETIC_MARKER not in (ROOT / f).read_text(errors="replace").splitlines()[0]:
                fail("public", f"{f}: line 1 must declare {SYNTHETIC_MARKER}")
        if f == SELF:
            continue
        try:
            text = (ROOT / f).read_text()
        except UnicodeDecodeError:
            fail("public", f"{f}: binary file")
            continue
        for pat, what in SECRET_PATTERNS:
            if re.search(pat, text):
                fail("public", f"{f}: possible {what}")


# --- import rules (architecture §1) -----------------------------------------------------------------------

# package -> hio packages it may import (itself always allowed)
ALLOWED_IMPORTS = {
    "contracts": set(),
    "reference": {"contracts"},
    "storage": {"contracts"},
    "rights": {"contracts"},
    "marketdata": {"contracts", "reference", "storage", "rights"},
    "sources": {"contracts", "reference", "storage", "rights", "marketdata"},  # S1b-1 adapters, T-0009
    "library": {"contracts", "reference"},  # pure compute: no storage, no writes
    "publish": {"contracts", "storage", "rights"},  # the only writer of releases and artefacts
    "models": {"contracts"},
    "portfolio": {"contracts"},
    "taa": {"contracts"},
    "implementation": {"contracts"},
    "jobs": {"contracts", "reference", "storage", "rights", "marketdata", "library", "publish", "sources"},
}
# Network clients are forbidden in src/: S1a has no source-data network access (OD-0017).
FORBIDDEN_MODULES = {
    "socket",
    "ssl",
    "http",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "ftplib",
    "smtplib",
    "macsmsf",
}


def check_imports(files: list[str]) -> None:
    for f in (x for x in files if x.startswith("src/hio/") and x.endswith(".py")):
        parts = f.split("/")
        pkg = parts[2] if len(parts) > 3 else None
        tree = ast.parse((ROOT / f).read_text(), filename=f)
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            elif isinstance(node, ast.ImportFrom) and node.level > 0:
                fail("imports", f"{f}:{node.lineno}: use absolute imports")
            for name in names:
                top = name.split(".")[0]
                if top in FORBIDDEN_MODULES:
                    fail("imports", f"{f}:{node.lineno}: forbidden import {name}")
                if top == "hio" and pkg is not None:
                    target = name.split(".")[1] if "." in name else None
                    if target and target != pkg and target not in ALLOWED_IMPORTS.get(pkg, set()):
                        fail("imports", f"{f}:{node.lineno}: hio.{pkg} may not import hio.{target}")
        if pkg is not None and pkg not in ALLOWED_IMPORTS:
            fail("imports", f"{f}: package hio.{pkg} has no declared import rule")


# --- OBS-INV-005 lint ----------------------------------------------------------------------------------


def check_valid_time(files: list[str]) -> None:
    """valid_time is never derived from a UTC instant: no `.date()` on a datetime, no
    `date.fromtimestamp`/`utcfromtimestamp` in src/. Market-local dates are parsed from source
    fields as dates."""
    for f in (x for x in files if x.startswith("src/hio/") and x.endswith(".py")):
        tree = ast.parse((ROOT / f).read_text(), filename=f)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "date" and not node.args:
                    line = getattr(node, "lineno", 0)
                    fail("valid_time", f"{f}:{line}: .date() on an instant (OBS-INV-005)")
                if node.func.attr in {"fromtimestamp", "utcfromtimestamp"}:
                    fail("valid_time", f"{f}:{getattr(node, 'lineno', 0)}: {node.func.attr} (OBS-INV-005)")


# --- commit trailers ---------------------------------------------------------------------------------


def check_trailers(base: str, head: str) -> None:
    out = subprocess.run(
        ["git", "rev-list", "--no-merges", f"{base}..{head}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for sha in out:
        msg = subprocess.run(
            ["git", "log", "-1", "--format=%B", sha], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        if not re.search(r"^HIO-Actor: \S", msg, re.M):
            fail("trailers", f"{sha[:7]}: no HIO-Actor trailer (metadata hygiene, operating model §8)")


STATIC = {
    "links": check_links,
    "frontmatter": check_frontmatter,
    "yaml": check_yaml,
    "status": check_status,
    "public": check_public,
    "imports": check_imports,
    "valid_time": check_valid_time,
}


def main(argv: list[str]) -> int:
    if argv[:1] == ["trailers"]:
        if len(argv) != 3:
            print("usage: check_repo.py trailers <base> <head>", file=sys.stderr)
            return 2
        check_trailers(argv[1], argv[2])
    else:
        names = argv or list(STATIC)
        unknown = [n for n in names if n not in STATIC]
        if unknown:
            print(f"unknown check(s): {unknown}", file=sys.stderr)
            return 2
        files = tracked_files()
        for n in names:
            STATIC[n](files)
    for e in errors:
        print(e)
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
