# HIO — Codex Independent Review Branch and Worktree Protocol

**Status:** Proposed harness amendment for owner adoption  
**Date:** 18 October 2026  
**Scope:** Agentic collaboration and review provenance; documentation and lightweight validation only  
**Audience:** Claude (harness maintainer), Codex (independent reviewer), HIO owner

## 1. Architectural decision recommended

Adopt a **short-lived, isolated Git worktree and review branch for every independent Codex review**. The branch starts at the exact assigned implementation head SHA. Codex writes review evidence only within `hio/reviews/`, not implementation code or other project documents. Review results are incorporated into the staging/integration branch after an explicit allowed-path check.

This protocol preserves reviewer independence and an auditable review trail. It does **not** itself authenticate the reviewer or constitute approval of the subject under review.

## 2. Roles and authority

- **Owner:** Assigns an exact review target, accepts review evidence into the repository, decides architecture acceptance, release authorisation and any waivers.
- **Claude:** Authors and implements approved work, submits evidence, responds to findings and produces remediation commits. Claude does not close or verify Codex findings.
- **Codex:** Independently inspects the fixed target, records findings and independently verifies remediation. Codex does not silently patch the work it reviews or authorise architectural decisions.
- **ChatGPT:** Advises the owner, challenges assumptions and drafts implementation/review directives. Advice is not authorisation unless the owner explicitly adopts it.

## 3. Assignment and fixed review target

Each assigned review must name:

| Field | Required content |
|---|---|
| Review ID | Stable unique ID, e.g. `REVIEW-2026-10-18-A01` |
| Target base | Exact full base commit SHA |
| Target head | Exact full head commit SHA |
| Scope | Files, work package, architectural and financial standards to review |
| Review branch | e.g. `review/a01-codex` |
| Reviewer | Codex, as declared role; authentication tracked separately |
| Evidence | Tests, inspected files, calculations and reproduced commands |
| Verdict | `READY`, `READY WITH CONDITIONS`, or `NOT READY` |
| Findings | Stable IDs, severity, evidence, and consequence |

The target head must not be silently rebased or force-pushed during review. If implementation changes after assignment, either a new review or a clearly scoped supplemental verification against a new head is required.

## 4. Worktree workflow

Illustrative commands (replace SHAs and branch names with assigned values):

```bash
# Create an isolated Codex checkout from the exact assigned head.
git worktree add ../macsmsf-review-a01 35c9821 -b review/a01-codex

# Codex conducts the independent review in that worktree and commits
# only permitted review records under hio/reviews/.

# Before incorporating review evidence, confirm that no other paths changed.
git diff --exit-code 35c9821 review/a01-codex -- . ':!hio/reviews'

# Also inspect changed paths and file types, rejecting disallowed paths,
# symlinks or unexpected files. Review commit provenance and content.
git diff --name-status 35c9821 review/a01-codex

# Once verified, integrate review evidence into the designated staging branch.
# Use --no-ff if that is the repository's approved merge convention.
```

A passed diff check establishes a **content-scope constraint**, not authenticated reviewer identity. Git worktrees isolate checkouts operationally but are **not security boundaries**. The hosting platform's authenticated reviews and branch protections should become the stronger control when available.

## 5. Review records and verification records

Codex should create an immutable submitted review record, for example:

`hio/reviews/records/REVIEW-2026-10-18-A01.md`

That record must capture base/head, scope, review outcome, stable finding IDs, evidence and relevant code or document references. **Do not rewrite original submitted findings** to make remediation appear as though the defect never existed.

For remediation, Claude records a response and the new implementation SHA. Codex then starts a fresh review worktree at the remediation head and adds a distinct verification record referencing the original finding IDs. Verification may confirm resolution or reject the remediation with reasons.

Suggested finding lifecycle:

1. `OPEN` — Codex submits finding.
2. `REMEDIATION_PROPOSED` — Claude records proposed fix.
3. `REMEDIATION_IMPLEMENTED` — Claude provides exact remediation commit and evidence.
4. `VERIFIED` or `REJECTED` — Codex independently checks the fix.
5. `WAIVED` — Owner explicitly accepts a remaining risk, with dated rationale and exact revision; no agent may self-waive.
6. `CLOSED` — Administrative state following independent verification or explicit owner waiver.

Owner acceptance of the overall work package remains distinct from finding verification.

## 6. Review index

The source of truth is the individual review and verification records. The index at `hio/reviews/README.md` is a navigation and status summary, not a competing authority.

**Preferred eventual approach:** generate or validate the index deterministically from structured record metadata, avoiding repeated concurrent edits to a shared index. **Near-term:** a lightweight manually maintained index is acceptable. Do not introduce a complex workflow engine or dedicated review application.

## 7. Meaning of a merge

Merging a Codex review branch means **the review evidence has been received into the repository**. It does **not** mean:

- Codex's conclusions have been accepted by the owner;
- defects have been corrected;
- an ADR has been approved;
- HIO-S1 or another implementation slice is authorised; or
- the reviewed work is accepted for production.

These require the distinct evidence and authorisation already defined in the HIO harness.

## 8. Long-term hosted-repository evolution

Once HIO has a standalone hosted repository, retain the independent review records while adding:

- Claude implementation pull requests with exact head commits;
- Codex reviews through an authenticated account on the fixed target;
- branch protection, required checks and review-scope validation;
- independently verifiable owner acceptance and waiver records.

Commit messages and `HIO-Actor` trailers are **declared-role hints**, never authentication or proof of approval.

## 9. Small harness amendment requested from Claude

If the owner adopts this proposal, make **minimal documentation-only changes** to:

- `hio/docs/harness/operating-model.md` §6.1: add isolated review worktree and branch procedure, reviewed base/head requirements, merging semantics, and path-boundary check;
- the review workflow portion of §2.2: require owner assignment of an exact review target before the independent session;
- `hio/reviews/README.md` (“Who writes what”): Codex authors review and verification records, Claude authors remediation responses, and the owner controls approval and waivers;
- `hio/AGENTS.md` only if a short bootstrap pointer is needed, not to duplicate the operating model.

Preserve all unapproved ADR and implementation statuses. Do not modify application code, financial calculation code, architecture choices, SMSF data, infrastructure or the HIO-S1 implementation plan except for an essential cross-reference. Do not perform a review merely by adding this procedure.

## 10. Acceptance criteria

The harness amendment is ready for independent evaluation only when:

1. A fresh Codex session can determine whether a review is **assigned**; if unassigned, it correctly reports **no fixed review target**.
2. If assigned, the session identifies the exact target base/head, scope, reviewer role and pending findings from repository records alone.
3. Codex operates from a separate worktree and produces a review-only commit with no changes outside the permitted review artefact paths.
4. A scripted or explicitly repeatable check fails when a non-review path or unexpected file type appears in a review branch.
5. A review merge is documented as *receipt*, not technical or owner approval.
6. Original findings remain immutable; later Claude responses and Codex verifications preserve stable IDs and explicit remediation SHAs.
7. Owner waivers and work-package approvals remain explicit, authenticated as practicable and tied to exact revisions.
8. There are no new mandatory heavyweight session rituals or duplicate sources of authoritative decisions.

## 11. Recommended next step

Adopt this as a narrow proposed harness amendment, have Claude update the designated documentation on the staging branch, and then assign Codex's **independent A01 architecture and financial-mathematics review** against a fixed head SHA using a fresh worktree. Do not mistake adopting the workflow for approving A01, HIO-ADR-0008 or HIO-S1.
