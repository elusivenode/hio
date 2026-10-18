---
id: HIO-REVIEWS
title: Review index (assignments, records, findings, remediation claims, verification, waivers)
status: current
owner: independent reviewer (findings and verification); owner (assignments and waivers)
last_reviewed: 2026-10-18
---

# HIO review index

**The single place** to find what is assigned for review, what has been reviewed at which
revision, and what remains open. Rules: [operating model §3 and
§6.1](../docs/harness/operating-model.md#61-review-index-and-provenance).

**Who writes what:**
- **The owner:** *Assigned reviews*; waivers (by OD id).
- **The reviewer (Codex):** review rows, finding rows, verification outcomes.
- **The author (Claude):** only the *Remediation claim* cell of a finding.

Commits carry `HIO-Actor` role trailers as **self-declared metadata, not proof**. Reviewer
actions are evidenced by the reviewer's own output, committed verbatim and hashed (§6.1).

## Assigned reviews (owner-assigned; the only source of a review target)

| Review | Repository | Base SHA | Head SHA | Task / scope | Assigned by (OD / source) | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | **No review target has been assigned.** |

## Candidate review targets (NOT assigned; a reviewer must not treat these as its target)

| Candidate | Repository | Base SHA | Head SHA | Proposed scope | Proposed by |
|---|---|---|---|---|---|
| A01 independent review | `macsmsf`, branch `docs/hio-a01-baseline` | `1502ab8` (`macsmsf` main) | **the commit that adds the latest `hio/handoffs/*t0006-final-correction*` handoff**, resolved as `git log -n1 --format=%H -- <that file>`; the SHA is stated in the owner-facing completion report | ADRs 0001–0010; the standards (especially return accounting v0.1); the S1 draft specs; harness-0.3 (T-0006); the four `macsmsf` pointer edits in `85ef0fa` | Claude (candidate only) |

## Reviewed revisions and review records

| Review | Subject | Base..head | Reviewer | Verdict | Record |
|---|---|---|---|---|---|
| — | **none yet.** No independent review of HIO has taken place | — | — | — | — |

**Other reviewer inputs (not reviews; no findings opened):**
- A **Codex focused analysis** (`hio-harness-refinement-codex-analysis-for-chatgpt-2026-10-18.md`,
  of `23ad27f`) is cited by the owner's directive (OD-0002). It was not supplied to Claude and
  is not in the repository.
- The directive describes it as "not the independent A01 architecture, financial mathematics,
  or implementation review", granting no approval.
- If the owner wants it on record, commit it verbatim under `docs/history/`.

## Findings register

| Finding | From review | Severity | State | Remediation claim (author) | Verification (reviewer) | Waiver (owner OD) |
|---|---|---|---|---|---|---|
| — | — | — | **no findings recorded** | — | — | — |

States: `open`, `remediation_claimed` (still open), `verified_closed`, `waived`. A waiver
preserves the finding. It is not a verification.
