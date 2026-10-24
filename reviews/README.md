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
- **The owner:** assignments (an *Assigned reviews* row, an owner PR comment, or a direct
  instruction later indexed here; exact SHAs and the review branch); runs or reviews the scope
  check; merges reviewer PRs (receipt only); acceptance, approval and waivers (by OD id).
- **The reviewer (Codex):** review records and verification records (`records/`), its
  handoffs (`handoffs/`), opinion or readiness reports (`reports/`), and its own index rows. Written on its review branch, in its own
  worktree, never on the staging branch.
- **The author (Claude):** remediation responses (`responses/`) and the *Remediation claim*
  cell. Never a verdict, a verification or a closure.

Commits carry `HIO-Actor` role trailers as **self-declared metadata, not proof**. Reviewer
actions are evidenced by the reviewer's own output on a scope-checked review branch (§6.1–6.2).

## Assigned reviews (owner-assigned; harness-0.7: one of three owner-authored sources, see operating model §6.2 step 1)

| Review | Repository | Base SHA | Head SHA | Task / scope | Assigned by (OD / source) | Status |
|---|---|---|---|---|---|---|
| REVIEW-2026-10-18-t0004 | `macsmsf`, branch `docs/hio-001-boundary-c1` | `1502ab8804c5968a8bf91fa36275c44e6e84f575` (`main`) | `fe3fdc78cb2d2b9f147122528cc5cf97db976397` | T-0004: the documentation-only ADR 0003 C1 boundary amendment and the HIO-001 review-record pointer. Check it is consistent with HIO-ADR-0003 (approved, OD-0008) and changes no code, schema or activation prerequisite. Review branch `review/t0004-codex`, cut from the staging commit that adds OD-0010; the target is inspected read-only (cross-lineage mechanics in OD-0010) | [OD-0010](../docs/decisions/owner/OD-0010-g1-followup-instructions.md) (owner instruction, transcribed); cross-lineage mechanics **confirmed** by [OD-0018](../docs/decisions/owner/OD-0018-t0004-mechanics-parallel-work.md). The repository and SHAs are `macsmsf`'s; the review branch is in `macsmsf` | **assigned** |
| REVIEW-2026-10-24-s1a-1 | `elusivenode/hio` | `9370256bac6ba2193b09c342170bd11ca57b70a3` | `98e6a8e08fca8b28241d9e4e7c04c181d75f1eef` | T-0005 S1a synthetic-fixture implementation (HIO-ADR-0010 rev 3, OD-0017, OD-0020). Review branch `review/s1a-1-codex` | owner direct assignment in Codex chat, 2026-10-24; indexed at receipt and the five values confirmed by the owner ([OD-0022](../docs/decisions/owner/OD-0022-receive-s1a-review.md)) | **received** at `e55cc89` (PR #1); verdict REQUEST CHANGES; findings open |

## Candidate review targets (NOT assigned; a reviewer must not treat these as its target)

| Candidate | Repository | Base SHA | Head SHA | Proposed scope | Proposed by |
|---|---|---|---|---|---|
| A01 independent review | `macsmsf`, branch `docs/hio-a01-baseline` | `1502ab8` (`macsmsf` main) | **the commit that adds the latest `hio/handoffs/*t0006-final-correction*` handoff**, resolved as `git log -n1 --format=%H -- <that file>`; the SHA is stated in the owner-facing completion report | ADRs 0001–0010; the standards (especially return accounting v0.1); the S1 draft specs; harness-0.3 (T-0006); the four `macsmsf` pointer edits in `85ef0fa` | Claude (candidate only) |
| S1a implementation review (**assigned directly; see Assigned reviews**) | `elusivenode/hio` | `9370256bac6ba2193b09c342170bd11ca57b70a3` (the revision OD-0020 reviewed) | **the commit that adds `docs/evidence/S1A-evidence-package.md`**, resolved as `git log -n1 --format=%H -- docs/evidence/S1A-evidence-package.md` | S1a under HIO-ADR-0010 rev 3 and OD-0017/OD-0020: the acceptance list, the RA §3.2 and FX fixtures, OBS-INV-001…007, the rights gate, releases §6.1, the safeguards, and the ten interpretations listed in the evidence package | Claude (candidate only) |

Historical candidate: the owner subsequently assigned the A01 review directly at the fixed
head `35c9821`. The completed review is indexed below; this candidate is not a pending task.

## Reviewed revisions and review records

| Review | Subject | Base..head | Reviewer | Verdict | Record |
|---|---|---|---|---|---|
| REVIEW-2026-10-18-a01 | A01 architecture, mathematics, S1 specs and harness-0.3 | `1502ab8..35c9821` | Codex, on the owner's direct 2026-10-18 request | **REQUEST CHANGES** | [record](records/REVIEW-2026-10-18-a01.md) |
| REVIEW-2026-10-18-t0007-pilot | T-0007 review-worktree protocol and harness-0.5 corrections | `46ea6a5..b48f83c` | Codex, on the owner's direct 2026-10-18 assignment | **READY** | [record](records/REVIEW-2026-10-18-t0007-pilot.md) |
| REVIEW-2026-10-24-s1a-1 | T-0005 S1a synthetic-fixture implementation | `9370256..98e6a8e` | Codex, on the owner's direct 2026-10-24 assignment | **REQUEST CHANGES** | [record](records/REVIEW-2026-10-24-s1a-1.md) |

Reviewer build-check addendum for `REVIEW-2026-10-24-s1a-1`:
[locked offline sync and repeated tests](reports/2026-10-24-s1a-1-build-addendum.md).

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
| F-REVIEW-2026-10-24-s1a-1-1 | REVIEW-2026-10-24-s1a-1 | high | **open** | remediation_claimed: fix `39d37da`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | — | — |
| F-REVIEW-2026-10-24-s1a-1-2 | REVIEW-2026-10-24-s1a-1 | high | **open** | remediation_claimed: fix `6bbf562`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | — | — |
| F-REVIEW-2026-10-24-s1a-1-3 | REVIEW-2026-10-24-s1a-1 | high | **open** | remediation_claimed: fix `3185443`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | — | — |
| F-REVIEW-2026-10-24-s1a-1-4 | REVIEW-2026-10-24-s1a-1 | high | **open** | none claimed: policy question Q-001 (draft in [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md)) | — | — |
| F-REVIEW-2026-10-24-s1a-1-5 | REVIEW-2026-10-24-s1a-1 | medium | **open** | remediation_claimed: fix `7076452`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | — | — |
| F-REVIEW-2026-10-24-s1a-1-6 | REVIEW-2026-10-24-s1a-1 | medium | **open** | remediation_claimed (round 5): fix `7cf2c01`; [response 5](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-5.md) (OD-0025). Earlier rounds rejected, records preserved and owner-disposed, not received: round 4 (fix `5fbbd09`, [response 4](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-4.md)) by VERIFY-2026-10-24-s1a-1-4 at `873fc69`; round 3 (fix `c964461`, [response 3](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-3.md)) by VERIFY-2026-10-24-s1a-1-3 at `ff0dd81`; round 1 (fix `1c117e6`, [response 1](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md)) by VERIFY-2026-10-24-s1a-1-1 at `0255cb2`; round 2 (fix `45dd538`, [response 2](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-2.md)) by VERIFY-2026-10-24-s1a-1-2 at `9a94c3a` | — | — |
| F-REVIEW-2026-10-24-s1a-1-7 | REVIEW-2026-10-24-s1a-1 | medium | **open** | none claimed: policy question Q-002 (draft in [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md)) | — | — |

States: `open`, `remediation_claimed` (still open), `verified_closed`, `waived`. A waiver
preserves the finding. It is not a verification.
