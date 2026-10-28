---
id: OD-0079
title: "Owner acceptance: T-0009 S1b-1.0 (synthetic-fixture development under Authorisation A) accepted at 846974b and PR #6 merged into main as 7eba3f9; no live operation, right or finality accepted or authorised"
decision: accept_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-accept-t0009.md (typed by the owner, verbatim)
  sha256: fe9cb22e8d5d268dca2a67270a0e2a342c38d33179b50651cc7b9c4ee35d18d3
  date: 2026-10-28
  quote: "accept T-0009 and merge PR #6"
applies_to:
  - path: src/, tests/, tools/, specs/, infra/, registers/sources.yaml, pyproject.toml, uv.lock
    revision: 846974b2c43e5b9839809af0f1ebc08cee4e88b1   # the accepted head; all seven findings verified_closed there
  - path: /
    revision: 7eba3f9fe50d69a7030759ec15e4eb02f8d1c85f   # the integration of PR #6 into main; those paths equal 846974b's
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: [F-REVIEW-2026-10-25-t0009-1, F-REVIEW-2026-10-25-t0009-2, F-REVIEW-2026-10-25-t0009-3, F-REVIEW-2026-10-25-t0009-4, F-REVIEW-2026-10-25-t0009-5, F-REVIEW-2026-10-25-t0009-6, F-REVIEW-2026-10-25-t0009-7], ods: [OD-0062, OD-0063, OD-0065, OD-0067, OD-0075, OD-0078]}
---

# OD-0079: T-0009 accepted; PR #6 merged

## Owner actions (verbatim in the source file)

1. **Acceptance.** T-0009 (S1b-1.0) is accepted as completed work at `846974b2c43e5b9839809af0f1ebc08cee4e88b1`. That is
   the slice Authorisation A allowed (OD-0062): synthetic-fixture development, the documentation-only storage
   check, and IaC authoring (OD-0063, OD-0065). The basis:
   - `REVIEW-2026-10-25-t0009-1` (NOT READY at `ce0c3b5`, OD-0067);
   - its remediation, under OD-0067 and OD-0076;
   - all seven findings `verified_closed`: F-1 to F-4, F-6 and F-7 at `76539b5` (VERIFY-2026-10-28-t0009-1-1,
     OD-0075), and F-5 at `846974b` (VERIFY-2026-10-28-t0009-1-3, OD-0078).
2. **Merge.** PR #6 is integrated into `main` by the merge commit `7eba3f9`, of exactly `846974b`.
   - **Code unchanged.** At the merge, every code, test, tool, spec, infrastructure and register path equals
     `846974b`'s (`git diff 846974b 7eba3f9` over those paths is empty).
   - **One conflict.** It was in `docs/decisions/owner/README.md` and was resolved by keeping `main`'s rows, a
     superset (OD-0066 to OD-0078); the PR side added nothing there.
   - **Checks on the integrated head:** 416 passed; `ruff check` and `ruff format --check` clean; `check_repo.py`
     and trailers PASS.

## What is accepted, and what is not

**Accepted:** the S1b-1.0 synthetic-fixture slice: the cash adapters, capture-run records, shared F1 receipt, cash
releases and index comparisons, the cloud-store interface, the OpenTofu definitions (authored, never applied), the
disabled capture workflow and due-time gate, and the dated 2026 RITS and NSW reference calendars.

**Not accepted or authorised:**
- **Finality-staging work** (T-0009 §7): the C1–C7 checks, finality, the 10-business-day soak (S1-A13) and the P2
  mode. These remain owed before final labels, S1b-1 completion or G2.
- **Live acceptance and Authorisation B:**
  - any real fetch, schedule, provisioning or credential;
  - `tofu init/validate/plan/apply`;
  - any source right beyond D7 (OD-0076);
  - Q-013.
- **S1b-1 stage completion and S1b-2.**
- **The draft specs 0.3.0 and the `check_repo.py` proposals** (`VALID_TIME_EXEMPT`, the `archive/` naming rule).
  Their acceptance as work is not approval of a standard or spec.

**Known limits accepted with the work:**
- **Calendars:** they cover 2026 only (recheck by 2027-01-31).
- **Precision:** the declared precisions are unverified assumptions.
- **Same-vendor work:** remediation and receipt were both by Claude (author-receiver, OD-0061).

## Card

`registers/tasks/T-0009-s1b1-cash-capture-and-research.md`: `status: accepted`, `accepted_by: OD-0079`. This is an
administrative edit; the rest of the card is unchanged.

## Corrections (append-only)

None.
