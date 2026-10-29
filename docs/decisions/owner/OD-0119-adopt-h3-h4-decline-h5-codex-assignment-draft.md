---
id: OD-0119
title: "Owner adopts the S1b-1 H3/H4 decision pack as recommended (controls C-1 to C-9, storage S-1 to S-10), declines the Q-010 ingest check for S1b-1 (H5 closed; Q-010 open), and authorises drafting a Codex review assignment for T-0010 and T-0011; nothing provisioned"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-h3-h4-h5-codex.md (owner's messages AP and AQ, verbatim, with Claude's decisions put)
  sha256: 4985e84c23dba7811992d1393e8ad1aa7af523db6b8fa58fd94ddab9a535e9fa
  date: 2026-10-29
  quote: "yes to all 3"
applies_to:
  - path: docs/evidence/S1B1-H3-H4-decision-pack.md
    revision: "main at 5315f2d"
related: {adrs: [HIO-ADR-0012], tasks: [T-0009, T-0010, T-0011], findings: [], ods: [OD-0038, OD-0115, OD-0117, OD-0118]}
---

# OD-0119: H3 and H4 adopted; H5 declined; Codex assignment to be drafted

## 1. H3 and H4 (T-0009 §8)

The pack at `main` `5315f2d` is adopted **as recommended**:
- **H3 (the OD-0038 successor):** C-1 to C-9. Includes **no runner egress firewall as an accepted residual** (C-2,
  the S1b successor to Q-008), owner-run OpenTofu with no CI apply (C-6), and removing the `capture` Environment's
  required-reviewer rule **at go-live** (C-4; that GitHub change is authorised by this yes, to be made when
  Authorisation B is given).
- **H4:** S-1 to S-10: Azure Blob in `australiaeast`, `hnf-prod`, `rg-hio-evidence`; ZRS; account-level
  version-level WORM **Unlocked**, 3,650 days (locking is a later decision); network Allow with Entra-only auth;
  soft delete 30 days; budget 20 a month; Log Analytics 90 days. S-6 (the provider validation probe, including C5's
  whole-second timing) and S-10 (resource provider registration) are **settings of the plan, executed only under
  Authorisation B**. S-7 (second copy) is deferred to within the first month of capture.

**H3 and H4 are decided.** Nothing is provisioned.

## 2. H5 declined

No additive multi-vintage ingest check is built for S1b-1. Same-instant equal-strength vintages stay suppressed by
`as_captured_by_hio` (fail closed). **H5 is closed for this slice; Q-010 stays open** for genuine archive ingestion.

## 3. Codex review

Claude drafts one assignment covering T-0010 (at the `feat/t0010` tip once W-3 and W-5 land) and T-0011 (at PR #8's
head), and puts the exact heads to the owner for a one-line approval. **Nothing is assigned by this OD.**

## Remaining before live capture

T-0010 W-3 (workflow and CLI wiring) and W-5 (2027 calendars); the Codex review and owner acceptance of T-0010 and
T-0011; **Authorisation B**, naming the apply steps (bootstrap, provider registration, evidence store, identities,
alerting, the C-4 GitHub change, the S-6 probe, then capture).

## Not authorised

Any Azure write; `tofu plan` or `apply`; Authorisation B; any Codex launch.

## Corrections (append-only)
