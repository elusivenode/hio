---
id: HIO-G1-PACKAGE
title: A01 Gate G1 owner decision package
status: current            # a decision aid, not a decision. Nothing in it is approved.
owner: owner (decides); prepared by claude/documentation-agent
prepared_at: 2026-10-18
evidence_revision: a82aa0dbddcbf63bb3432a3ddcf5df48300ff2b1   # the receipt merge of the Codex verification
authorised_by: owner directive hio/docs/history/2026-10-18-directive-g1-approval-package.md
---

# A01 Gate G1: owner decision package

> **Nothing here is approved.** Every item below is `proposed` or `draft` until you record an
> explicit decision, tied to its revision. Silence, a merge, Codex's READY opinion, or this
> package does not approve anything. Recommendations are labelled **Claude recommends**, and
> are not decisions.

## 1. What is being decided, at which revision

**Approval target revision:** `a82aa0dbddcbf63bb3432a3ddcf5df48300ff2b1`. Each item is pinned
by its git blob hash, the first 12 characters, at that revision. Later commits that add this
package and update navigation change none of these files. Check that with
`git diff a82aa0d HEAD -- <path>`, which should be empty.

| # | Item | Path | Blob at `a82aa0d` | Status | Version |
|---|---|---|---|---|---|
| 1 | Charter | `hio/docs/charter.md` | `740d88c5e098` | proposed | 0.1 |
| 2 | Architecture baseline | `hio/docs/architecture.md` | `9e384d1c9de2` | proposed | 0.1 |
| 3 | HIO-ADR-0001 separate system, modular monolith | `hio/docs/decisions/HIO-ADR-0001-*.md` | `8a2c015a2422` | proposed | — |
| 4 | HIO-ADR-0002 systems of record, SMSF boundary | `…/HIO-ADR-0002-*.md` | `d27994cd3663` | proposed | — |
| 5 | HIO-ADR-0003 instrument identity, HIO-001 boundary (option C1) | `…/HIO-ADR-0003-*.md` | `79b3e40fe1a7` | proposed | — |
| 6 | HIO-ADR-0004 temporal semantics | `…/HIO-ADR-0004-*.md` | `bd86ec3938c8` | proposed | — |
| 7 | HIO-ADR-0005 rights model | `…/HIO-ADR-0005-*.md` | `2e223877d9b7` | proposed | — |
| 8 | HIO-ADR-0006 releases, artefacts, publication | `…/HIO-ADR-0006-*.md` | `595e6b4f829c` | proposed | — |
| 9 | HIO-ADR-0007 return accounting standard as a gate | `…/HIO-ADR-0007-*.md` | `e97a36599575` | proposed | — |
| 10 | HIO-ADR-0008 canonical knowledge and harness | `…/HIO-ADR-0008-*.md` | `fffb4be30556` | proposed | — |
| 11 | HIO-ADR-0009 catalogue from manifests | `…/HIO-ADR-0009-*.md` | `1ec9ed0e95ff` | proposed | — |
| 12 | HIO-ADR-0010 first-slice scope | `…/HIO-ADR-0010-*.md` | `fe651aca746d` | proposed | — |
| 13 | Observations and PIT standard | `hio/docs/standards/observations-and-point-in-time.md` | `bd9eff0893ea` | proposed | 0.2 |
| 14 | Return accounting and factor construction standard | `…/return-accounting-and-factor-construction.md` | `651c3abe1259` | proposed | 0.2 |
| 15 | Datasets, releases and artefacts standard | `…/datasets-releases-and-artefacts.md` | `8539be643e9d` | proposed | 0.2 |
| 16 | Rights and licensing standard | `…/rights-and-licensing.md` | `1d7296db6670` | proposed | 0.2 |
| 17 | Reference identity standard | `…/reference-identity.md` | `7796e7b38331` | proposed | 0.1 |
| 18 | Factor specification standard | `…/factor-specification.md` | `6d380434c320` | proposed | 0.1 |
| 19 | Harness: operating model | `hio/docs/harness/operating-model.md` | `7172659cf4ba` | proposed | harness-0.5 |
| 20 | Harness: entry point | `hio/AGENTS.md` | `4000ab1895ee` | current (provisional protocol) | harness-0.5 |
| 21 | S1 specs: AUD cash, USD cash, FX excess | `hio/specs/factors/{cash.aud.overnight,cash.usd.overnight,fx.usd_cash_vs_aud.excess}.yaml` | `4fda37d45e7f`, `8730879fc0a3`, `58af1f3249ce` | draft | 0.2.0 |
| 22 | Roadmap; implementation plan | `hio/docs/roadmap.md`; `hio/docs/implementation-plan.md` | `6561f75dd607`; `e1ebadcb8d48` | proposed | 0.1 |

## 2. Decision matrix

For each item, the decision sought is **approve**, **revise** (with the change) or **defer**
(with a revisit trigger).

| # | Scope if approved | Material trade-off | Claude recommends |
|---|---|---|---|
| 1–2 | the mission, philosophy, five-year trajectory and architecture are binding direction | broad and long-horizon; revisited annually at G6 | approve |
| 3 | a separate repository; one codebase; independently scheduled jobs | relies on import discipline rather than process boundaries | approve |
| 4 | systems of record; a fund-level-only SMSF projection; pinned artefacts; no shared runtime | integration costs two SMSF slices later (G5) | approve; confirm the projection fields (§6) |
| 5 | HIO owns reference data and taxonomy; SMSF keeps its held-vehicle dimension (C1); join on MIC + ticker and ISIN | leaves an `HIO_ECONOMIC` naming wart inside SMSF | approve C1, **or** defer until the HIO reference context is designed. Either way, decide before HIO-001 activation |
| 6 + 13 | vintage-specific knowability; `as_known_by_market` / `as_captured_by_hio` / `reconstructed` | stricter: much backfilled history becomes "reconstructed only" | approve |
| 7 + 16 | every operation is rights-gated and fails closed; `automated_retrieval` | more verification work per source before any live use | approve |
| 8 + 15 | content-hash identity excludes run metadata and status; status as events | the canonical rendering is still an S1 choice (§7) | approve |
| 9 + 14 | the return accounting standard v0.2 as a CI gate | the gate blocks factors lacking income data (e.g. equity until T-0003) | approve |
| 10 + 19 | owner decision records; record lifecycles; review worktree protocol | process overhead; the fresh-session cold-start test is still pending | approve. T-0007's protocol (§6.2) is already accepted at `b48f83c` (OD-0004); approving ADR-0008 makes the harness non-provisional |
| 11 | catalogue = manifests plus a local index; no hosted database initially | concurrency limits; measurable triggers to revisit | approve |
| 12 | first slice = cash and FX walking skeleton, including live capture | conflicts with a fixture-first start (§7) | **revise**: split S1 into S1a (fixture-only) and S1b (live, after T-0002); see §7 |
| 17–18 | identity and spec conventions | light; mostly used from S2 on | approve |
| 21 | draft specs used as S1a fixture specifications | they stay `draft` until S1 executes them | defer approval: the specs are validated by S1 execution plus review, not at G1 |
| 22 | planning baseline | — | note, not approve: they are recommendations that update as gates pass |

## 3. Review evidence

| Stage | Revision | Record |
|---|---|---|
| Original A01 review (Codex), REQUEST CHANGES, 8 findings | base `1502ab8804c5968a8bf91fa36275c44e6e84f575`, head `35c9821f805955914b05991c1c075b8cb3e082b5` | `hio/reviews/records/REVIEW-2026-10-18-a01.md` |
| Claude remediation (T-0008): fix commit, then submission head | `0e3de4b76398799692cd09f3982c12986e195e7b`, then `0c74686fa1de21fb2e7ac6ef361c716df67b35a9` | `hio/reviews/responses/RESPONSE-REVIEW-2026-10-18-a01-1.md` (author claim) |
| Codex verification: **all eight `verified_closed`**, no new findings, no waivers | `bb4aa7258f2da5951337aa62b0e469d74cefb89e` (report `5b4c50e`) | `hio/reviews/records/VERIFY-2026-10-18-a01-1.md` (**authoritative**); `hio/reviews/reports/A01-independent-verification-and-readiness-2026-10-18.md` (reviewer opinion) |
| Receipt merge | `a82aa0dbddcbf63bb3432a3ddcf5df48300ff2b1` | merge commit message (scope check PASS) |

Findings, all **verified_closed** by Codex:

| Finding | Severity | Subject |
|---|---|---|
| F-REVIEW-2026-10-18-a01-1 | critical | PIT backfill masquerade |
| -2 | high | USD cash fixing look-ahead |
| -3 | high | release identity versus status |
| -4 | high | CMT coupon |
| -5 | high | rights gates per operation |
| -6 | high | bill rates as returns |
| -7 | medium | compounding bound |
| -8 | medium | forward denominator |

**Codex's readiness opinion** (not approval): **A01 G1: READY WITH CONDITIONS. HIO-S1: NOT
READY.**

**Receipt observations** (not findings):
- (a) `hio/reviews/reports/` is not among the reviewer write paths listed in operating model
  §6.2 step 3, although the checker allows it. **Decide whether to add it** (a one-line harness
  edit) or keep reports in `records/`.
- (b) Codex shortened the author's eight remediation-claim cells. The facts are preserved.

### What is verified, and what is not

| Verified (independently, by Codex) | NOT verified by anyone yet |
|---|---|
| the design contracts as written; the synthetic counterexamples; the fixture arithmetic (Decimal-reproduced) | any application code (none exists); execution of S1 fixtures |
| internal consistency of the standards, specs, ADRs and S1 tests for the eight findings | actual source licence grants and terms (T-0002); publication instants and time zones; the AUD rate regime |
| the HIO/SMSF documentation boundary (no `macsmsf` file changed by T-0008) | NY/Sydney calendar alignment against real data; market forward/CIP basis; vendor equity TR (T-0003) |
| | cloud behaviour: GitHub Actions cron punctuality, bucket versioning and object lock; the fresh-session Codex cold-start test |

## 4. Outstanding conditions, kept separate

| Category | Conditions |
|---|---|
| **A01 approval (G1)** | the owner's revision-specific decisions on items 1–20; T-0008 acceptance decided separately; receipt observation (a) resolved or noted |
| **S1a authorisation (fixture-only)** | G1 approvals of at least ADR-0001, 0004, 0005, 0006, 0007, 0009 and a revised 0010; an owner OD authorising S1a; repository creation (owner); no data, network or credentials |
| **S1b / live-data readiness** | T-0002 `owner_verified` rights for every operation, per source; verified publication timing and the AUD regime; calendars evidenced; bucket provisioned with scoped keys; S1a fixtures passing and reviewed |

**G1 approval does not authorise HIO-S1. Fixture-only S1 does not authorise live data
operations.**

## 5. Architectural invariants that approval would bind

1. **HIO/SMSF boundary:** separate system. HIO never writes SMSF truth or holds trustee
   authority; the only interfaces are a fund-level projection and pinned artefacts (ADR-0002).
2. **Factor versus vehicle separation:** portfolios are in exposure space, and vehicles are
   assessed downstream (charter §3; ADR-0003).
3. **Economic return correctness:** total and excess returns are accounted; `price_only` and
   `state_indicator` series are never returns; single-period identities are exact (RA v0.2;
   ADR-0007).
4. **Value-specific PIT evidence:** knowability per vintage; a schedule is not evidence;
   reconstruction is labelled (observations v0.2; ADR-0004).
5. **Operation-specific rights:** every operation is gated and fails closed (rights v0.2;
   ADR-0005).
6. **Immutable, reproducible releases:** a deterministic content hash; status as events;
   withdrawal visible to pinned consumers (releases v0.2; ADR-0006).
7. **Owner-controlled decisions:** instruct, accept, approve and waive are explicit and
   revision-specific; review is independent (ADR-0008; operating model §1.1, §6.2).

## 6. The HIO-001 boundary (no change to `macsmsf`)

- **Proposal** (ADR-0003, option C1):
  - SMSF keeps `dim_instrument`, `instrument_identifier` and `instrument_asset_map` as its
    held-vehicle dimension, corroborated against SF360 and broker data;
  - HIO owns multi-portfolio reference data and economic taxonomies;
  - the two join on (MIC, ticker, date) and ISIN.
- **Change impact if approved:** one documentation-only `macsmsf` commit amending ADR 0003
  (T-0004). There is **no code, migration or activation change**. HIO-001's existing activation
  prerequisites (A17, the judgement calls, vehicle types) are unchanged.
- **If deferred:** decide before HIO-001 activation. Otherwise the `HIO_ECONOMIC` taxonomy
  becomes a de facto second master.
- **Projection fields to confirm** (ADR-0002): date; MIC + ticker and ISIN; units; AUD market
  value; staleness and provisional flags; fund-level external flows; fund TWR index; producing
  revision. No member data.

## 7. Recommended next implementation slice (NOT started)

**Claude recommends S1a: a synthetic-fixture-only foundation**, started after G1, while T-0002
runs in parallel.

**Scope:**
- the new `hio` repository (history-preserving migration per operating model §8.1);
- CI: tests, import rules, documentation checks, the review-branch checker;
- `contracts` schemas;
- a **local-filesystem object-store adapter** (no cloud bucket);
- the observation, vintage and knowability model with the three query modes;
- manifest-derived catalogue;
- the three S1 constructions;
- the rights gate with synthetic sources;
- the publication gate.

**Acceptance (all synthetic):**
- OBS-INV-001…007 (including the §4.1 backfill fixture);
- RA §3.2 cash fixtures and the CASH-USD-INV-3 look-ahead trap;
- FXC-INV-1…4;
- RA-INV-021 forward fixtures;
- releases §6.1 fixtures;
- rights fail-closed fixtures for fetch, store raw, build, store derived, rebuild and publish;
- the import-rule and independence checks;
- reproducible rebuild in CI;
- harness CI checks;
- a Codex review on an assigned head.

**Excluded:** network fetch, real sources, credentials, buckets, scheduling and soak. All of
these go to S1b.

**Why fixture-first:** it removes T-0002 and infrastructure from the critical path. Every
contract the A01 review hardened becomes executable before real data touches it. The cost is
that the PIT capture clock starts later (at S1b), so **start T-0002 now**.

**Open design choices:**

| Choice | Claude's preferred resolution | Owner question |
|---|---|---|
| Canonical hashing | **Logical content hash** over canonical row-sorted JSON Lines: rows sorted by primary key (`series_id`, `key`, `vintage_seq`); observed values as **exact decimal strings** as published; derived floats as IEEE-754 shortest round-trip text; `-0.0` normalised to `0.0`; **NaN and ±Inf forbidden** in releases (missing = null). The physical Parquet hash is recorded for integrity only, never as identity | adopt? |
| Calendars | a curated in-repo calendar registry (NY Fed SOFR business days, Sydney/RBA business days), each with a cited source [EXT], validated against observed publication days once S1b captures | adopt, and name the evidence source per calendar in T-0002? |
| Cash publication and AUD regime | treat AUD as **in arrears** until T-0002 evidences ex-ante publication; record publication instants per source in T-0002 | confirm T-0002 owns this |
| First equity TR (S2) | a licensed EOD vendor **market-price TR** of a US-listed S&P 500 ETF with explicit dividends, triangulated against issuer NAV TR. **No adjusted-close proxy**; nothing ships without T-0003/ADR-0011 | approve T-0003 to start? |
| SMSF projection | keep the ADR-0002 fund-level fields; implement only at G5 when a consumer needs it | confirm the boundary is still right |
| Live operation rights | none in S1a. S1b requires T-0002 `owner_verified` for fetch, store raw, build, store derived, rebuild, publish and external processing per source; no agent-context use of licensed data | authorise T-0002 now? |

## 8. Owner decisions required, in order

Each needs your explicit words. Claude records each as an OD tied to the revision above.

1. **T-0008:** accept, or return, at `0c74686`. **Claude recommends: accept.** It is verified by
   Codex.
2. **T-0006:** accept, or return, at `35c9821`. Later harness changes are under T-0007, already
   accepted. **Claude recommends: accept as completed work**, noting its content was revised by
   T-0007.
3. **G1 items 1–20** (§2 matrix): approve, revise or defer each. **Claude recommends:** approve
   1–11, 13–20; **revise 12 (ADR-0010)** to the S1a/S1b split; decide item 5 (C1) now or before
   HIO-001 activation.
4. **Receipt observation (a):** add `reviews/reports/` to §6.2's reviewer paths, or not.
5. **T-0002:** authorise source rights and timing verification (research only). **Claude
   recommends: authorise now.**
6. **T-0003:** authorise equity TR source evaluation (research only). **Claude recommends:
   authorise.**
7. **T-0004:** only if C1 is approved, authorise the documentation-only `macsmsf` ADR 0003
   amendment.
8. **S1a:** after 3 and the revised ADR-0010, authorise the fixture-only slice and repository
   creation. *Not part of G1.*

**No other decision is pending. Silence on any item leaves it `proposed`.**
