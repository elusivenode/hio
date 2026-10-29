---
id: OD-0128
title: "Owner accepts T-0012 (B-2 storage probe build) at efb6fa1 and authorises its merge into main by PR; owner authorises a read-only assembly of the solution architect's performance-review material; nothing created, applied or dispatched"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-accept-t0012.md (owner's messages 1 and 2, verbatim, with Claude's decisions and clarifying question put)
  sha256: 2d78fcbc08da3d0474e45b751ae6dadcaf83fd54692f617d7200fe80f961cf9a
  date: 2026-10-29
  quote: "yes; then, selected: Both 1 and 3"
applies_to:
  - path: feat/t0012
    revision: efb6fa115ede33869f1e21c4ee6030ba35b92e28
related: {adrs: [HIO-ADR-0012], tasks: [T-0012], findings: [], ods: [OD-0089, OD-0119, OD-0125, OD-0127]}
---

# OD-0128: T-0012 accepted; architect review material

The owner's first "yes" answered two questions at once, so Claude asked which was meant; the owner selected "Both 1 and
3" (transcript).

## 1. Acceptance of T-0012

**T-0012 is accepted at `efb6fa115ede33869f1e21c4ee6030ba35b92e28`** on the owner's own judgement, without a Codex
review. `feat/t0012` is then merged into `main` by pull request, so that the dispatch-only probe workflow exists on the
default branch. The T-0012 card is set to accepted after the merge. Limits: everything T-0012 measures is unverified
until B-2 runs; no C5 tolerance is decided.

## 2. Architect performance-review material

A read-only assembly of the solution architect's genuine consultations (`ask`, `assess`) across hiomux runs: the
consultation logs and the summaries given to the owner, for the review that OD-0089 makes due after the fifth. Nothing
is consulted, tuned or changed; the held-out cases are not touched.

## Not authorised

B-2 itself: creating the probe account or any Azure resource, any `tofu plan` or `apply`, any dispatch of the probe or
capture workflow; any write to the evidence store; B-3; `LIVE_AUTHORISATION`; any C5 tolerance; any change to the
architect's identity, manifest or cases.

## Corrections (append-only)

### Correction 1 (2026-10-29): T-0012 merged; review material assembled

**Decision 1 effective:** this record merged as `edb2168` (PR #32); `feat/t0012` merged at head `efb6fa1` (head match
enforced) as `01edfe9` (PR #33); `infra/`, `tools/`, `tests/` and `.github/` on `main` are identical to `efb6fa1`. The
T-0012 card is set to accepted in this commit. Nothing was created, applied or dispatched.

**Decision 2 done:** the review material was assembled read-only from the four hiomux runs' consultation logs and answers,
and the records that cite them, and given to the owner. It is operational material outside the repository, not a
record. Six `ask` consultations; whether the identity check `20261028T180220-ask-1a5f` counts as genuine is for the
owner (five or six). The review itself, and any outcome, is a separate owner action.
