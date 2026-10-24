---
id: T-0005
title: "HIO-S1 walking skeleton in two stages: S1a synthetic-fixture foundation (independent repository, contracts, cash legs and investable FX excess return on fixtures); S1b live official observations"
status: submitted_for_review   # S1a only: integrated and evidence received (OD-0037), NOT accepted; S1b not authorised
owner: owner
assignee_role: implementation engineer (+ quantitative researcher for specs; independent reviewer)
created: 2026-10-18
authorised_by: OD-0017   # S1a only
base_revision: e32d282ee4c6f8195096c0aa62c25c0a59cf334f   # = macsmsf@dc4fd02 (migration source)
links:
  adrs: [HIO-ADR-0001, HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0007, HIO-ADR-0008, HIO-ADR-0009, HIO-ADR-0010]
  specs: [cash.aud.overnight@0.2.0, cash.usd.overnight@0.2.0, fx.usd_cash_vs_aud.excess@0.2.0]
  depends_on: {S1a: [G1 (complete, OD-0011), S1a owner authorisation], S1b: [S1a accepted, T-0002, S1b owner authorisation]}
  blocks: [S2]
---

# T-0005: the HIO-S1 walking skeleton

The full definition is in [`../../docs/implementation-plan.md#hio-s1-walking-skeleton-recommended`](../../docs/implementation-plan.md#hio-s1-walking-skeleton-recommended).
This card does not repeat it. The acceptance tests are S1-A1 to S1-A16 there, split by stage in
the plan's *Stage mapping*.

## Stages (HIO-ADR-0010 rev 3)

| Stage | Scope | Entry gate |
|---|---|---|
| **S1a** | synthetic sources and fixtures only: repository and history-preserving migration (operating model §8.1), CI, contracts, local-filesystem object store, observation/vintage/knowability model, the three S1 constructions, rights and publication gates on fixtures. **No network fetch, real data, credentials, buckets or schedules** | G1 (complete) and a separate owner authorisation of S1a's scope. **T-0002 does not gate S1a** |
| **S1b** | real-source adapters, bucket and scoped keys, scheduled capture, soak, triangulations | S1a accepted; T-0002 `owner_verified` rights per operation; timing, calendars and the AUD rate regime evidenced; a separate S1b authorisation |

**S1a is authorised** by [OD-0017](../../docs/decisions/owner/OD-0017-authorise-s1a.md) (owner, 2026-10-24),
including its stack, CI and migration settings. S1b is not authorised.

## Non-goals
Listed in the implementation plan, under S1 exclusions.

## Review status
**2026-10-25 (OD-0037):** PR #2 integrated at reviewed head `084154c` (`773a557`); VERIFY-2026-10-24-s1a-1-1…-11 received; F1–F7 verified closed at their reviewed heads. **Not accepted**: S1-A16 (§10) and its owner grading outstanding ([readiness](../../docs/evidence/S1A-acceptance-readiness.md)).
**2026-10-25 (OD-0038):** Q-007 ratified; Q-008 accepted for S1a only (S1b needs a network and credential-control decision); Q-005a confirmed; the capture-clock archive question deferred to S1b design (Q-010). Not acceptance.
**2026-10-25 (OD-0039):** S1-A16 run 1 at `3fd129e` recorded ([HARNESS-2026-10-25-s1a16-1](../../reviews/records/HARNESS-2026-10-25-s1a16-1.md)); **pending**: a Codex-only retest after the T-0004 baseline is resolved.
**2026-10-25 (OD-0041):** run 2 (Codex) at `df3af48` graded PASS; **S1-A16 satisfied** on the two-revision basis (OD-0040). All S1a acceptance evidence is complete ([acceptance package](../../docs/evidence/S1A-acceptance-package.md)); **not accepted**.

S1a reviewed (REVIEW-2026-10-24-s1a-1, REQUEST CHANGES, received `e55cc89`); remediation of findings 1, 2, 3, 5, 6 submitted on `remediation/s1a-1` (OD-0023); VERIFY-2026-10-24-s1a-1-1 (`0255cb2`, not received) verified 1, 2, 3, 5 closed and rejected 6; F6 round 2 submitted (OD-0024) and rejected by VERIFY-2026-10-24-s1a-1-2 (`9a94c3a`, not received); F6 round 3 submitted (OD-0025) and rejected by VERIFY-2026-10-24-s1a-1-3 (`ff0dd81`, not received); F6 round 4 submitted (OD-0025) and rejected by VERIFY-2026-10-24-s1a-1-4 (`873fc69`, not received); F6 round 5 verified closed by VERIFY-2026-10-24-s1a-1-5 (`6d8b60d`, READY, not received); Q-001/Q-002 approved (OD-0029/OD-0030) and F4/F7 implemented on the same branch (response 6), round 1 rejected by VERIFY-2026-10-24-s1a-1-6 (`3cb3dd0`, not received; OD-0031), round 2 submitted (response 7) and rejected for F7 by VERIFY-2026-10-24-s1a-1-7 (`35526b5`, not received; OD-0032), F7 round 3 submitted (response 8) and rejected by VERIFY-2026-10-24-s1a-1-8 (`db1722c`, not received; OD-0033), F7 round 4 submitted (response 9), contract gap found by VERIFY-2026-10-24-s1a-1-9 (`63df7ff`, not received), Q-002-R1 approved (OD-0035) and implemented (response 10), rejected by VERIFY-2026-10-24-s1a-1-10 (`586b35e`, not received; OD-0036), F7 round 6 submitted (response 11); findings 4 and 7 awaiting Q-001/Q-002. Originally implemented and **submitted for review** (2026-10-24): evidence in
[`docs/evidence/S1A-evidence-package.md`](../../docs/evidence/S1A-evidence-package.md), at the
commit that adds it. **Not accepted.** The Codex review needs the owner's assignment; the §10
fresh-session test has not been run. S1b: not authorised; do not start.
