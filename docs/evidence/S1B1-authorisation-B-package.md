---
id: HIO-EVIDENCE-S1B1-AUTH-B
title: "S1b-1 Authorisation B package: the staged apply steps from an empty hnf-prod to live daily capture"
status: proposed            # a request for owner decisions; authorises nothing
owner: HIO architecture lead (owner); prepared by claude/implementation-agent
created_at: 2026-10-29
base_revision: 579de8d
instruction: owner message AS ("2. authorised"), read as authorising preparation of this package (to be recorded with the next OD)
governs: [HIO-ADR-0012 rev 3, T-0009 §8, T-0010, T-0011, OD-0116, OD-0119]
---

# S1b-1 Authorisation B package

Authorisation B is the explicit owner act that permits live operation (T-0009 §8). It is split into **three stages**,
each a separate yes tied to an exact revision, so that infrastructure can exist before the code is accepted and so that
nothing captures until the last stage. Each stage lists its prerequisites; a missing one is a stop.

| Prerequisite | State at 579de8d |
|---|---|
| H1 rights (five datasets) | **met** (OD-0116 correction 1, OD-0118) |
| H2 Q-013 | P3 in force; not blocking |
| H3 controls, H4 storage | **decided** (OD-0119) |
| H5 | **declined** (OD-0119) |
| T-0011 review and acceptance | REVIEW-2026-10-29-t0011-1 running (OD-0120) |
| T-0010 review and acceptance | REVIEW-2026-10-29-t0010-1 running (OD-0120) |
| 2027 RITS and NSW calendars | RBA page not yet published; recheck by 2026-12-01 |

## Stage B-1: infrastructure (after T-0011 is accepted and PR #8 merged)

Executed by Claude in the owner's terminal session with the owner's `az` login, `--subscription hnf-prod` named on
every command (C-6: owner-run; the owner sees each plan before its apply). Values that identify the tenant, subscription,
principals or the owner's email are typed at the prompt or held in files outside the repository, never committed.

1. Register `Microsoft.Insights`, `Microsoft.OperationalInsights`, `Microsoft.AlertsManagement` (S-10).
2. `infra/tofu/bootstrap`: `tofu init`, `tofu plan` (shown to the owner), `tofu apply`; local state kept outside the
   repository, with a copy the owner holds (C-7).
3. `infra/tofu`: backend configuration file outside the repository; `tofu init` against the state account; `tofu plan`
   (shown to the owner); `tofu apply`. Inputs: `github_oidc_subject` in the immutable format, the owner as reader, the
   owner's alert email, budget 20.
4. GitHub: set the `capture` Environment variables (`HIO_STORAGE_ACCOUNT_URL`, `HIO_STORAGE_CONTAINER`,
   `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`; C-8). The reviewer rule stays until B-3.

**Leaves:** an empty evidence store, identities, logs, alert and budget. No data. Reversible by `tofu destroy` until the
immutability policy holds objects (none yet).

## Stage B-2: provider validation (S-6; before any real object is written)

The account-level immutability default applies to every container, so probe objects written to the evidence account
would be retained for 3,650 days. **Proposed:** a separate, short-lived probe account with the same settings and a one-day
immutability period, created and destroyed by the probe configuration; a small probe workflow on the `capture` identity
pattern exercises: create, conditional-create conflict, overwrite and delete denied for the writer, version listing,
and `Last-Modified` against `completed_at` over repeated runs. **Owed:** the probe configuration and workflow (a small
T-0010/T-0011 extension). **Outcome needed:** whether C5's `completed_at ≤ s` holds with whole-second timestamps; if
not, an owner decision on a C5 tolerance (an ADR-0012 change).

## Stage B-3: go-live (after T-0010 is accepted and merged, and B-2's outcome is decided)

1. **Data-source URLs:** the exact URL for each of the five datasets, proposed by Claude from the publishers'
   documentation and approved by the owner (each URL is part of the approved request identity).
2. `LIVE_AUTHORISATION` in `src/hio/jobs/s1b1_capture.py` set to the Authorisation B OD id; the workflow moved from
   `infra/workflows/` to `.github/workflows/` (by PR).
3. Remove the `capture` Environment's required-reviewer rule (C-4, authorised by OD-0119).
4. One manual `workflow_dispatch` run, watched; then the schedule runs.
5. **The soak** (T-0009 §7): ten consecutive Sydney business days; punctuality and gaps recorded; a deliberate-failure
   alert test; a sampled CI-run audit (C6); replay and reconstruction on live receipts.

## What each yes will say

- **B-1:** "Apply T-0011 at `<revision>` to `hnf-prod`: provider registration, bootstrap, evidence store, Environment
  variables." Nothing captures.
- **B-2:** "Create the probe account and run the S-6 probe at `<revision>`; destroy it afterwards."
- **B-3:** "Go live at `<revision>` with these five URLs." Capture starts; the soak begins.

## Not approved by this document

Everything above is proposed. No Azure write, GitHub change, live request or capture is authorised by it.
