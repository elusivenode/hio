"""Scripted receipt of reviewer evidence (harness-0.9 H6; operating model §6.2 step 5.0 to 5.11).

NOT ACTIVATED: nothing in the operating model, CI or hooks references this tool. Run it in a
scratch clone of the repository, on a clean `main`, never in a reviewer's worktree.

Without --publish it performs every check that needs no remote write (5.0 to 5.3, a read-only look
at the provenance tag, and the 5.5 to 5.7 import in a throwaway worktree) and prints a summary
suitable as the body of the receipt's OD. With --publish it also does 5.4 (provenance tag), 5.8
(the pure import commit), 5.9 (remote recheck, `merge --no-ff`, push of `main`) and 5.10
(post-push verification). The status word is "receipt incomplete" until 5.10 passes. Every run
restarts at 5.1 and checks the state it depends on (5.11).

The tool reuses `main`'s `tools/check_review_branch.sh` and `tools/check_review_assignment.py`
(5.3) and `tools/check_repo.py` (5.7); it never reimplements them. `check_repo.py` runs under the
interpreter that runs this tool (use `uv run python tools/hio_receive.py ...`).

Exit codes: 0 all requested steps passed; 1 a STOP condition (message on stderr and in the
summary); 2 usage error.

Usage:
  python tools/hio_receive.py --review-id ID --base SHA --head SHA --branch review/<x>-codex \
      --assignment-source "<5.0.1 location>" --report report.json \
      --second-assignment-checked "<where the receiver looked>" [--scope-terms T ...] \
      [--remote origin] [--od OD-NNNN] [--actor ROLE] [--co-authored-by "Name <email>"] [--publish]

The report is JSON from the reviewer's own final message, held outside the repository:
  {"branch_tip": "<40 hex>", "files": {"<path>": "<sha256>", ...}, "supplied_by": "<how supplied>"}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

MAIN = "main"
SHA_RE = re.compile(r"[0-9a-f]{40}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
ADD_DIRS = ("reviews/records/", "reviews/handoffs/", "reviews/reports/")
README = "reviews/README.md"
STATE_WORDS = ("verified_closed", "remediation_rejected", "open")
FORBIDDEN_STATES = ("accepted", "waived", "approved")  # owner ODs only: the receiver cites, never creates
PLACEHOLDERS = {"", "—", "–", "-"}


class Stop(Exception):
    """A stop condition: the receiver reports it and takes no further step."""


class Git:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd

    def run(self, *args: str, input: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        return subprocess.run(["git", *args], cwd=self.cwd, input=input, capture_output=True, env=env)

    def raw(self, *args: str, input: bytes | None = None) -> bytes:
        p = self.run(*args, input=input)
        if p.returncode:
            err = p.stderr.decode(errors="replace").strip()
            raise Stop(f"git {' '.join(args)} failed ({p.returncode}): {err}")
        return p.stdout

    def out(self, *args: str, input: bytes | None = None) -> str:
        return self.raw(*args, input=input).decode(errors="replace").strip()

    def ok(self, *args: str) -> bool:
        return self.run(*args).returncode == 0


@dataclass
class Ctx:
    args: argparse.Namespace
    root: Path
    g: Git
    hooks: dict[str, Callable[[Ctx], None]]
    report: dict = field(default_factory=dict)
    scope_terms: list[str] = field(default_factory=list)
    prefix: str = ""
    tip: str = ""
    added: list[str] = field(default_factory=list)
    readme_modified: bool = False
    records: list[Record] = field(default_factory=list)
    inventory: dict[str, list[str]] = field(default_factory=dict)
    checks: dict[str, str] = field(default_factory=dict)
    import_commit: str = ""
    merge_commit: str = ""
    ahead_with_import: bool = False
    wt: Path | None = None
    touched: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    pushed_commits: list[str] = field(default_factory=list)
    completed: bool = False

    @property
    def remote(self) -> str:
        return self.args.remote

    @property
    def tag(self) -> str:
        return f"reviews/{self.args.review_id}"

    @property
    def receipt_branch(self) -> str:
        return f"receipt/{self.args.review_id}"

    @property
    def publish(self) -> bool:
        return bool(self.args.publish)

    def sec(self, title: str) -> None:
        self.lines += ["", f"### {title}"]

    def add(self, text: str) -> None:
        self.lines.append(text)


@dataclass
class Record:
    path: str
    id: str
    kind: str
    fm: dict[str, str]
    text: str

    @property
    def name(self) -> str:
        return posixpath.basename(self.path)


# --- small parsers ---------------------------------------------------------------------------------


def front_matter(text: str) -> dict[str, str]:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([a-z_]+):\s*(.*?)\s*(#.*)?$", line)
        if km:
            out[km.group(1)] = km.group(2).strip("\"'")
    return out


def _norm(text: str) -> str:
    return " ".join(text.split())


def split_row(line: str) -> list[str] | None:
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|") and len(s) > 1):
        return None
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)[1:-1]]


def norm_cell(cell: str) -> str:
    cell = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell)
    return _norm(cell.replace("*", "").replace("`", ""))


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def _has_header(block: list[tuple[str, list[str]]]) -> bool:
    return len(block) > 1 and _is_separator(block[1][1])


def parse_tables(lines: list[str]) -> list[tuple[list[str], list[tuple[str, list[str]]]]]:
    """Table blocks: (normalised lower-case header cells, [(line, cells)] body rows).

    A block is a contiguous run of table lines. A header-less run that follows a table across blank
    lines only (the real index has one inside the findings register) continues that table, row by
    row, for each row with the table's column count; a row with another count stays in a header-less
    block of its own, which has no body and so is never classified.
    """
    blocks: list[list[tuple[str, list[str]]]] = []
    cur: list[tuple[str, list[str]]] = []
    orphans: list[tuple[str, list[str]]] = []
    blank = cont = False
    for i, line in enumerate(lines):
        cells = split_row(line)
        if cells is None:
            if line.strip():
                blocks += [b for b in (cur, orphans) if b]
                cur, orphans, blank, cont = [], [], False, False
            else:
                if orphans:
                    blocks.append(orphans)
                    orphans = []
                blank, cont = bool(cur), False
            continue
        if blank:
            blank = False
            nxt = split_row(lines[i + 1]) if i + 1 < len(lines) else None
            if (nxt is not None and _is_separator(nxt)) or not _has_header(cur):
                blocks.append(cur)
                cur = []
            else:
                cont = True
        if cont and len(cells) != len(cur[0][1]):
            orphans.append((line, cells))
        else:
            cur.append((line, cells))
    blocks += [b for b in (cur, orphans) if b]
    tables = []
    for b in blocks:
        header = [norm_cell(c).lower() for c in b[0][1]]
        body = b[2:] if len(b) > 1 and _is_separator(b[1][1]) else []
        tables.append((header, body))
    return tables


def col(header: list[str], *prefixes: str) -> int | None:
    for i, h in enumerate(header):
        if any(h.startswith(p) for p in prefixes):
            return i
    return None


def table_kind(header: list[str]) -> str | None:
    first = header[0] if header else ""
    if first == "review" and col(header, "repository") is not None:
        return "assigned"
    if first == "review" and col(header, "subject") is not None:
        return "reviewed"
    if first == "verification" and col(header, "original review") is not None:
        return "rounds"
    if first == "finding":
        return "findings"
    return None


def row_index(lines: list[str]) -> dict[str, tuple[str | None, list[str], list[str]]]:
    index = {}
    for header, body in parse_tables(lines):
        for line, cells in body:
            index.setdefault(line, (table_kind(header), header, cells))
    return index


def duplicate_problems(lines: list[str]) -> list[str]:
    problems = []
    finding_ids: Counter[str] = Counter()
    for _header, body in parse_tables(lines):
        ids = [norm_cell(cells[0]) for _line, cells in body if cells and norm_cell(cells[0])]
        problems += [f"duplicate id {i!r} in one table" for i, n in Counter(ids).items() if n > 1]
        finding_ids.update(i for i in ids if i.startswith("F-"))
    problems += [f"finding id {i!r} appears {n} times in the file" for i, n in finding_ids.items() if n > 1]
    return sorted(set(problems))


def _residual(lines: list[str], consumed: Counter[str]) -> list[str]:
    left = Counter(consumed)
    out = []
    for line in lines:
        if left[line] > 0:
            left[line] -= 1
        else:
            out.append(line)
    return out


def _sha_prefix_ok(cell: str, full: str) -> bool:
    tokens = re.findall(r"\b[0-9a-f]{7,40}\b", norm_cell(cell))
    return bool(tokens) and full.startswith(tokens[0])


def _matches_assignment(cell: str, source: str) -> bool:
    flat = _norm(re.sub(r"\[([^\]]*)\]\(([^)]*)\)", r"\1 \2", cell).replace("*", "").replace("`", ""))
    if _norm(source) in flat:
        return True
    locators = re.findall(r"OD-\d+", source)
    locators += [posixpath.basename(t) for t in re.findall(r"[\w./-]+\.md\b", source)]
    return bool(locators) and all(t in flat for t in locators)


# --- 5.6 index-row semantics -----------------------------------------------------------------------


def _review_findings(rec: Record) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"^#{1,6}\s+(F-\S+)\s+[—–-]\s+([A-Za-z]+)\b", rec.text, re.M):
        out[m.group(1)] = m.group(2).lower()
    return out


def _check_record_row(kind: str, header: list[str], cells: list[str], rec: Record, source: str) -> list[str]:
    probs = []
    if len(cells) != len(header):
        return [f"{rec.id}: row has {len(cells)} cells, the header {len(header)}"]
    if kind == "reviewed" and rec.kind != "REVIEW":
        probs.append(f"{rec.id}: a received-review row needs a REVIEW record")
    if kind == "rounds" and rec.kind != "VERIFY":
        probs.append(f"{rec.id}: a verification-round row needs a VERIFY record")
    base, head = rec.fm.get("reviewed_base", ""), rec.fm.get("reviewed_head", "")
    for name, full in (("base sha", base), ("head sha", head)):
        i = col(header, name)
        if i is not None and not _sha_prefix_ok(cells[i], full):
            probs.append(f"{rec.id}: {name} cell does not equal the record's {full or 'value (absent)'}")
    i = col(header, "base..")
    if i is not None:
        m = re.search(r"\b([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\b", norm_cell(cells[i]))
        if not (m and base.startswith(m.group(1)) and head.startswith(m.group(2))):
            probs.append(f"{rec.id}: base..head cell does not equal the record's {base[:7]}..{head[:7]}")
    i = col(header, "record")
    if i is not None:
        m = re.search(r"\]\(([^)]+)\)", cells[i])
        if not (m and posixpath.normpath(m.group(1)) == f"records/{rec.name}"):
            probs.append(f"{rec.id}: record cell does not link records/{rec.name}")
    verdict = norm_cell(rec.fm.get("verdict", "")).lower()
    i = col(header, "verdict")
    j = col(header, "reviewer outcome")
    if i is not None or j is not None:
        cell = norm_cell(cells[i if i is not None else j]).lower()  # type: ignore[index]
        if not verdict:
            probs.append(f"{rec.id}: the record has no verdict in its front matter")
        elif i is not None and cell != verdict:
            probs.append(f"{rec.id}: verdict cell {cell!r} does not equal the record's {verdict!r}")
        elif i is None and cell.rsplit(";", 1)[-1].strip() != verdict:
            probs.append(f"{rec.id}: the outcome cell {cell!r} does not end with the record's {verdict!r}")
    i = col(header, "status")
    if kind == "assigned" and i is not None:
        status = norm_cell(cells[i]).lower()
        if not re.match(r"received\b", status):
            probs.append(f"{rec.id}: the status cell must begin with received, not {status[:40]!r}")
        stated = re.search(r"\bverdict\s+([^;,.()]+)", status)
        claimed = stated.group(1).strip() if stated else verdict
        if claimed != verdict:
            probs.append(f"{rec.id}: status cell verdict {claimed!r} does not equal the record's {verdict!r}")
    i = col(header, "assigned by")
    if i is not None and not _matches_assignment(cells[i], source):
        probs.append(f"{rec.id}: assignment cell does not match the 5.0.1 source {source!r}")
    return probs


def _check_finding_n(header: list[str], cells: list[str], recs: list[Record]) -> list[str]:
    fid = norm_cell(cells[0])
    if len(cells) != len(header):
        return [f"{fid}: finding row has {len(cells)} cells, the header {len(header)}"]
    owner = [r for r in recs if r.kind == "REVIEW" and fid in _review_findings(r)]
    if not owner:
        return [f"{fid}: no imported REVIEW record defines this finding (a new finding row must)"]
    rec = owner[0]
    probs = []
    sev = _review_findings(rec)[fid]
    if norm_cell(cells[col(header, "from review") or 1]) != rec.id:
        probs.append(f"{fid}: 'from review' cell is not {rec.id}")
    if norm_cell(cells[col(header, "severity") or 2]).lower() != sev:
        probs.append(f"{fid}: severity cell differs from the record's {sev!r}")
    state = norm_cell(cells[col(header, "state") or 3]).lower()
    if not re.match(r"open\b", state):
        probs.append(f"{fid}: a new finding row must have the state open, not {state!r}")
    for name in ("remediation", "verification", "waiver"):
        i = col(header, name)
        if i is not None and norm_cell(cells[i]) not in PLACEHOLDERS:
            probs.append(f"{fid}: {name} cell must be empty in a new finding row")
    return probs


def _check_finding_s(
    old: list[str], new: list[str], header: list[str], recs: list[Record], od: str | None
) -> list[str]:
    fid = norm_cell(new[0])
    if len(old) != len(header) or len(new) != len(header):
        return [f"{fid}: finding row cell count differs from its header"]
    probs = []
    ci = {
        n: col(header, p)
        for n, p in (
            ("review", "from review"),
            ("severity", "severity"),
            ("state", "state"),
            ("claim", "remediation"),
            ("verification", "verification"),
            ("waiver", "waiver"),
        )
    }
    if any(v is None for v in ci.values()):
        return [f"{fid}: the findings table lacks an expected column"]
    for name in ("review", "severity", "claim", "waiver"):
        i = ci[name]
        if old[i] != new[i]:  # type: ignore[index]
            probs.append(f"{fid}: the {name} cell changed (only the state and verification cells may)")
    if old[0] != new[0]:
        probs.append(f"{fid}: the id cell changed")
    state = norm_cell(new[ci["state"]]).lower()  # type: ignore[index]
    m = re.match(rf"({'|'.join(STATE_WORDS)})\b", state)
    if not m:
        probs.append(f"{fid}: the state cell {state[:40]!r} does not begin with {', '.join(STATE_WORDS)}")
        return probs
    word = m.group(1)
    stated = {r.id: record_outcome(r, fid) for r in recs if r.kind == "VERIFY"}
    verifying = [r for r in recs if stated.get(r.id) == word]
    if not verifying:
        others = sorted({s for s in stated.values() if s})
        probs.append(
            f"{fid}: no imported VERIFY record states {word} for this finding"
            + (f" (its outcome table states {', '.join(others)})" if others else "")
        )
        return probs
    rec = verifying[0]
    vcell = norm_cell(new[ci["verification"]])  # type: ignore[index]
    if rec.id not in vcell:
        probs.append(f"{fid}: the verification cell does not cite the imported record {rec.id}")
    allowed_hex = [rec.fm.get("reviewed_head", ""), rec.fm.get("reviewed_base", "")]
    for cell in (new[ci["state"]], new[ci["verification"]]):  # type: ignore[index]
        for tok in re.findall(r"\b[0-9a-f]{7,40}\b", norm_cell(cell)):
            if not any(a.startswith(tok) for a in allowed_hex if a):
                probs.append(f"{fid}: commit {tok} in the row is not the record's reviewed head or base")
        for rid in re.findall(r"\b(?:VERIFY|REVIEW)-[\w.-]+", norm_cell(cell)):
            if rid.rstrip(".,;:") not in (rec.id, norm_cell(new[ci["review"]])):  # type: ignore[index]
                probs.append(f"{fid}: {rid} in the row is not traceable to the imported record")
        for odid in re.findall(r"\bOD-\d+\b", norm_cell(cell)):
            if odid != od and odid not in rec.text:
                probs.append(f"{fid}: {odid} in the row is not traceable to the record")
    return probs


def record_outcome(rec: Record, fid: str) -> str | None:
    """The state a VERIFY record affirmatively states for `fid` in its per-finding outcome table.

    Only a table row counts: the first cell is exactly the finding id (bold or code allowed) and the
    second cell begins with a state word (bold allowed). A state word in prose, negated or quoted, or
    in any other cell never counts. Rows that disagree state nothing.
    """
    found = set()
    for line in rec.text.splitlines():
        cells = split_row(line)
        if not cells or len(cells) < 2 or cells[0].strip("*` ") != fid:
            continue
        m = re.match(rf"\**({'|'.join(STATE_WORDS)})\b", cells[1])
        if m:
            found.add(m.group(1))
    return found.pop() if len(found) == 1 else None


def check_index(
    main_text: str, staged_text: str, recs: list[Record], source: str, od: str | None
) -> list[str]:
    """5.6: the staged README may differ from main's only by Class N and Class S lines."""
    main_lines, staged_lines = main_text.splitlines(), staged_text.splitlines()
    problems = duplicate_problems(staged_lines)
    if main_lines == staged_lines:
        return problems
    rm = Counter(main_lines) - Counter(staged_lines)
    ad = Counter(staged_lines) - Counter(main_lines)
    if _residual(main_lines, rm) != _residual(staged_lines, ad):
        problems.append("unchanged lines were reordered or moved")
    main_rows, staged_rows = row_index(main_lines), row_index(staged_lines)
    removed: dict[str, tuple[list[str], list[str]]] = {}
    for line in rm.elements():
        info = main_rows.get(line)
        if info is None or info[0] != "findings":
            problems.append(
                f"a removed or changed line is not the superseded version of a Class S row: {line[:90]!r}"
            )
        else:
            removed[norm_cell(info[2][0])] = (info[2], info[1])
    imported_text = "\n".join(r.text for r in recs)
    for line in ad.elements():
        info = staged_rows.get(line)
        if info is None or info[0] is None:
            problems.append(f"an added line is neither a Class N nor a Class S row: {line[:90]!r}")
            continue
        kind, header, cells = info
        fid = norm_cell(cells[0])
        scanned = line
        if kind == "findings" and fid in removed:
            # a Class S row repeats main's other cells verbatim; only the cells it rewrites are scanned
            rewritten = (col(header, "state"), col(header, "verification"))
            scanned = " ".join(cells[i] for i in rewritten if i is not None and i < len(cells))
        for word in FORBIDDEN_STATES:
            if re.search(rf"\b{word}\b", scanned, re.I):
                problems.append(
                    f"{word} in an added row: it exists only as an owner OD, which the receiver "
                    f"cites and never creates: {line[:90]!r}"
                )
        if re.search(r"\bverified_closed\b", line, re.I) and not re.search(
            r"\bverified_closed\b", imported_text, re.I
        ):
            problems.append(
                f"verified_closed in an added row that no imported record supports: {line[:90]!r}"
            )
        if kind == "findings" and fid in removed:
            old, old_header = removed.pop(fid)
            if old_header != header:
                problems.append(f"{fid}: the row moved to another table")
            else:
                problems += _check_finding_s(old, cells, header, recs, od)
        elif kind == "findings":
            problems += _check_finding_n(header, cells, recs)
        else:
            owner = [r for r in recs if r.id == fid]
            if not owner:
                problems.append(f"{fid}: row {kind} matches no imported record's id")
            else:
                problems += _check_record_row(kind or "", header, cells, owner[0], source)
    problems += [f"{fid}: the old row was removed with no superseding Class S row" for fid in removed]
    return sorted(set(problems))


# --- helpers for remote state ---------------------------------------------------------------------


def ls_remote(ctx: Ctx, *patterns: str) -> list[tuple[str, str]]:
    out = ctx.g.out("ls-remote", ctx.remote, *patterns)
    rows = []
    for line in out.splitlines():
        if line.strip():
            sha, _, name = line.partition("\t")
            rows.append((sha.strip(), name.strip()))
    return rows


def remote_tip(ctx: Ctx, label: str) -> str:
    ref = f"refs/heads/{ctx.args.branch}"
    rows = ls_remote(ctx, ref)
    if not rows:
        raise Stop(f"{label}: {ctx.remote} has no {ref}: the branch is absent or was deleted")
    if len(rows) > 1:
        raise Stop(f"{label}: ls-remote returned several lines for {ref}: {rows}")
    sha, name = rows[0]
    if not SHA_RE.fullmatch(sha) or name != ref:
        raise Stop(f"{label}: ls-remote returned an unexpected shape: {rows[0]!r}")
    return sha


def remote_tag_peel(ctx: Ctx) -> str | None:
    ref = f"refs/tags/{ctx.tag}"
    rows = dict((name, sha) for sha, name in ls_remote(ctx, ref, f"{ref}^{{}}"))
    return rows.get(f"{ref}^{{}}") or rows.get(ref)


def local_tag_peel(ctx: Ctx) -> str | None:
    p = ctx.g.run("rev-parse", "--verify", "-q", f"refs/tags/{ctx.tag}^{{commit}}")
    return p.stdout.decode().strip() if p.returncode == 0 else None


def blob_at(g: Git, rev: str, path: str) -> bytes:
    return g.raw("cat-file", "blob", f"{rev}:{path}")


# --- 5.0 inputs ------------------------------------------------------------------------------------


def step_inputs(ctx: Ctx) -> None:
    a = ctx.args
    missing = []
    for flag, value in (
        ("--review-id", a.review_id),
        ("--base", a.base),
        ("--head", a.head),
        ("--branch", a.branch),
        ("--assignment-source (5.0.1)", a.assignment_source),
        ("--report (5.0.2)", a.report),
        ("--second-assignment-checked (5.0.3)", a.second_assignment_checked),
    ):
        if not (value or "").strip():
            missing.append(flag)
    if missing:
        raise Stop(
            f"5.0: input absent: {', '.join(missing)}. The receiver reports it absent and stops; "
            "it never substitutes the record's own statements."
        )
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.review_id):
        raise Stop(f"5.0: review id {a.review_id!r} has an unexpected shape")
    for name, sha in (("base", a.base), ("head", a.head)):
        if not SHA_RE.fullmatch(sha):
            raise Stop(f"5.0: --{name} must be a full 40-character lowercase sha, not {sha!r}")
    if not re.fullmatch(r"review/[A-Za-z0-9._/-]+", a.branch) or ".." in a.branch:
        raise Stop(f"5.0: --branch must look like review/<id>-codex, not {a.branch!r}")
    if a.publish and not re.fullmatch(r"OD-\d{4}", a.od or ""):
        raise Stop("5.0: --publish needs --od OD-NNNN (the HIO-Actor trailer names the receipt's OD)")
    terms = [t.strip() for raw in a.scope_terms for t in raw.split(",") if t.strip()]
    ctx.scope_terms = terms
    rp = Path(a.report)
    if not rp.is_file():
        raise Stop(f"5.0.2: the reviewer's independent report {a.report!r} is absent")
    if rp.resolve().is_relative_to(ctx.root.resolve()):
        raise Stop(
            "5.0.2: the report is inside the repository; it must come from somewhere other than the branch"
        )
    try:
        report = json.loads(rp.read_text())
    except (OSError, ValueError) as exc:
        raise Stop(f"5.0.2: the report is not readable JSON: {exc}") from exc
    if not isinstance(report, dict):
        raise Stop("5.0.2: the report must be a JSON object")
    if not SHA_RE.fullmatch(str(report.get("branch_tip", ""))):
        raise Stop("5.0.2: the report lacks a 40-character branch_tip")
    files = report.get("files")
    if not isinstance(files, dict) or not files:
        raise Stop("5.0.2: the report lacks the files map (path -> sha256)")
    bad = [p for p, h in files.items() if not isinstance(h, str) or not SHA256_RE.fullmatch(h)]
    if bad:
        raise Stop(f"5.0.2: the report has malformed sha256 values for {bad}")
    if not str(report.get("supplied_by", "")).strip():
        raise Stop("5.0.2: the report does not say how it was supplied (supplied_by)")
    ctx.report = report
    ctx.sec("5.0 Inputs")
    ctx.add(f"- review id `{a.review_id}`; base `{a.base}`; head `{a.head}`; branch `{a.branch}`")
    ctx.add(f"- 5.0.1 assignment source: {a.assignment_source}")
    ctx.add(
        f"- 5.0.2 reviewer report (supplied by: {report['supplied_by']}): tip `{report['branch_tip']}`, "
        f"{len(files)} file(s)"
    )
    ctx.add(f"- 5.0.3 second owner-authored assignment: {a.second_assignment_checked}")
    if terms:
        ctx.add(f"- scope terms: {', '.join(terms)}")


def step_preflight(ctx: Ctx) -> None:
    g, a = ctx.g, ctx.args
    if not g.ok("remote", "get-url", ctx.remote):
        raise Stop(f"remote {ctx.remote!r} is not configured in this clone")
    branch = g.run("symbolic-ref", "--short", "-q", "HEAD").stdout.decode().strip()
    if branch != MAIN:
        raise Stop(
            f"run the receipt on a clean `{MAIN}` in a scratch clone "
            f"(this clone is on {branch or 'a detached HEAD'!r})"
        )
    if g.out("status", "--porcelain"):
        raise Stop("the working tree is not clean; use a scratch clone")
    for name, sha in (("base", a.base), ("head", a.head)):
        if not g.ok("cat-file", "-e", f"{sha}^{{commit}}"):
            raise Stop(f"the assigned {name} {sha} is not a commit in this clone; fetch it first")
    for tool in ("tools/check_review_branch.sh", "tools/check_review_assignment.py", "tools/check_repo.py"):
        if not g.ok("cat-file", "-e", f"{MAIN}:{tool}"):
            raise Stop(f"`{MAIN}` has no {tool}; the receipt reuses main's checks")
    ctx.prefix = "hio/" if g.ok("cat-file", "-e", f"{a.head}:hio/AGENTS.md") else ""


# --- 5.1 to 5.3 ------------------------------------------------------------------------------------


def step_tip(ctx: Ctx) -> None:
    g, a = ctx.g, ctx.args
    tip = remote_tip(ctx, "5.1")
    ref = f"refs/heads/{a.branch}"
    g.out("fetch", "--no-tags", ctx.remote, ref)
    fetched = g.out("rev-parse", "FETCH_HEAD")
    if fetched != tip:
        raise Stop(
            f"5.1: FETCH_HEAD {fetched} differs from the ls-remote tip {tip}: "
            "the branch moved during the fetch"
        )
    if tip != ctx.report["branch_tip"]:
        raise Stop(
            f"5.1: the branch tip {tip} differs from the reviewer's reported tip {ctx.report['branch_tip']}: "
            "the branch moved after the report, or the report is wrong. The owner decides; changed work "
            "needs a new assignment at a newly stated head."
        )
    ctx.tip = tip
    ctx.sec("5.1 Tip")
    ctx.add(f"- T = `{tip}` (ls-remote = FETCH_HEAD = reviewer's reported tip)")


def step_main_state(ctx: Ctx) -> None:
    """Fetch main, refuse a stale or diverged target, and find an import of T already on main (5.11)."""
    g = ctx.g
    g.out("fetch", "--no-tags", ctx.remote, f"+refs/heads/{MAIN}:refs/remotes/{ctx.remote}/{MAIN}")
    local, remote = g.out("rev-parse", MAIN), g.out("rev-parse", f"{ctx.remote}/{MAIN}")
    found = g.out(
        "log", MAIN, "--extended-regexp", f"--grep=^Review-Commit: {ctx.tip}$", "--format=%H"
    ).split()
    ctx.import_commit = found[0] if found else ""
    if ctx.import_commit:
        msg = g.out("log", "-1", "--format=%B", ctx.import_commit)
        if not re.search(rf"^Review-Id: {re.escape(ctx.args.review_id)}$", msg, re.M):
            raise Stop(
                f"{ctx.tip} is already imported on main at {ctx.import_commit} under a different Review-Id"
            )
    ctx.sec("Target")
    if local == remote:
        ctx.add(f"- local `{MAIN}` = `{ctx.remote}/{MAIN}` = `{local}`")
    elif g.ok("merge-base", "--is-ancestor", remote, local):
        if ctx.import_commit and not g.ok("merge-base", "--is-ancestor", ctx.import_commit, remote):
            ctx.ahead_with_import = True
            ctx.add(
                f"- local `{MAIN}` `{local}` is ahead of `{ctx.remote}/{MAIN}` `{remote}` by this receipt "
                "(merged locally, push pending; 5.11)"
            )
        else:
            raise Stop(
                f"local {MAIN} has commits that are not on {ctx.remote}/{MAIN} and are not this receipt"
            )
    elif g.ok("merge-base", "--is-ancestor", local, remote):
        raise Stop(
            f"stale target: local {MAIN} {local} is behind {ctx.remote}/{MAIN} {remote}; "
            "update the scratch clone"
        )
    else:
        raise Stop(f"local {MAIN} and {ctx.remote}/{MAIN} have diverged")


def step_inventory(ctx: Ctx) -> None:
    g, a, p = ctx.g, ctx.args, ctx.prefix
    if not g.ok("merge-base", "--is-ancestor", a.head, ctx.tip):
        raise Stop(
            f"the review branch tip {ctx.tip} does not descend from the assigned head {a.head}: "
            "the reviewed head differs from the assignment"
        )
    raw = g.raw("diff", "--name-status", "--no-renames", "-z", a.head, ctx.tip).decode().split("\0")
    entries = [(raw[i], raw[i + 1]) for i in range(0, len(raw) - 1, 2)]
    allowed_dirs = tuple(p + d for d in ADD_DIRS)
    bad = [
        f"{s} {path}"
        for s, path in entries
        if not ((s == "A" and path.startswith(allowed_dirs)) or (s == "M" and path == p + README))
    ]
    if bad:
        raise Stop(
            "5.2: change(s) outside the allowed set "
            f"(A under records/, handoffs/, reports/; M reviews/README.md): {bad}"
        )
    ctx.added = sorted(path for s, path in entries if s == "A")
    ctx.readme_modified = any(path == p + README for _s, path in entries)
    found = set(ctx.added) | ({p + README} if ctx.readme_modified else set())
    reported: dict[str, str] = ctx.report["files"]
    expected = set(reported)
    missing = sorted(expected - found)
    extra = sorted(set(ctx.added) - expected)
    mismatched = []
    for path in sorted(expected & found):
        actual = hashlib.sha256(blob_at(g, ctx.tip, path)).hexdigest()
        if actual != reported[path]:
            mismatched.append(f"{path}: reported {reported[path]}, found {actual}")
    ctx.inventory = {
        "expected": sorted(expected),
        "found": sorted(found),
        "missing": missing,
        "extra": extra,
        "hash mismatch": mismatched,
    }
    ctx.sec("5.2 Inventory (reconciled both ways)")
    for k, v in ctx.inventory.items():
        ctx.add(
            f"- {k}: {', '.join(f'`{x}`' for x in v) if v else 'none'}"
            if k != "hash mismatch"
            else f"- {k}: {'; '.join(v) if v else 'none'}"
        )
    if missing or extra or mismatched:
        raise Stop(
            f"5.2: inventory mismatch (missing {missing}; extra {extra}; hash mismatch {mismatched}). "
            "A missing or extra file is a stop, never a note."
        )
    records = []
    for path in ctx.added:
        if re.fullmatch(rf"{re.escape(p)}reviews/records/(REVIEW|VERIFY)-[^/]+\.md", path):
            text = blob_at(g, ctx.tip, path).decode(errors="replace")
            fm = front_matter(text)
            records.append(Record(path, fm.get("id", ""), posixpath.basename(path).split("-")[0], fm, text))
    ctx.records = records


def step_checks(ctx: Ctx) -> None:
    g, a = ctx.g, ctx.args
    ref = f"refs/heads/{a.branch}"
    have = g.run("rev-parse", "--verify", "-q", ref).stdout.decode().strip()
    if have and have != ctx.tip:
        raise Stop(f"a local branch {a.branch} exists at {have}, not T; remove it from this scratch clone")
    if not have:
        g.out("update-ref", ref, ctx.tip)
        ctx.notes.append(
            f"created the local ref {ref} at T so that main's check_review_assignment.py can resolve it"
        )
    ctx.sec("5.3 Checks (main's copies)")
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    scope = subprocess.run(
        ["sh", "tools/check_review_branch.sh", a.head, ctx.tip],
        cwd=ctx.root,
        capture_output=True,
        text=True,
        env=env,
    )
    ctx.add(f"- `tools/check_review_branch.sh {a.head[:7]} {ctx.tip[:7]}`: exit {scope.returncode}")
    cmd = [
        sys.executable,
        "tools/check_review_assignment.py",
        "--review-id",
        a.review_id,
        "--base",
        a.base,
        "--head",
        a.head,
        "--branch",
        a.branch,
        "--assignment-source",
        a.assignment_source,
    ]
    if ctx.scope_terms:
        cmd += ["--scope-terms", ",".join(ctx.scope_terms)]
    assign = subprocess.run(cmd, cwd=ctx.root, capture_output=True, text=True, env=env)
    ctx.add(f"- `tools/check_review_assignment.py` with the 5.0.1 values: exit {assign.returncode}")
    ctx.checks["scope"] = "PASS" if scope.returncode == 0 else "FAIL"
    ctx.checks["assignment"] = "PASS" if assign.returncode == 0 else "FAIL"
    if scope.returncode or assign.returncode:
        detail = "\n".join(
            x.strip() for x in (scope.stdout, scope.stderr, assign.stdout, assign.stderr) if x.strip()
        )
        raise Stop(f"5.3: scope {ctx.checks['scope']}, assignment {ctx.checks['assignment']}:\n{detail}")


# --- 5.4 provenance tag ----------------------------------------------------------------------------


def tag_precheck(ctx: Ctx) -> tuple[str | None, str | None]:
    remote, local = remote_tag_peel(ctx), local_tag_peel(ctx)
    for where, peel in (("remote", remote), ("local", local)):
        if peel is not None and peel != ctx.tip:
            raise Stop(
                f"5.4: the {where} tag {ctx.tag} exists at {peel}, not T {ctx.tip}: "
                "a mismatch for the owner. A tag is never moved or deleted."
            )
    ctx.sec("5.4 Provenance tag")
    ctx.add(f"- `{ctx.tag}`: remote {remote or 'absent'}; local {local or 'absent'}; T = `{ctx.tip}`")
    return remote, local


def step_tag(ctx: Ctx) -> None:
    g = ctx.g
    remote, local = tag_precheck(ctx)
    ref = f"refs/tags/{ctx.tag}"
    if local is None and remote is None:
        g.out(
            "tag",
            "-a",
            ctx.tag,
            ctx.tip,
            "-m",
            f"Provenance tag for {ctx.args.review_id}: reviewer branch {ctx.args.branch} at {ctx.tip} "
            "(evidence receipt; not acceptance)",
        )
    elif local is None:
        g.out("fetch", "--no-tags", ctx.remote, f"{ref}:{ref}")
    if remote is None:
        p = g.run("push", ctx.remote, ref)
        if p.returncode:
            raise Stop(
                f"5.4: the tag push failed or was rejected (nothing else was done; retry): "
                f"{p.stderr.decode(errors='replace').strip()}"
            )
        if ctx.import_commit:
            ctx.notes.append(
                f"the remote tag {ctx.tag} was missing after the import; recreated at T. "
                "Record in the OD that the receipt was incomplete until then."
            )
    peel = remote_tag_peel(ctx)
    if peel != ctx.tip:
        raise Stop(f"5.4: after the push, ls-remote reports the tag peeling to {peel}, not T {ctx.tip}")
    ctx.touched.append(f"tag {ctx.tag} at T on {ctx.remote}")
    ctx.add(f"- verified: `{ctx.tag}^{{}}` on {ctx.remote} = T")


# --- 5.5 to 5.7 import and verification -------------------------------------------------------------


def _prepare_receipt_branch(ctx: Ctx) -> None:
    g, rb = ctx.g, ctx.receipt_branch
    g.run("worktree", "prune")
    tip = g.run("rev-parse", "--verify", "-q", f"refs/heads/{rb}").stdout.decode().strip()
    if not tip:
        return
    main_tip = g.out("rev-parse", MAIN)
    msg = g.out("log", "-1", "--format=%B", tip)
    ours = re.search(rf"^Review-Commit: {ctx.tip}$", msg, re.M) is not None
    if tip != main_tip and not ours:
        raise Stop(f"{rb} exists at {tip} with unrecognised content; remove it or investigate (5.11)")
    g.out("branch", "-D", rb)
    ctx.notes.append(f"discarded the disposable {rb} at {tip} and rebuilt it from the current {MAIN} (5.11)")


def step_import(ctx: Ctx) -> None:
    g, a = ctx.g, ctx.args
    ctx.sec("5.5 Import")
    wt = Path(tempfile.mkdtemp(prefix="hio-receive-")) / "wt"
    ctx.wt = wt
    if ctx.publish:
        _prepare_receipt_branch(ctx)
        g.out("worktree", "add", "-q", "-b", ctx.receipt_branch, str(wt), MAIN)
        ctx.add(f"- `{ctx.receipt_branch}` cut at {MAIN} `{g.out('rev-parse', MAIN)}`")
    else:
        g.out("worktree", "add", "-q", "--detach", str(wt), MAIN)
        ctx.add(
            f"- throwaway worktree cut at {MAIN} `{g.out('rev-parse', MAIN)}` "
            f"(dry run; no {ctx.receipt_branch} created)"
        )
    w = Git(wt)
    for path in ctx.added:
        w.out("checkout", ctx.tip, "--", path)
    ctx.add(f"- `git checkout T -- <file>` for {len(ctx.added)} added file(s)")
    if ctx.readme_modified:
        patch = g.raw("diff", "--no-renames", a.head, ctx.tip, "--", ctx.prefix + README)
        p = w.run("apply", "--index", "-", input=patch)
        if p.returncode:
            raise Stop(
                f"5.5: the reviewer's README diff does not apply cleanly to {MAIN}: "
                f"{p.stderr.decode(errors='replace').strip()}"
            )
        ctx.add("- the reviewer's `reviews/README.md` diff applied cleanly")

    ctx.sec("5.6 Index-row semantics")
    path = ctx.prefix + README
    main_text = g.raw("show", f"{MAIN}:{path}").decode()
    staged_text = w.raw("show", f":{path}").decode()
    problems = check_index(main_text, staged_text, ctx.records, a.assignment_source, a.od)
    if problems:
        ctx.checks["index rows"] = "FAIL"
        raise Stop(
            "5.6: refused (the reviewer's README diff is not applied; report the discrepancy to the "
            "owner):\n  - " + "\n  - ".join(problems)
        )
    ctx.checks["index rows"] = "PASS"
    ctx.add(
        "- README differs from main only by Class N / Class S lines supported by the imported records"
        if ctx.readme_modified
        else "- README unchanged"
    )

    ctx.sec("5.7 Verify")
    for rel in ctx.added:
        staged, expected = w.out("rev-parse", f":{rel}"), g.out("rev-parse", f"{ctx.tip}:{rel}")
        if staged != expected:
            raise Stop(f"5.7: blob id of {rel} is {staged} in the import but {expected} at T")
    ctx.checks["blob identity"] = "PASS"
    ctx.add(f"- blob identity: {len(ctx.added)} imported file(s) equal T's")
    names = [n for n in w.raw("diff", "--cached", "--name-only", "-z").decode().split("\0") if n]
    outside = [n for n in names if not n.startswith(ctx.prefix + "reviews/")]
    if outside:
        raise Stop(f"5.7: paths outside reviews/ are staged: {outside}")
    want = set(ctx.added) | ({path} if ctx.readme_modified else set())
    if set(names) != want:
        raise Stop(f"5.7: the staged set {sorted(names)} differs from the inventory {sorted(want)}")
    ctx.add(f"- nothing outside `{ctx.prefix}reviews/` is staged ({len(names)} path(s))")
    cr = subprocess.run([sys.executable, "tools/check_repo.py"], cwd=wt, capture_output=True, text=True)
    ctx.checks["check_repo"] = "PASS" if cr.returncode == 0 else "FAIL"
    if cr.returncode:
        raise Stop(f"5.7: tools/check_repo.py failed:\n{(cr.stdout + cr.stderr).strip()}")
    ctx.add("- `tools/check_repo.py`: PASS")


def receipt_checks(ctx: Ctx) -> str:
    order = ("scope", "assignment", "index rows", "blob identity", "check_repo")
    return "; ".join(f"{k} {ctx.checks.get(k, 'NOT RUN')}" for k in order)


def actor(ctx: Ctx) -> str:
    return f"HIO-Actor: {ctx.args.actor} (evidence receipt, {ctx.args.od})"


def step_commit(ctx: Ctx) -> None:
    """5.8: the pure import commit, then the 5.7 trailers check on the unpublished commit."""
    a, g = ctx.args, ctx.g
    assert ctx.wt is not None
    w = Git(ctx.wt)
    records = [
        f"Record: {p} blob {g.out('rev-parse', f'{ctx.tip}:{p}')} sha256 "
        f"{hashlib.sha256(blob_at(g, ctx.tip, p)).hexdigest()}"
        for p in ctx.added
    ]
    trailers = [
        f"Review-Id: {a.review_id}",
        f"Review-Branch: {a.branch}",
        f"Review-Commit: {ctx.tip}",
        f"Reviewed-Base: {a.base}",
        f"Reviewed-Head: {a.head}",
        f"Assignment-Source: {_norm(a.assignment_source)}",
        f"Reviewer-Report: {_norm(str(ctx.report['supplied_by']))}",
        *records,
        "Inventory: complete",
        f"Receipt-Checks: {receipt_checks(ctx)}",
        actor(ctx),
    ]
    message = [
        "-m",
        f"Receive {a.review_id} evidence by byte-identical import (receipt only; {a.od})",
        "-m",
        "\n".join(trailers),
    ]
    if a.co_authored_by:
        message += ["-m", f"Co-Authored-By: {a.co_authored_by}"]
    w.out("commit", "-q", *message)
    sha = w.out("rev-parse", "HEAD")
    ctx.touched.append(f"import commit {sha} on {ctx.receipt_branch} (unmerged)")
    ctx.sec("5.8 Import commit")
    ctx.add(f"- `{sha}` on `{ctx.receipt_branch}`: pure import, trailers per §5.8")
    cr = subprocess.run(
        [sys.executable, "tools/check_repo.py", "trailers", f"{ctx.remote}/{MAIN}", "HEAD"],
        cwd=ctx.wt,
        capture_output=True,
        text=True,
    )
    if cr.returncode:
        raise Stop(
            f"5.7: check_repo trailers {ctx.remote}/{MAIN} HEAD failed; fix the unpublished import commit:\n"
            f"{(cr.stdout + cr.stderr).strip()}"
        )
    ctx.add(f"- `tools/check_repo.py trailers {ctx.remote}/{MAIN} HEAD`: PASS")
    ctx.import_commit = sha
    ctx.pushed_commits.append(sha)


def cleanup_worktree(ctx: Ctx) -> None:
    if ctx.wt is not None:
        ctx.g.run("worktree", "remove", "--force", str(ctx.wt))
        shutil.rmtree(ctx.wt.parent, ignore_errors=True)
        ctx.wt = None


# --- 5.9 merge and publish, 5.10 verification ------------------------------------------------------


def step_merge_and_push(ctx: Ctx) -> None:
    g, a = ctx.g, ctx.args
    hook = ctx.hooks.get("before_recheck")
    if hook:
        hook(ctx)
    ctx.sec("5.9 Final remote recheck, merge, publish")
    tip = remote_tip(ctx, "5.9")
    if tip != ctx.tip or tip != ctx.report["branch_tip"]:
        raise Stop(
            f"5.9: the branch moved (now {tip}; T {ctx.tip}). Do not merge; the tag is left in place; "
            "the owner decides."
        )
    peel = remote_tag_peel(ctx)
    if peel != ctx.tip:
        raise Stop(f"5.9: the tag {ctx.tag} now peels to {peel}, not T {ctx.tip}. Do not merge.")
    ctx.add("- branch tip and tag unchanged since 5.1/5.4")
    g.out("fetch", "--no-tags", ctx.remote, f"+refs/heads/{MAIN}:refs/remotes/{ctx.remote}/{MAIN}")
    local, remote = g.out("rev-parse", MAIN), g.out("rev-parse", f"{ctx.remote}/{MAIN}")
    if not ctx.ahead_with_import:
        if local != remote:
            raise Stop(
                f"5.9: {ctx.remote}/{MAIN} moved to {remote} (local {local}) since the import was cut. "
                "Do not merge; rerun from 5.1 (the import is rebuilt)."
            )
        subject = f"Merge {ctx.receipt_branch}: receive {a.review_id} evidence (receipt only)"
        msg = ["-m", subject, "-m", actor(ctx)]
        if a.co_authored_by:
            msg += ["-m", f"Co-Authored-By: {a.co_authored_by}"]
        p = g.run("merge", "--no-ff", *msg, ctx.receipt_branch)
        if p.returncode:
            g.run("merge", "--abort")
            raise Stop(
                f"5.9: the merge did not complete: {(p.stdout + p.stderr).decode(errors='replace').strip()}"
            )
        local = g.out("rev-parse", MAIN)
        ctx.touched.append(f"merge {local} on local {MAIN} (not pushed)")
        ctx.add(f"- merged `{ctx.receipt_branch}` `--no-ff` into {MAIN}: `{local}`")
    else:
        changed = g.out("diff", "--name-only", remote, local).splitlines()
        outside = [n for n in changed if not n.startswith(ctx.prefix + "reviews/")]
        if outside:
            raise Stop(f"5.9: the unpublished local {MAIN} changes paths outside reviews/: {outside}")
        ctx.add(f"- local {MAIN} `{local}` already holds the merge; re-verified, pushing")
    ctx.merge_commit = local
    ctx.pushed_commits.append(local)
    p = g.run("push", ctx.remote, f"refs/heads/{MAIN}:refs/heads/{MAIN}")
    if p.returncode:
        raise Stop(
            f"5.9: the push of {MAIN} failed or was rejected ({p.stderr.decode(errors='replace').strip()}). "
            f"State: merged locally, push failed (5.11): re-verify and push again."
        )
    ctx.add(f"- pushed `{MAIN}` to {ctx.remote}")


def step_verify_published(ctx: Ctx) -> None:
    """5.10: remote main equals the local merge, the blobs on main equal T's, the remote tag peels to T."""
    g = ctx.g
    ctx.sec("5.10 Post-push verification")
    local = g.out("rev-parse", MAIN)
    rows = ls_remote(ctx, f"refs/heads/{MAIN}")
    if len(rows) != 1 or rows[0][0] != local:
        raise Stop(f"5.10: remote {MAIN} is {rows}, local {MAIN} is {local}")
    ctx.add(f"- remote `{MAIN}` = local `{MAIN}` = `{local}`")
    for rel in ctx.added:
        on_main, at_t = g.out("rev-parse", f"{MAIN}:{rel}"), g.out("rev-parse", f"{ctx.tip}:{rel}")
        if on_main != at_t:
            raise Stop(f"5.10: blob of {rel} on {MAIN} is {on_main}, T's is {at_t}")
    ctx.add(f"- blobs on `{MAIN}` equal T's for {len(ctx.added)} file(s)")
    peel = remote_tag_peel(ctx)
    if peel != ctx.tip:
        raise Stop(f"5.10: the remote tag {ctx.tag} peels to {peel}, not T")
    ctx.add(f"- remote tag `{ctx.tag}` peels to T")
    ctx.completed = True


def step_verify_existing(ctx: Ctx) -> None:
    """The import of T is already on main: verify blob identity there (used by dry runs and restarts)."""
    g = ctx.g
    ctx.sec("Existing import")
    ctx.add(f"- T is already imported on `{MAIN}` by `{ctx.import_commit}` (Review-Id matches)")
    for rel in ctx.added:
        on_main, at_t = g.out("rev-parse", f"{MAIN}:{rel}"), g.out("rev-parse", f"{ctx.tip}:{rel}")
        if on_main != at_t:
            raise Stop(f"the blob of {rel} on {MAIN} is {on_main}, T's is {at_t}")
    ctx.checks["blob identity"] = "PASS"
    ctx.add(f"- blobs on `{MAIN}` equal T's for {len(ctx.added)} file(s)")


# --- driver -----------------------------------------------------------------------------------------


def flow(ctx: Ctx) -> None:
    step_inputs(ctx)
    step_preflight(ctx)
    step_tip(ctx)
    step_main_state(ctx)
    step_inventory(ctx)
    step_checks(ctx)
    if ctx.import_commit:
        if not ctx.publish:
            tag_precheck(ctx)
            step_verify_existing(ctx)
            return
        step_tag(ctx)
        step_verify_existing(ctx)
        if ctx.ahead_with_import:
            step_merge_and_push(ctx)
        step_verify_published(ctx)
        return
    if ctx.publish:
        step_tag(ctx)
    else:
        tag_precheck(ctx)
    step_import(ctx)
    if not ctx.publish:
        return
    step_commit(ctx)
    cleanup_worktree(ctx)
    step_merge_and_push(ctx)
    step_verify_published(ctx)


def status_word(ctx: Ctx, stop: str | None) -> str:
    if not ctx.publish:
        return (
            "checks FAILED (dry run; nothing was published)"
            if stop
            else "checks passed (dry run; nothing was published)"
        )
    if ctx.completed:
        return "received (5.10 passed; the index status cell is a separate administrative commit)"
    if ctx.touched:
        return "receipt incomplete"
    return "not started (nothing was pushed or merged; 5.11: nothing has changed)"


def recovery_state(ctx: Ctx) -> str:
    if any(t.startswith("merge ") for t in ctx.touched):
        return "merged locally, push of main failed or not verified: re-verify 5.9 and push (5.11)"
    if any(t.startswith("import commit") for t in ctx.touched):
        return "import committed, not merged: re-verify 5.9 then merge, or discard receipt/<id> (5.11)"
    if any(t.startswith("tag ") for t in ctx.touched):
        return "tag pushed, no import: harmless; resume at 5.5 with the same T, or abandon with a note (5.11)"
    return "nothing pushed"


def receive(argv: list[str], hooks: dict[str, Callable[[Ctx], None]] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scripted evidence receipt (operating model §6.2 step 5)")
    ap.add_argument("--review-id", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--branch", required=True, help="review/<id>-codex")
    ap.add_argument("--assignment-source", required=True, help="the 5.0.1 location string")
    ap.add_argument("--report", required=True, help="JSON: branch_tip, files {path: sha256}, supplied_by")
    ap.add_argument("--second-assignment-checked", required=True, help="5.0.3: where the receiver looked")
    ap.add_argument("--scope-terms", nargs="*", default=[])
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--od", help="OD-NNNN for the HIO-Actor trailer (required with --publish)")
    ap.add_argument("--actor", default="claude/implementation-agent", help="role in the HIO-Actor trailer")
    ap.add_argument("--co-authored-by", help="'Name <email>' for a Co-Authored-By trailer (agent receivers)")
    ap.add_argument("--publish", action="store_true", help="also do 5.4 and 5.8 to 5.10 (writes the remote)")
    args = ap.parse_args(argv)
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode:
        print("STOP: not inside a git repository", file=sys.stderr)
        return 1
    root = Path(top.stdout.strip())
    ctx = Ctx(args=args, root=root, g=Git(root), hooks=hooks or {})
    stop: str | None = None
    try:
        flow(ctx)
    except Stop as exc:
        stop = str(exc)
    except (OSError, ValueError, KeyError) as exc:
        stop = f"unexpected {type(exc).__name__}: {exc}"
    finally:
        cleanup_worktree(ctx)
    ctx.lines.insert(0, f"## Receipt of {args.review_id} ({'publish' if ctx.publish else 'dry run'})")
    if stop:
        ctx.lines += ["", "### STOP", stop]
    ctx.lines += ["", "### Status", f"- STATUS: {status_word(ctx, stop)}"]
    if ctx.publish and not ctx.completed:
        ctx.lines.append(f"- state (5.11): {recovery_state(ctx)}")
    if ctx.touched:
        ctx.lines += [f"- done: {t}" for t in ctx.touched]
    if ctx.checks:
        ctx.lines.append(f"- Receipt-Checks: {receipt_checks(ctx)}")
    ctx.lines += [f"- note: {n}" for n in ctx.notes]
    ctx.lines += ["", "### CI integration checks (separate from evidence integrity)"]
    shown = ", ".join(f"`{c}`" for c in ctx.pushed_commits) or "none pushed by this run"
    ctx.lines.append(
        f"- NOT REPORTED by this tool. Report the CI run id and head SHA for every pushed commit: {shown}."
    )
    try:
        sweep = ls_remote(ctx, "refs/heads/review/*")
        ctx.lines += [
            "",
            f"### Receipt sweep: review branches on {ctx.remote} (check each against the index)",
        ]
        ctx.lines += [f"- `{name}` `{sha}`" for sha, name in sweep] or ["- none"]
    except Stop:
        ctx.lines.append("- receipt sweep unavailable (ls-remote failed)")
    print("\n".join(ctx.lines))
    if stop:
        print(f"STOP: {stop}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(receive(sys.argv[1:]))
