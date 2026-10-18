---
id: HIO-REVIEWS
title: Review index (assignments, records, findings, remediation claims, verification, waivers)
status: current
owner: independent reviewer (findings and verification); owner (assignments and waivers)
last_reviewed: 2026-10-18
---

# HIO review index

A **navigation summary**: what is assigned, what has been reviewed at which revision, and what
remains open. **The individual records are the source of truth.** If this index disagrees with a
record, the record wins. Rules: [operating model §3, §6.1 and
§6.2](../docs/harness/operating-model.md#62-review-branch-and-worktree-protocol).

**Who writes what:**
- **The owner:** *Assigned reviews* (exact SHAs and the review branch); runs the scope check;
  merges reviewer branches (receipt only); acceptance, approval and waivers (by OD id).
- **The reviewer (Codex):** review records and verification records (`records/`), its
  handoffs (`handoffs/`), opinion or readiness reports (`reports/`), and its own index rows. Written on its review branch, in its own
  worktree, never on the staging branch.
- **The author (Claude):** remediation responses (`responses/`) and the *Remediation claim*
  cell. Never a verdict, a verification or a closure.

Commits carry `HIO-Actor` role trailers as **self-declared metadata, not proof**. Reviewer
actions are evidenced by the reviewer's own output on a scope-checked review branch (§6.1–6.2).

## Assigned reviews (owner-assigned; the only source of a review target)

| Review | Repository | Base SHA | Head SHA | Task / scope | Assigned by (OD / source) | Status |
|---|---|---|---|---|---|---|
| REVIEW-2026-10-18-t0004 | `macsmsf`, branch `docs/hio-001-boundary-c1` | `1502ab8804c5968a8bf91fa36275c44e6e84f575` (`main`) | `fe3fdc78cb2d2b9f147122528cc5cf97db976397` | T-0004: the documentation-only ADR 0003 C1 boundary amendment and the HIO-001 review-record pointer. Check it is consistent with HIO-ADR-0003 (approved, OD-0008) and changes no code, schema or activation prerequisite. Review branch `review/t0004-codex`, cut from the staging commit that adds OD-0010; the target is inspected read-only (cross-lineage mechanics in OD-0010) | [OD-0010](../docs/decisions/owner/OD-0010-g1-followup-instructions.md) (owner instruction, transcribed) | **assigned** |

## Candidate review targets (NOT assigned; a reviewer must not treat these as its target)

| Candidate | Repository | Base SHA | Head SHA | Proposed scope | Proposed by |
|---|---|---|---|---|---|
| A01 independent review | `macsmsf`, branch `docs/hio-a01-baseline` | `1502ab8` (`macsmsf` main) | **the commit that adds the latest `hio/handoffs/*t0006-final-correction*` handoff**, resolved as `git log -n1 --format=%H -- <that file>`; the SHA is stated in the owner-facing completion report | ADRs 0001–0010; the standards (especially return accounting v0.1); the S1 draft specs; harness-0.3 (T-0006); the four `macsmsf` pointer edits in `85ef0fa` | Claude (candidate only) |

Historical candidate: the owner subsequently assigned the A01 review directly at the fixed
head `35c9821`. The completed review is indexed below; this candidate is not a pending task.

## Reviewed revisions and review records

| Review | Subject | Base..head | Reviewer | Verdict | Record |
|---|---|---|---|---|---|
| REVIEW-2026-10-18-a01 | A01 architecture, mathematics, S1 specs and harness-0.3 | `1502ab8..35c9821` | Codex, on the owner's direct 2026-10-18 request | **REQUEST CHANGES** | [record](records/REVIEW-2026-10-18-a01.md) |
| REVIEW-2026-10-18-t0007-pilot | T-0007 review-worktree protocol and harness-0.5 corrections | `46ea6a5..b48f83c` | Codex, on the owner's direct 2026-10-18 assignment | **READY** | [record](records/REVIEW-2026-10-18-t0007-pilot.md) |

## Verification rounds

| Verification | Original review | Base..submission head | Fix commit | Reviewer outcome | Record |
|---|---|---|---|---|---|
| VERIFY-2026-10-18-a01-1 | REVIEW-2026-10-18-a01, findings 1–8 | `35c9821..0c74686` | `0e3de4b` | **Eight verified_closed** | [record](records/VERIFY-2026-10-18-a01-1.md) |

The owner assigned the A01 review directly in the Codex session. The *Assigned reviews* table
above was not updated beforehand; it is not evidence that the candidate row authorised the
review. The reviewed base/head and assignment source are in that record. The review record does
not accept or approve the A01 baseline.

The owner also assigned T0007-PILOT directly in the Codex session at the fixed base/head in its
record. Its READY opinion is not acceptance of T-0007 or approval of HIO-ADR-0008.

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
| F-REVIEW-2026-10-18-a01-1 | REVIEW-2026-10-18-a01 | critical | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-2 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-3 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-4 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-5 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-6 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-7 | REVIEW-2026-10-18-a01 | medium | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-8 | REVIEW-2026-10-18-a01 | medium | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |

States: `open`, `remediation_claimed` (still open), `verified_closed`, `waived`. A waiver
preserves the finding. It is not a verification.
