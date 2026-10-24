---
id: HIO-OD-INDEX
title: Owner decision records
status: current
owner: owner
last_reviewed: 2026-10-24
---

# Owner decision records (OD)

These records evidence explicit owner actions: instruct (authorise work), accept, approve and
waive. The authority is the **owner's statement**, which each record cites verbatim. The rules
are in operating model §1.1; the template is
[`../../../templates/owner-decision.md`](../../../templates/owner-decision.md).

| ID | Decision | What | Applies to | Record status |
|---|---|---|---|---|
| [OD-0001](OD-0001-authorise-harness-refinement.md) | authorise_work | T-0006 harness refinement (the original ambiguity is preserved) | `hio/` from `85ef0fa` | corrected |
| [OD-0002](OD-0002-authorise-t0006-final-correction.md) | authorise_work | T-0006 final harness correction | `hio/` from `23ad27f` | recorded |
| [OD-0003](OD-0003-adopt-review-worktree-protocol.md) | authorise_work | T-0007 review branch and worktree protocol | `hio/` from `bada952` | recorded |
| [OD-0004](OD-0004-accept-t0007.md) | accept_work | T-0007 accepted | T-0007 at `b48f83c` | recorded |
| [OD-0005](OD-0005-authorise-a01-correction-slice.md) | authorise_work | T-0008 A01 correction slice | `hio/` from `e99fae1` | recorded |
| [OD-0006](OD-0006-accept-t0008.md) | accept_work | T-0008 accepted | T-0008 at `0c74686` | recorded |
| [OD-0007](OD-0007-accept-t0006.md) | accept_work | T-0006 accepted as completed work | T-0006 at `35c9821` | recorded |
| [OD-0008](OD-0008-g1-decisions-a82aa0d.md) | approve | G1: items 1–11 and 13–20 approved (C1 chosen; projection fund-level); item 12 (ADR-0010) returned | each file at `a82aa0d` | recorded |
| [OD-0009](OD-0009-g1-follow-on-instructions.md) | authorise_work | §6.2 `reports/` path; T-0002 and T-0003 authorised; prepare T-0004; S1a limits | `hio/` from `f7a9ec9` | recorded |
| [OD-0010](OD-0010-g1-followup-instructions.md) | authorise_work | ADR-0010 S1a gate corrected; harness-0.6 presented for approval; begin T-0002/T-0003; T-0004 review assigned | `hio/` from `f2275e2` | recorded |
| [OD-0011](OD-0011-approve-adr-0010-rev3.md) | approve | HIO-ADR-0010 rev 3; **G1 complete**; S1a not authorised | ADR-0010 at `760f73e` (blob `8ade1962cf28`) | recorded |
| [OD-0012](OD-0012-approve-harness-0.6.md) | approve | harness-0.6, including the `reviews/reports/` rule | operating model at `f2275e2` (blob `e3114bd188ad`) | recorded |
| [OD-0013](OD-0013-t0002-hold-t0003-drafts.md) | authorise_work | keep T-0002 permissions unverified and blocked; draft (do not send) vendor questions | `hio/` from `8e11581` | recorded |
| [OD-0014](OD-0014-fix-stale-lines.md) | authorise_work | fix the stale lines (STATUS authority row; T-0002/T-0003 front matter; T-0007 line 60 as a later edit) | `hio/` from `4a994d3` | recorded |
| [OD-0015](OD-0015-fix-further-stale-lines.md) | authorise_work | fix the further stale lines in the accepted T-0006 and T-0007 cards (later edits); commit the OD-0014 work | `hio/` from `73512cf` | recorded |
| [OD-0016](OD-0016-s1a-preparation.md) | authorise_work | adopt the S1a-preparation advice: align roadmap, plan, T-0005, §8.1 and README to ADR-0010 rev 3; draft (not grant) S1a; push the staging branch | `hio/` from `81793f7` | recorded |
| [OD-0017](OD-0017-authorise-s1a.md) | authorise_work | **S1a authorised** (synthetic-fixture-only); create `elusivenode/hio` and migrate the verified history; stack and CI set | `macsmsf@dc4fd02` (`hio/`) | recorded (draft of the same id superseded) |
| [OD-0018](OD-0018-t0004-mechanics-parallel-work.md) | authorise_work | T-0004 review mechanics confirmed (no merge); T-0002/T-0003 continue; propose an SMSF-owned ETF diagnostic card; correct roadmap dates and gates | roadmap at `e32d282` | recorded |
| [OD-0019](OD-0019-repository-public.md) | authorise_work | make `elusivenode/hio` **public** (amends OD-0017's "private"), so ChatGPT can review | repository at `f10ad70` | recorded |
| [OD-0020](OD-0020-s1a-proceed-implementation.md) | authorise_work | proceed with S1a implementation under OD-0017, with five implementation considerations | repository at `9370256` | recorded |
| [OD-0021](OD-0021-approve-harness-0.7.md) | approve | harness-0.7 rev 3 approved (12 blobs); integration into `main` authorised; adoption condition on the CI gate | `9b58811` | recorded |
| [OD-0022](OD-0022-receive-s1a-review.md) | authorise_work | receipt of REVIEW-2026-10-24-s1a-1 (PR #1) at `e55cc89`; assignment confirmed and indexed; harness-0.7 adoption condition met | `e55cc89` | recorded |
| [OD-0023](OD-0023-authorise-s1a-remediation.md) | authorise_work | S1a remediation of findings 1, 2, 3, 5, 6; draft Q-001/Q-002 amendments | `6fe35cf` | recorded |
| [OD-0024](OD-0024-f6-remediation-before-receipt.md) | authorise_work | F6 remediation on PR #2 under the remediation-before-receipt exception (VERIFY-2026-10-24-s1a-1-1 at `0255cb2`, sha256 checked); harness-0.8 stopped | `18c80f2` | recorded |
| [OD-0025](OD-0025-f6-round3-disposition.md) | authorise_work | VERIFY-2026-10-24-s1a-1-1 and -2 disposed as preserved evidence (not received); F6 correction cycle on PR #2; hash transcription corrected by the owner | `759ddf7` | recorded |
| [OD-0026](OD-0026-q001-q002-drafting.md) | authorise_work | refine the Q-001/Q-002 draft amendments (drafting only; Option A advised, not adopted); F6 verification (VERIFY-2026-10-24-s1a-1-5, READY) acknowledged | `d9fa276` | recorded |
| [OD-0027](OD-0027-q001-q002-final-draft-amendment.md) | authorise_work | final narrow amendment of the Q-001/Q-002 drafts (revision 3: admissibility, distinguishability, conflict identity, diagnostics); refined Option A supported, not approved | `baa8e4e` | recorded |
| [OD-0028](OD-0028-q001-q002-revision4.md) | authorise_work | drafts revision 4: Q-001 header fix; Q-002 processing order vs acquisition history; architectural direction approved, exact text not yet | `6f013a7` | recorded |
| [OD-0029](OD-0029-approve-q001-select-q002-a-prime.md) | approve | **OBS-AMEND-Q001 revision 4 approved** (blob `419992f2`) as the governing two-cutoff contract; Q-002 Option A′ selected as direction (not approved); reproducibility and completeness required | `4e57fa1` | recorded |
| [OD-0030](OD-0030-approve-q002-authorise-f4-f7.md) | approve | **OBS-AMEND-Q002 revision 5 approved** (blob `d0a25b3b`); bounded F4/F7 implementation authorised on PR #2; observations v0.3 to be prepared for separate approval | `b4c398d` | recorded |
| [OD-0031](OD-0031-f4-f7-verify-6-exception.md) | authorise_work | remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-6 (`3cb3dd0`, sha256 `87ff2b82…`, checked); F4/F7 correction on PR #2 | `191ac0f` | recorded |
| [OD-0032](OD-0032-f7-verify-7-exception.md) | authorise_work | remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-7 (`35526b5`, sha256 `5cfc9bc3…`, checked); F7 correction on PR #2 | `f00db8c` | recorded |

**Current position:**
- **Approved:**
  - charter, architecture, HIO-ADR-0001…0009, six standards and `AGENTS.md`, at `a82aa0d`
    (OD-0008);
  - HIO-ADR-0010 rev 3 at `760f73e` (OD-0011);
  - the operating model, harness-0.6, at `f2275e2` (OD-0012).
- **G1 is complete.**
- **Not approved:** the factor specs (drafts); the roadmap and plan (recommendations).
- **Authorised:** S1a (OD-0017), not accepted.
- **Not authorised:** S1b.
- **Accepted:** T-0006, T-0007 and T-0008.
- **No finding is waived.**
