---
id: A01-INDEPENDENT-VERIFICATION-AND-READINESS-2026-10-18
title: A01 Independent Verification and Readiness Report
author: codex/reviewer
status: reviewer_opinion
date: 2026-10-18
review: REVIEW-2026-10-18-a01
verification: VERIFY-2026-10-18-a01-1
---

# A01 Independent Verification and Readiness Report

**For:** ChatGPT and the HIO owner. **Reviewer opinion at a fixed revision; no approval or
authorization is granted here.** The [original review](../records/REVIEW-2026-10-18-a01.md)
covered A01 architecture, return mathematics, S1 draft specs and the harness. This round was
assigned to verify its **eight findings**, not to validate an HIO implementation or vendor data.

## Revision evidence

| Revision | Exact SHA |
|---|---|
| Original A01 review base → reviewed head | `1502ab8804c5968a8bf91fa36275c44e6e84f575` → `35c9821f805955914b05991c1c075b8cb3e082b5` |
| Claude T-0008 fix → submission head | `0e3de4b76398799692cd09f3982c12986e195e7b` → `0c74686fa1de21fb2e7ac6ef361c716df67b35a9` |
| Codex [verification](../records/VERIFY-2026-10-18-a01-1.md) commit | `bb4aa7258f2da5951337aa62b0e469d74cefb89e` on `review/a01-verify-1-codex` |

## Findings disposition

Evidence below is from the corrected standards, specs and S1 tests at the submission head,
with the numeric examples independently recalculated. `verified_closed` is recorded on the
review branch; the staging index changes only when the owner receives that branch.

| Finding | Status | Independent evidence | Residual risk / later gate |
|---|---|---|---|
| F-1: revised backfill appears knowable | **verified_closed** | Observations v0.2 §3–4 and OBS-INV-007 exclude `schedule_only` from `as_known_by_market`; the 110 backfill is absent in 2021, while documented 100/110 publisher vintages resolve at their respective dates. | Source-specific archive date and integrity rules before using `archived_receipt`. |
| F-2: cash fixing look-ahead | **verified_closed** | RA §3.2 and USD cash v0.2.0 use Friday SOFR for a Friday–Monday accrual, exclude Monday's overnight, and label the result in arrears with later `knowable_at` (`S1-A7/A8`). | T-0002 must confirm publication instants, AUD rate regime and NY/Sydney alignment for live data. |
| F-3: release hash versus status | **verified_closed** | Releases v0.2 §2, §5–7 separate the deterministic manifest/envelope hash from run data and sequenced status events; S1-A11 requires rebuild and pinned-withdrawal fixtures. | S1 must choose and test canonical Parquet or CSV hashing. |
| F-4: CMT coupon omitted | **verified_closed** | RA §6 step 3 includes paid coupon cash: `(100+2)/102−1=0`; non-coupon `101.05/101−1=0.000495049505`. | S3 must implement the re-strike and cash-holding convention. |
| F-5: incomplete rights gates | **verified_closed** | Rights v0.2 §3 maps fetch, store, build, rebuild, publish and agent operations to permissions; S1-A12 requires fail-closed fixtures for each S1 operation. | T-0002 verifies actual grants before any live operation; S1 implements enforcement. |
| F-6: bill rates treated as returns | **verified_closed** | Cash specs and S1-A10 now compare rate levels and aligned horizons as `state_indicator` references; `0.042/(1−0.042×91/360)=0.042450684770`. | Reference availability and conventions remain subject to T-0002. |
| F-7: false cash bound | **verified_closed** | Exact block compounding replaces `<1e-8`; recalculated 3-day, 4-day and Thursday–Monday returns are `0.000358333333`, `0.000477777778`, `0.000486154907`. | S1 must execute these fixtures against code. |
| F-8: FX forward denominator | **verified_closed** | RA §4.2 and RA-INV-021 use equal initial capital; under CIP both cash and forward excess equal `(1+rʰ)(S_T/F−1)`, including the −10% versus −9.090909% example. | Market forward triangulation remains a later slice. |

## Architecture conformance and limits

The corrections preserve the **documented** HIO/SMSF boundary: HIO remains a separate system,
with no SMSF database, credential or accounting authority ([ADR-0002](../../docs/decisions/HIO-ADR-0002-systems-of-record-and-smsf-boundary.md),
[S1-A1](../../docs/implementation-plan.md)). They strengthen point-in-time vintage selection
(F-1), defined total and excess return mathematics (F-2, F-4, F-6–8), operation-level licensing
(F-5), and content identity plus withdrawal semantics (F-3). The fix and submission commits
change no file outside `hio/`. These are **verified design contracts and arithmetic**, not
evidence that future code, vendor terms, capture schedules, cloud storage or consumers comply.

## Readiness and owner action

**A01 G1 approval: READY WITH CONDITIONS.** No original finding remains open; no waiver is
needed. The owner must first receive and inspect the scope-checked review branch, decide
T-0008 acceptance separately, and make revision-specific decisions on the A01 charter, ADRs
0001–0010, standards and harness through T-0001/G1. They remain proposed in the repository.

**HIO-S1 authorization: NOT READY at this revision.** G1 has not occurred and T-0005 is only
proposed. After G1, the owner may separately authorize a **synthetic-fixture-only** S1 scope.
Live fetch, storage, build and publication must wait for T-0002 evidence of every required
source right and timing rule. The solution architect should specify the S1 hash rendering and
NY/Sydney cash alignment; the AUD rate regime follows verified publication timing. The owner
should confirm the ADR-0002 projection-field boundary before approving that interface. S1
acceptance tests, including rights denials, PIT vintages, reproducible rebuilds and cash/FX
identities, remain unrun until implementation.
