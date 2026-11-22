---
id: T-0024
title: "Build a first AUD multi-asset research comparison from five core sleeves"
status: proposed          # drafted under OD-0218; not authorised. Each work package needs its own owner yes
owner: owner
assignee_role: "implementation engineer (Claude orchestrator; hiomux workers for bounded tool work)"
created_at: 2026-11-22
updated_at: 2026-11-22
authorised_by: null       # OD-0218 authorised the draft only
base_revision: 6d7535a290107a899436bfa912996c7644555abc
accepted_by: null
review_required: "owner; one bounded Codex review per coherent slice, assigned by the owner or under OD-0184"
links:
  adrs_governing_approved: [docs/decisions/HIO-ADR-0005-rights-model.md, docs/decisions/HIO-ADR-0007-return-accounting-standard.md]
  adrs_context_proposed: []
  specs: []
  standards: [docs/standards/return-accounting-and-factor-construction.md, docs/standards/factor-specification.md, docs/standards/rights-and-licensing.md]
  findings: []
  depends_on: [T-0003]   # T-0020 and T-0023 are related, not prerequisites: see the dependency table
  blocks: []
---

# T-0024: a first AUD multi-asset research comparison

> **Proposed.** Drafted under OD-0218 from ChatGPT's guidance (`docs/history/2026-11-22-chatgpt-factor-programme-guidance.md`, advice only) and solution-architect consultation `20261122T133335-ask-3fa5` (advice only). The sequence is in `docs/decisions/factor-programme-sequence-proposal.md`.

## Purpose and rationale

The first factor builds (OD-0213 to OD-0217; `docs/evidence/factors/build-1.md` to `build-4.md`) show that HIO can build return series. They ran on separate owner instructions with no card. This card gives them one purpose: **a research comparison, in AUD, of how five exposures behave together and what drives their risk.**

| Sleeve | Vehicle or source today | State |
|---|---|---|
| AUD cash | RBA rate accrual joined to the RBA total return index | built, exploratory |
| US equity | SPY | built, exploratory |
| US Treasury duration | IEF | built, exploratory |
| Australian equity | VAS, from snapshot `s2` | built, exploratory (OD-0219) |
| Australian government duration | VGB, with IGB and AGVT as comparators, from snapshot `s4` | built, exploratory (OD-0222) |

Each sleeve is a **declared vehicle proxy**, not a pure factor: SPY is US equity, not global equity, and a bond fund is one maturity basket, not duration itself. Every output says so.

## Owner-authorised scope

None yet. The work packages below are proposals. Each needs its own yes.

**Milestone A: equity comparison**

| Package | Work | Output | Needs |
|---|---|---|---|
| A1 | Australian equity total return in AUD from the ASX fund already in snapshot `s2`: a spec, then a build with `tools/factor_build.py` | a proposed spec; a local build; `docs/evidence/factors/build-5.md` (stub) | **done under OD-0219,** exploratory and unaccepted |
| A2 | Targeted check of the SPY, IEF and BIL inputs: reuse T-0023's evidence, then name the remaining price and distribution gaps against independently readable reference bytes, with an expected-difference model, on the periods that matter most (2008, 2020, 2022) | a discrepancy table per sleeve, in the local results store; a stub here | **done under OD-0224 for VAS and VGB** (`docs/evidence/factors/issuer-check-1.md`); no new read for the US funds, whose remaining gaps are named there |
| A3 | Hedge inception: `tools/factor_translate.py` implies the forward from **realised** AUD and USD cash returns over the period, which were not known at inception (RA §3.2). Assess whether rates lockable at inception exist for both currencies at the hedge tenor. Until they do, mark the hedged series diagnostic-only in each spec and output | an input assessment; spec patch versions | **done under OD-0225** (`docs/research/T-0024-hedge-inception-assessment.md`, proposed; hedged specs at 0.1.1) |
| A4 | A research note: Australian and US equity against AUD cash on common complete months, unhedged, with the currency effect separated and uncertainty stated. Hedged figures appear only as labelled diagnostics | the note in the local store; `docs/evidence/factors/build-6.md` (stub) | **done under OD-0220,** exploratory and unaccepted |

A1, A2 and A3 have disjoint files and can run at once. A4 follows A1.

**Milestone B: defensive sleeves**

| Package | Work | Needs |
|---|---|---|
| B1 | A USD overnight cash leg with history: find a source, read its rights, then build `cash.usd.overnight` | a yes for the source and its rights |
| B2 | A hedge forward from AUD and USD rates lockable at inception, if A3 finds suitable inputs. A compounded overnight leg does not by itself supply one | open. **Anchor run first** (OD-0226; `docs/evidence/factors/hedge-anchor-1.md`): the CIP-implied series overstates a traded hedged fund's return, mostly for reasons a better rate would not fix |
| B3 | Australian government duration: a feasibility note first (a government-bond fund's total return, stating its sovereign exposure, maturity range, fees and price-versus-NAV convention. E-0001's par-curve approximation failed its bars, so a fund is the smaller route; that does not rule out every curve construction), then a build | **done:** feasibility note (OD-0221), then one fetch and three builds, VGB, IGB and AGVT (OD-0222; `docs/evidence/factors/build-7.md`); exploratory and unaccepted |
| B4 | A defensive-sleeve report: Australian and US duration against cash, with a 60/40 sensitivity | **done under OD-0223 as a five-sleeve comparison,** without B1 and B2 (`docs/evidence/factors/build-8.md`); exploratory and unaccepted |
| — | A distribution plausibility screen in the build tool, run on every held fund | **done under OD-0228** (`docs/evidence/factors/distribution-screen-1.md`); a duplicate record found in IGB, confirmed on public pages (OD-0229) and corrected at spec 0.1.1 (OD-0230; `docs/evidence/factors/build-9.md`) |

**Milestone C: later.** Shrinkage against sample covariance on the five sleeves, with fixed estimation windows and judged out of sample only. Credit and gold each need a separate data and exposure case. Not specified here.

**Alongside, on its own yes:** a deletable backup of the local stores (retained inputs and manifests as well as outputs) with one restore checked against the pinned hashes. The owner first decides whether the licence allows a copy off the Mac: OD-0210 did not authorise one, and encryption does not establish the right.

## Exclusions (explicitly out of scope)

- Any allocation recommendation, optimisation, tactical signal or preferred hedge ratio.
- Any publication to a consumer or the SMSF; any change to `macsmsf` or HIO-001.
- Any purchase, subscription change or vendor contact.
- Restarting E-0004 or H6; any change to capture or infrastructure; promotion through G2.
- Trend, futures and private credit.
- Adopting or approving any spec. Specs stay `proposed`.

## Governing documents

**Approved:** the return accounting standard (HIO-ADR-0007); the factor-specification standard (status ladder `draft → proposed → validated → approved`); the rights and licensing standard (HIO-ADR-0005).

**Context, proposed or adopted as working order:** `docs/roadmap.md` (proposed); `docs/decisions/factor-first-sequencing-proposal.md` (OD-0139); `docs/decisions/factor-programme-sequence-proposal.md` (proposed).

## Environment and rights constraints

- EODHD data: the `eodhd.personal_evaluation` row only. Local on the owner's Mac; agents may review; **no value enters the repository** (OD-0210). Workers get invented data, never the snapshot.
- Any new source: unknown means deny until the owner reads its terms and a rights row records them.
- No `macsmsf` access.

## Acceptance evidence

This card adds no new acceptance regime and no new status value. Every output here is `exploratory`. A local build record is not a validated release.

| ID | Test | Evidence expected |
|---|---|---|
| E1 | Each new series has a `proposed` spec and a pinned, repeatable build | `build.json` with input hashes; a byte-identical rebuild |
| E2 | Each tool is checked on real data by a script that shares no code with it | agreement per period, recorded in the build record |
| E3 | Each consequential sleeve has one targeted source check, with unresolved differences left visible | A2's table; no "vendor verified" statement |
| E4 | Each research note names its sample, return class, currency, timing mismatch and hedge assumption, and what it cannot answer | the note |
| E5 | No licensed value is in the repository | `tools/check_repo.py`; a sweep before each push |

A spec is `validated` only after an independent review of it and of its first release, for a stated purpose; a release reaches a consumer only by the owner's `approved_for_consumer` decision (`docs/standards/datasets-releases-and-artefacts.md` §5). Neither is in this card's scope.

## Decision dependencies, open questions, blockers

| Card | Relation |
|---|---|
| T-0003 | keeps the equity-source decision, which is undecided. Exploratory use here does not settle it; everything rests on one vendor under a personal evaluation licence |
| T-0020 | keeps the CMT experiment and its open validity questions. A fund proxy neither completes nor supersedes it |
| T-0023 | supplies reusable, bounded evidence. It is parked and unaccepted (OD-0215); its verification excluded licensed bytes and a real-input rebuild |

- **The reference index for Australian equity** and the treatment of franking credits (proposed: cash distributions only, franking excluded and stated).
- **The noon FX fix against 4 pm closes.** Monthly figures are reported as descriptive. Daily attribution is not reported.

## Stop and ask

Stop the affected package only, and offer the smallest evidence step or a narrower claim:

- a source, a fetch or a cost not already permitted, or unknown rights;
- reference evidence that the claim needs and that cannot be read;
- an unexplained difference that could reverse a comparison;
- too little common history, or no inception inputs for the hedge.

Also:

- A review returns NOT READY: one remediation and one verification, then ask (OD-0213).
- Any revision or rights mismatch.

## Intended outputs and next approval gate

The gate is the owner's yes on Milestone A's packages, singly or together.

## Submission (filled by the implementer)

## Review and acceptance
