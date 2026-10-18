---
id: HIO-REVIEWS
title: Review index (records, findings, remediation claims, verification, waivers)
status: current
owner: independent reviewer (findings and verification); owner (waivers)
last_reviewed: 2026-10-18
---

# HIO review index

**The single place** to find what has been reviewed, at which revision, and what remains open.
The rules are in [operating model §3 and §6.1](../docs/harness/operating-model.md#61-review-index-and-provenance).

**Who writes what** (checked from `git log` `HIO-Actor` trailers; not technically enforced):
- **Codex (reviewer):** review rows, finding rows, and `verified_closed` or reopened outcomes.
- **Claude (author):** only the *Remediation claim* cell of a finding (commit + evidence path).
- **Owner:** the *Waiver* cell, by OD id.

## Reviewed revisions and review records

| Review | Subject | Base..head | Reviewer | Verdict | Record |
|---|---|---|---|---|---|
| — | **none yet.** No independent review of HIO has taken place. | — | — | — | — |

## Findings register

| Finding | From review | Severity | State | Remediation claim (author) | Verification (reviewer) | Waiver (owner OD) |
|---|---|---|---|---|---|---|
| — | — | — | **no findings recorded** | — | — | — |

States: `open`, `remediation_claimed` (still open), `verified_closed`, `waived`.

## Pending review requests

| Request | Target | Scope | Requested by | Status |
|---|---|---|---|---|
| A01 independent review | `docs/hio-a01-baseline`, `85ef0fa` → the T-0006 head (see the latest handoff) | the A01 baseline: ADRs 0001–0010, the standards (especially return accounting v0.1), and harness-0.2 (T-0006) | Claude (proposal) | **awaiting the owner's go-ahead** |
