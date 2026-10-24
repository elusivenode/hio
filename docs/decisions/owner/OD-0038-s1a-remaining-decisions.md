---
id: OD-0038
title: "Owner decisions for S1a: Q-007 ratified, Q-008 accepted for S1a only, Q-005a confirmed, the capture-clock archive question deferred to S1b design; not S1a acceptance"
decision: approve
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-s1a-remaining-decisions.md (pasted by the owner, verbatim)
  sha256: 46e013c1393468617564f77bbe96cd5db8da2639428b8da069ce3b5bce401f5a
  date: 2026-10-25
  quote: "I adopt the following decisions for S1a, subject to your verification that the underlying evidence and approved scope remain unchanged."
applies_to:
  - path: /
    revision: 3fd129e946498e180b9f78a13d3f745afb46c638   # main when the decisions were verified
  - path: src/, tests/, tools/, pyproject.toml, uv.lock, .github/
    revision: 084154ccb0fd1c13150d77d02eb525007a5b161e   # the reviewed S1a head; identical on main
related: {adrs: [HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0010], tasks: [T-0005], findings: []}
---

# OD-0038: the remaining S1a owner decisions

## Condition checked first: evidence and approved scope unchanged

The owner adopted the decisions subject to this verification. All checks passed on
2026-10-25 at `main` = `3fd129e946498e180b9f78a13d3f745afb46c638` (equal to `origin/main`).

| Check | Result |
|---|---|
| Implementation unchanged since the reviewed head | `git diff 084154c 3fd129e -- src tests tools pyproject.toml uv.lock .github` is empty |
| Approved standards, harness, ADRs and `AGENTS.md` unchanged since the reviewed head | `git diff --quiet 084154c 3fd129e -- docs/standards docs/harness docs/decisions/HIO-ADR-* AGENTS.md` exit 0 |
| Approved contract blobs at `3fd129e` | Q-001 r4 `419992f2…`, Q-002 r5 `d0a25b3b…`, Q-002-R1 r1 `cb7a937d…`: equal to OD-0029, OD-0030 and OD-0035 |
| Observations v0.3 candidate | blob `61ddd58ed49af9fed395eaa17e61dfc7fb451fe6`, unchanged (not decided here) |
| Repository checks | `uv run python tools/check_repo.py`: PASS, 0 problems |
| Release reproduction | `hio.jobs.s1a` run twice into empty stores at `3fd129e`: identical output; the four `data.csv` sha256 are AUD `9e3a03e9…`, USD `97faf4e8…`, FX decomposition `6e628493…`, FX excess `b8ea0d6f…`, equal to the S1a baseline |

No decision contradicts an approved contract or needs a wider authority change. The basis for
each is given with the decision below.

## Owner action

### 1. Q-007: dependencies ratified

**Ratified:** PyYAML as a runtime dependency and Hatchling as the build backend, **as used in
the reviewed S1a implementation** (`084154c`, identical on `main`).

| Item | As used |
|---|---|
| PyYAML | `pyproject.toml` `pyyaml>=6.0`, locked in `uv.lock` at **6.0.3** with registry hashes |
| Hatchling | `pyproject.toml` `[build-system] requires = ["hatchling>=1.25"]`, `build-backend = "hatchling.build"` |

- **Why it fits the approved scope:** PyYAML reads the YAML specs and registers that the approved
  factor-specification standard defines (review item 10). Hatchling is build-only.
- **This is an addition to the OD-0017 stack list** (Python 3.13, `uv`, `pytest`, `hypothesis`,
  `ruff`, DuckDB). That list is unchanged otherwise.
- **Recorded facts, not conditions:**
  - a build backend is not hash-locked by `uv.lock`, so Hatchling is constrained only by
    `>=1.25`;
  - the reviewer did not reproduce a fresh Hatchling build locally (review item 10).
- **Not covered:** any other dependency, or a future version change of these two beyond what the
  lock and the constraint allow. Those are ordinary stack changes needing their own decision.

### 2. Q-008: no CI egress firewall, accepted for S1a only

**Accepted for S1a only:** the documented absence of a CI-level egress firewall.

- **Basis, as the owner stated it:** S1a's synthetic-only scope; the current dependency
  restrictions; socket-blocked tests. The controls actually in place are:
  - `src/` may import no network client (`tools/check_repo.py`, OD-0017);
  - `tests/conftest.py` refuses every non-loopback socket connect;
  - CI declares minimum permissions and holds no secrets (`.github/workflows/ci.yml`);
  - the synthetic adapters read files only.
- **A known limitation, not proof of complete network isolation.** Static import rules and a
  Python test fixture are not a process-level or runner-level network control (review item 8).
  `uv sync --locked` reaches the package index.
- **Condition carried forward:** a **separate, explicit network and credential-control
  decision is required before S1b is authorised.** This acceptance does not extend to S1b, to
  any real source fetch, or to any credential.

### 3. Q-005a: exploratory internal research needs no individual owner event

**Confirmed:** exploratory research conducted internally within HIO does not require an
individual owner approval event.

- This is the current behaviour, and it matches the approved releases standard
  (`docs/standards/datasets-releases-and-artefacts.md` §5): the **producing job** sets
  `exploratory` once invariants pass. The S1a job does exactly that (`src/hio/jobs/s1a.py`).
- **Unchanged:** publication to `hio_internal` for consumer use still requires the owner's
  `approved_for_consumer(hio_internal)` event and every applicable rights check.
  - The rights standard's operation gates still apply to all internal work, exploratory or not:
    build, store derived, rebuild, and agent use (`docs/standards/rights-and-licensing.md` §3).
  - The consumer resolution path still runs the publish gate for the named class, on the
    release's own lineage, at every use (`src/hio/publish/status.py`, `resolve_for_use`).
- **Not decided here:** Q-005b (how several distribution-class approvals coexist and are
  withdrawn) and Q-006 (whether `superseded` and `deprecated` fail closed) stay open.

### 4. The capture-clock archive question: deferred to S1b design

**Deferred** to S1b design. The current fail-closed behaviour is **not** changed.

- **The question** (response 6, `reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-6.md`): a
  single archive receipt carrying a key's revision history gives several vintages at one
  `captured_at`, with equal strength. Under the approved ranking (Q-002 r5) that is a
  capture-clock conflict, so `as_captured_by_hio` reports the key absent (`suppresses_key`).
- **Current behaviour kept:** the key is suppressed, not resolved. It affects no S1a fixture or
  release.
- **Registered** in the open-decisions queue as **Q-010**, blocking S1b design.

## What this record does NOT do

- It does **not** accept S1a. S1-A16 (the §10 fresh-session test) is not run, and the owner's
  grading and the S1a acceptance record remain outstanding.
- It does **not** approve observations v0.3 (blob `61ddd58e`). That stays a separate decision,
  pending exact-revision confirmation.
- It does **not** authorise S1b, any real fetch, cloud storage or credential, or decide the S1b
  network and credential controls.
- It does **not** change, reinterpret or amend any approved standard, ADR, contract or the
  verified implementation, and it waives no finding.
- It does **not** decide Q-003, Q-004, Q-005b or Q-006.

## Corrections (append-only)

None.
