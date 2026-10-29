---
id: HIO-BASE-CAMP
title: "Base camp: the procurement-readiness milestone (proposed)"
status: proposed            # drafted under OD-0130 item 1; adopted only by an explicit owner decision at an exact revision
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-10-29
base_revision: b1fc6b4
sources: [OD-0129 (architect consultation 20261029T182940-ask-9dab; Fable review), OD-0130]
---

# Base camp

> **Proposed.** It amends no gate. G2, S1 completion and the roadmap's ordering are unchanged unless the owner decides
> otherwise.

## Purpose

The owner's goal is a set of factors to assess and construct multi-asset portfolios quantitatively. Before any money
is spent on data (a budget of about AUD 400 a month is in view), the owner wants evidence that HIO stands on a stable
footing. **Base camp** is that evidence, defined so that each criterion can be checked by a named record.

**In one line:** HIO captures real observations reliably, constructs economically specified returns from them (cash,
plus one harder factor), keeps and reproduces the evidence, serves a pinned release safely, and knows what data it
needs and is allowed to use next.

## Exit criteria

Criteria 1–6 are the architect's (OD-0129), with criterion 4 reduced. Criteria 7–9 are Fable's additions.

| # | Criterion | Met when (the evidence) | Work that delivers it |
|---|---|---|---|
| 1 | **Provider behaviour demonstrated** | the B-2 report is retained in the repository; every check passed, or C5 holds after an owner-decided, evidence-based amendment. A failed timing check is never rounded into a pass | B-2 (plan: `docs/evidence/S1B1-B2-probe-plan.md`, proposed, PR #37) |
| 2 | **Unattended cash operation demonstrated** | ten consecutive Sydney business days of scheduled capture. Every expected slot is reconciled (`captured`, `verified_unchanged`, `failed` or `missing`) by the soak report. The punctuality bar is agreed **before** the soak. A failing *scheduled* run's email was received (I-5). The dead-man alert is shown to fire and resolve. Recovery after a failure is shown | T-0013 (monitoring), B-3, the soak |
| 3 | **Real cash construction demonstrated** | the AUD and USD cash accruals rebuild from retained receipts; the publisher-index comparisons account for every eligible period; precision, date alignment and every unexplained difference have a written disposition | T-0009 code on live receipts |
| 4 | **Specifications and finality recorded** | the cash specifications are validated and approved; the first real releases carry a C1–C7 finality evaluation recorded **alongside** each release. A missing evaluation blocks any final claim. Building finality into release identity can follow after base camp | a completion task (to be drafted) |
| 5 | **Recovery demonstrated** | a clean checkout plus the retained store reproduce a pinned release byte for byte; the catalogue rebuilds; the independent second copy (T-0011 I-8) and the state backup are restored once in a test | completion task; T-0011 I-8 |
| 6 | **A minimal consumer demonstrated** | a contract test in CI reads a pinned real release and applies the current rights and status checks; the synthetic refusal cases (withdrawal, tampering, insufficient permission) still pass. No SMSF data or code | completion task |
| 7 | **One harder factor proven on free data** | an AU or US duration (CMT) total return, including coupon cash, built from a rights-cleared free source; the RA-INV-013 fixtures pass and are reproduced on real inputs; a triangulation report. Research-only, not released | needs criterion 8 for its source, plus an owner change to the S2/S3-after-G2 ordering for research work |
| 8 | **Rights decided for the free long-history sources** | FRED/ALFRED, US Treasury, FRB H.10 and the RBA historical tables each recorded as owner-verified or explicitly denied, for historical research use (`hio_internal`). French and AQR data stay references only | rights rows (OD-0130 item 4), then the owner's verification |
| 9 | **A data-need statement** | for each Year-1 family (cash, FX, rates, equities, futures/commodities, trend): the required history, frequency, fields and construction inputs, derived from the risk-model plan. It is the input to every purchase decision | to be drafted |

## What base camp is not

- **Not S1 completion or G2.** HIO-ADR-0012 §5 still requires S1b-2 (live FX), its soak, the FX and bill triangulations,
  and the final completion evidence.
- **Not blocked by live FX (S1b-2).** FX would add a second instance of the same pipeline, not new architectural
  evidence. Clearing H.10 for historical use is in criterion 8.
- **Not a portfolio engine,** a full factor library or the full consumer integration (A05).

## Order and parallel work

1. T-0013 (monitoring fix) and B-2 run first. Both block B-3.
2. B-3 starts the soak (criterion 2). The soak is calendar time spent mostly waiting.
3. During the soak, in parallel: the completion task (criteria 3–6); rights rows and the owner's verification (8); the
   data-need statement (9); then the duration factor (7), once its source is cleared and the ordering change is decided.
4. **Hard date:** the 2027 RITS/NSW calendars must be loaded before 2027-01-01, or capture stops having RITS days. The
   RBA had not published them at 2026-10-29 (recheck due 2026-12-01).

**Estimate** (Fable, judgement; it assumes same-day owner responses and review rounds like T-0010's and T-0011's):
- criteria 1–6 by mid to late December 2026;
- all nine by about late January 2027.

## Spending after base camp (context for a later decision; nothing here authorises a purchase)

Both reviews agree on three points:
- **The licence class binds, not the monthly price:** personal or SMSF use, derived storage, and retention after
  cancelling.
- **Buy one package at a time,** each tied to a factor named in the data-need statement, with written vendor answers to
  the T-0003 questions first.
- **The likely first purchase** is one end-of-day feed covering ASX and US ETFs, with unadjusted closes and explicit
  distributions, ideally one that also carries futures.

All prices are unverified.

## Owner decision this document awaits

"Adopt `docs/base-camp.md` at `<revision>` as the procurement-readiness milestone, leaving G2 and S1 obligations
unchanged?" A yes adopts the definition only. Each piece of work it names needs its own authorisation.
