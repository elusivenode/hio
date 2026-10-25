---
id: HIO-ADR-0011
title: "Staged S1b live-observation implementation: S1b-1 official AUD and USD overnight cash benchmarks and publisher cash-return indices; S1b-2 FX and the AUD-investor USD cash excess return on a separately authorised FX source; further triangulations independently gated"
status: proposed   # NOT policy. HIO-ADR-0010 rev 3 (OD-0011, 760f73e, blob 8ade1962cf28) remains approved and in force, unedited
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
date: 2026-10-25
supersedes: []          # on approval only, in part: the HIO-ADR-0010 rev 3 S1b provisions S10-B2 and S10-B5, and the wording of S10-B8(ii) if its condition applies (§2); nothing else
superseded_by: null
gates: [S1b-1 authorisation, S1b-2 authorisation]
review_record: null     # independent review required before approval (decisions README, process step 3); draft assignment: HIO-ADR-0011-review-assignment-draft.md
drafted_under: [OD-0046, OD-0047]
evidence: [docs/evidence/S1B-readiness-assessment.md, docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md, docs/research/T-0002-owner-verification-matrix.md]
---

# HIO-ADR-0011: staged S1b live-observation implementation

> **Proposed, not policy.** HIO-ADR-0010 revision 3 stays approved and in force, and its file is
> not edited. If this ADR is approved, it supersedes **only** the revision 3 provisions marked
> "superseded" in §2, and every revision 3 S1b obligation is kept and re-mapped (§5). If it is
> rejected, nothing changes.
>
> **Numbering.** The owner chose `HIO-ADR-0011` (OD-0047). Earlier planning documents reserve
> "HIO-ADR-0011" for the equity total-return source decision (T-0003 Q3, roadmap G3,
> implementation plan S2, the G1 decision package, REVIEW-2026-10-18-a01). Those references are
> left unedited, pending the owner's renumbering of the equity ADR.

## 1. Context

**Revision 3 defines S1b as one stage.** The 2026-10-25 primary-source evidence
([evidence note](../research/T-0002-rba-nyfed-evidence-2026-10-25.md), accessed 2026-10-25)
shows that one stage cannot be cleared on publisher terms. [OBS] marks facts from the
publishers' files and pages:

- [OBS] **RBA F11 AUD/USD (`FXRUSD`): `Source` WM/Reuters.** It is the "WM/Reuters Australian
  Dollar Fix at 4.00 pm (Sydney)" (RBA definitions page).
  - RBA copyright §7.2: third-party material "may not be reproduced, published, communicated to
    the public, adapted or otherwise used in whole or part" without the third party's consent.
  - **No consent evidence exists.** The FX input of `fx.usd_cash_vs_aud.excess` therefore has
    **absent** permissions. That is not an explicit denial; see §4.6.
- [OBS] **RBA F1 1-month BAB (`FIRMMBAB30D`): `Source` ASX.** The same position. The RBA's own
  Treasury Note columns are empty in 2026.
- [OBS] **FRB H.10 is weekly.** Its DDP package builder is removed "the week of November 9",
  which leaves FRED. US Treasury bill terms are not located (2026-10-18).
- [OBS] **AONIA (`FIRMMCRID`) and the Cash Rate TRI (`FIRMMCTRI`) are `Source` RBA.** SOFR and
  the SOFR Index are NY Fed content, under terms with explicit automated access, storage and
  derivation.
- **Revision 3's premise "All S1 sources are official and keyless"** (its Options table) holds
  for the cash sources. **It does not hold for the F11 AUD/USD value.**

## 2. Revision 3 provisions: retained, superseded, refined

Revision 3 is quoted from the approved blob `8ade1962cf283a11470e1a199309f12610981dc1`. That is
`macsmsf@760f73e`, which is `hio` commit `5ea6287` (`MIGRATION-MAP.md`). Today's file differs from
it only in its status and approval lines. The ids `S10-*` are introduced here for reference only.

| Id | Revision 3 provision (S1b) | On approval of this ADR |
|---|---|---|
| S10-A | the **whole S1a column**, the S1a entry gate, "S1a authorises no live data operation", and the S1a history: OD-0011, OD-0017, the S1a acceptance by OD-0042 | **retained, untouched** |
| S10-B1 | S1b purpose: "start point-in-time capture of the official S1 sources" | **retained**; delivered per stage (§4) |
| S10-B2 | S1b includes: "real-source adapters (RBA, NY Fed, US Treasury, FRB H.10) behind the rights gate; a cloud bucket with scoped keys; scheduled capture; the soak; the three triangulation reports" | **superseded** by the stage table (§4.2). Every element is kept, but split across S1b-1, S1b-2 and independently gated triangulations; adapters are per dataset |
| S10-B3 | S1b excludes: "equity, bonds, futures; publication beyond `hio_internal`" | **retained** for every stage |
| S10-B4 | S1b acceptance: "S1-A1…A16 of the implementation plan against real sources, including the soak (S1-A13) and the triangulations (S1-A10)" | **retained** as the S1b completion criterion and G2 evidence; discharged in stages (§5) |
| S10-B5 | S1b entry gate: "S1a accepted; T-0002 `owner_verified` rights for every operation S1b performs, per source; publication timing, calendars and the AUD rate regime evidenced; the owner authorises S1b's scope and infrastructure" | **superseded** by per-stage gates (§4.2). Each contains every revision 3 condition, restricted to its datasets, and adds per-dataset rights and the OD-0038 control decision. **No condition is weakened** |
| S10-B6 | "S1a acceptance does not by itself authorise S1b" | **retained**; also, S1b-1 authorisation or acceptance does not authorise S1b-2 |
| S10-B7 | "The point-in-time capture clock starts at S1b, not at S1a" | **retained, refined**: each series' clock starts when the stage that captures it starts (`capture_started_at` per source, observations §5) |
| S10-B8 | S1's research output: (i) "the investable AUD-investor USD cash excess return, decomposed exactly into spot, carry and cross term"; (ii) "a triangulation of RBA and Federal Reserve FX fixings"; (iii) "a triangulation of overnight cash versus bills" | (i) and (iii) **retained**. (ii) **supersession proposed in wording only**, and only if the owner chooses an FX source other than RBA F11: "RBA" becomes "the S1b-2 FX source", and "Federal Reserve FX fixings" becomes "an independent FX publisher whose rights are `owner_verified`" (§5, S1-A10a). If the S1b-2 source **is** RBA F11 under consent, (ii) stands as written |
| S10-C | the Context, Options, Approval and Changelog sections | **retained, untouched** |

## 3. What this ADR does not change

These are invariants. A design that needs any of them changed **stops** and returns to the
owner.

1. **The S1a foundation as accepted** (OD-0042):
   - the implementation object ids at `084154c`;
   - the four S1a release `data.csv` sha256;
   - the fail-closed rights gate.

   S1b adds adapters and schedules beside S1a, and changes no S1a semantics.
2. **The return mathematics** (RA v0.2): §3.2 accrual, compounding and regimes; §4 FX; the
   invariant catalogue §13.
   - Spec patches only **align** the specs with RA. Example: `cash.aud.overnight` selects rates
     on RITS days, per RA §3.2 step 2 ("of that rate's market").
   - A spec whose numbers change takes a version bump.
3. **The observation invariants:**
   - OBS-INV-001…007;
   - the three query modes;
   - vintage-specific `knowable_basis`;
   - capture-clock ranking and derived conflicts (Q-001 r4, Q-002 r5, Q-002-R1 r1).
4. **The evidence-integrity contract:**
   - write-once, content-addressed receipts verified on read;
   - capture records fixed at capture;
   - bucket versioning;
   - capture gaps recorded, never filled;
   - no backfill presented as captured.
5. **Release integrity:**
   - release ids and `content_sha256` reproduce from receipts (S1-A11);
   - status events do not change identity;
   - `hio_internal` only;
   - `approved_for_consumer` before publication (OD-0038).
6. **The HIO/`macsmsf` boundary** (HIO-ADR-0002): no import, data, credential or network route
   (S1-A1).

## 4. Decision (proposed)

### 4.1 Cash factors are funding-rate benchmarks

The S1b cash series are **overnight funding-rate benchmarks compounded in arrears**:
- the interbank unsecured cash rate (AONIA) in AUD;
- secured repo (SOFR) in USD.

They serve as the financing and collateral reference for excess returns. **They are not
investor-achievable deposit, account or fund returns.**

Their classification is already correct under RA, so **no reclassification** is needed:
- `series_class: total_return`: income-inclusive accrual of a notional funded position;
- `investability: replicable_with_basis`: "a proxy whose basis is declared" (RA §2, §3.2 step
  4, §10).

**Each release manifest and limitations block states, in words:** "benchmark accrual; not an
achievable deposit or fund return; replicable only with a basis". `investable` must not be
claimed.

### 4.2 Stages

| | **S1b-1: official cash benchmarks** | **S1b-2: FX and the excess return** | **Further triangulations** |
|---|---|---|---|
| **Datasets** (source id each) | `rba.cash_rate` (AONIA); `rba.expert_judgement` (the F1 expert-judgement file); `rba.cash_rate_tri`; optionally `rba.cash_rate_target`; `nyfed.sofr`; `nyfed.sofr_index` | one FX fixing source, chosen in a **separate FX-source decision** | each reference source |
| **Outputs** | `cash.aud.overnight`, `cash.usd.overnight` (`as_captured_by_hio`, with labelled `reconstructed(T)` history); two **index triangulations** (§4.4) | `fx.usd_cash_vs_aud.excess` and its decomposition (S1-A9); the FX fixing triangulation | the bill-rate triangulations; any later reference |
| **Calendars** (cited reference data) | RITS (AONIA selection); SIFMA (SOFR); NSW, defining J for `cash.usd` periods until S1b-2 supplies fixings | the FX source's calendar; J checked against actual fixings | each reference's |
| **Entry gate** | (a) S1a accepted (done, OD-0042); (b) **`owner_verified` rights for each S1b-1 dataset × each operation it performs** ([matrix](../research/T-0002-owner-verification-matrix.md)); (c) cited RITS, SIFMA and NSW calendars; (d) publication timing evidenced and the spec patches applied: AUD regime "in arrears", RITS selection, the §4.1 wording, the windows in §4.3; (e) the network and credential-control decision (OD-0038); (f) the bucket and keys decision; (g) the owner's S1b-1 authorisation of scope and infrastructure | (a) S1b-1 authorised; (b) the **FX-source decision**, with `owner_verified` rights for that source × every operation; (c) publication timing and calendar for it; (d) the FX spec re-versioned if the source is not RBA F11 (quote convention per RA-INV-007); (e) the owner's S1b-2 authorisation | per triangulation: `owner_verified` rights for its reference; a cited calendar; a methodological-suitability note with a pre-registered expected-difference model; an owner instruction |
| **Excludes** | FX; equity, bonds, futures; any `smsf_*` distribution | the same, apart from FX | — |

### 4.3 Publication and revision windows (both stages)

For each series, the spec declares two instants from the publisher's documentation:

| Series | Publication instant P | Window close W (final) | Evidence |
|---|---|---|---|
| AONIA, Cash Rate TRI | before 09:20 Sydney, on the next RITS day after the rate's day b (the TRI is dated by its publication day) | 16:00 Sydney on that day ("will not revise" after) | RBA cash-rate methodology, last updated 21 July 2026 |
| SOFR, SOFR Index | about 08:00 ET on the next SIFMA day (the index is dated by its publication day) | about 14:30 ET on that day (a revision only if it moves more than 1 bp) | NY Fed reference-rate information, last updated 10/5/2026 |
| FX | per the S1b-2 source | per the S1b-2 source | S1b-2 |

**Rules.** Each uses only existing standard mechanisms.

1. **First capture**, after P and within `capture_grace`. A new vintage gets
   `knowable_at` = P and `knowable_basis = captured_on_schedule`.
   - Where P is uncertain, use the **later** documented candidate.
   - A capture after P plus `capture_grace` keeps `captured_at` as fact but does not claim
     `captured_on_schedule` (the Q-004 default, for the owner to confirm).
2. **Final capture**, after W.
   - If identical, it is a no-op (OBS-INV-001).
   - If changed, it creates a new vintage with `knowable_at` = W (the latest instant the
     revision could have been published), `captured_on_schedule`, logged by revision detection
     (observations §6).
   - SOFR's `revisionIndicator` is recorded as a material attribute, so a change to it alone
     also makes a new vintage.
3. **Out-of-window change.** A value that differs at a capture after W on a later day becomes
   a new vintage (never an overwrite). It is logged **and quarantined pending owner review**,
   by a series-specific quality rule. This is additive: the observations §6 gates are a
   minimum.
4. **Final builds.** A release described as final for period t uses a `knowledge_cutoff` after
   W of every input used. For X_t, that is the SOFR window close on NY day t, about 05:30–06:30
   Sydney on t+1.
   - Earlier cutoffs are allowed, but such releases are exploratory and identified by their
     recorded cutoff.
   - No new release attribute is needed.
5. **Gaps and backfill.** A missed run is a recorded capture gap. A backfill is a single
   current-value receipt, `schedule_only`, usable only through `reconstructed(T)`.
6. **Expert-judgement days.** An AONIA type-A day (the last rate republished) repeats the prior
   value by design. It is flagged from `rba.expert_judgement` and must not trip staleness.

**Capture schedule.**
- Two captures per series per publication day: shortly after P, and after W.
  - AONIA and TRI at about 09:45 and about 16:30 Sydney;
  - SOFR and SOFR Index at about 08:30 and about 15:00 ET.
- Jobs fire on several UTC cron slots, and act only when the local P or W is due, because the
  Sydney and New York daylight-saving switches move independently. Idempotence makes the extra
  runs no-ops.
- Requests stay light (a few a day per source), as the NY Fed terms condition automated access
  on not impairing the site.

### 4.4 Index triangulations (added in S1b-1; not substitutes)

Both follow S1-A10's form: a pre-registered expected-difference model, an outcome
classification, and **no pass or fail on agreement**. They are **not** identity invariants;
the RA invariants stay as approved. Neither becomes a CI gate without a later owner decision.

| Triangulation | Compared | Expected difference |
|---|---|---|
| `cash.aud.overnight` vs RBA Cash Rate TRI | `I_t/I_s` against TRI(t)/TRI(s), for period ends s < t on RITS days. A TRI value dated P compounds the rate applicable to the previous business day over the days since then, which is the period return ending at P, so there is **no label shift** | about 0. Residuals only from the TRI's documented accrual convention (non-business days accrue at the preceding business day's rate and are paid on the next business day, per the methodology) and its rounding; any other residual is classified unexplained |
| `cash.usd.overnight` vs NY Fed SOFR Index | the same, on dates in both J and SIFMA | about 0. Residuals only from the index rounding and the declared NY/Sydney date-label alignment |

### 4.5 Source-specific permissions

- **One source id per dataset** (§4.2), as the rights standard §1 allows "where terms differ".
  The accepted per-source gate applies unchanged.
- **RBA automated retrieval and the NY Fed permissions are recommended interpretations only,**
  pending the owner's explicit verification per dataset and per operation
  ([matrix](../research/T-0002-owner-verification-matrix.md)):
  - for RBA: the CC BY 4.0 licence covers copyright, not the access method, and the terms are
    silent on automated access;
  - for the NY Fed: the terms expressly allow access "manually or through an automated process
    or device".
- **The conditions recorded in every release manifest** (primary-source terms, 2026-10-25):
  - **RBA:**
    - attribution, "Source: Reserve Bank of Australia [year]" (or "Source: RBA [year]");
    - no suggestion of endorsement;
    - for AONIA, the §4 Cash Rate conditions: no implied endorsement, no unlawful use, no
      improper commercial exploitation;
    - for other RBA series, the §5 Financial Data conditions: risk on the user, no benchmark
      use implied, possible withdrawal.
  - **NY Fed:**
    - modified content "clearly label[led]": each release identifies itself as an HIO
      derivation, distinct from the published rate;
    - no statement or implication of endorsement;
    - the DTCC liability notice for SOFR;
    - on any republication beyond HIO (not in S1b), the notice "The [DATA NAME] is subject to
      the Terms of Use posted at newyorkfed.org." and the no-sanction, no-endorsement,
      no-liability disclaimer.

### 4.6 Third-party series: unavailable, not denied

- **WM/Reuters** (`FXRUSD`, and the F11 cross rates derived from it), **ASX** (`FIRMMBAB30D`
  and the other BAB tenors) and **FENICS** (OIS) are registered with `verification:
  unverified` and every permission **`unknown`**.
  - The record notes: "RBA copyright §7.2: use requires the third party's consent; no consent
    evidence".
  - **`unknown` means absent or unverified evidence. It is not an explicit `deny`.**
  - The gate refuses both, so these series are **unavailable** for every operation, including
    retaining a sample.
- **`deny` is recorded only when** a rights holder's terms or answer prohibit an operation
  outright.
- **Availability changes only through:**
  - a licence or written consent, recorded as `contract` or `owner_verified`;
  - or a substitute source chosen by the owner.

### 4.7 Q-010

- **The existing fail-closed behaviour is preserved unchanged.** Same-instant, equal-strength
  vintages of a key are a capture-clock conflict, and `as_captured_by_hio` suppresses the key
  (Q-002 r5).
- **No intra-receipt ranking is introduced.**
- S1b sources are declared **single-vintage per receipt**. The windows in §4.3 make every
  revision a later-captured vintage.
- **Proposed additional, additive check:** an S1b receipt that carries more than one vintage of
  a key is quarantined at ingest. It fails closed earlier and changes no S1a code path. The
  owner may decline it and rely on the suppression alone.
- **Q-010 stays open** for the first slice that ingests a genuine vintage archive.

## 5. S1b acceptance obligations: complete mapping

The obligations are revision 3's S1b acceptance (S10-B4) and inclusions (S10-B2), as detailed
in the implementation plan, plus its G2 evidence list.

**Legend:**
- **Retained**: unchanged, owed in each stage where it applies;
- **Staged**: discharged in the named stage;
- **Supersession proposed**: needs the owner's approval of this ADR, and is limited to the
  stated wording.

| Obligation | Class | S1b-1 | S1b-2 | Owed at S1b completion / G2 |
|---|---|---|---|---|
| S1-A1 independence (no `macsmsf` import, dependency, credential, network route) | Retained | yes | yes | yes |
| S1-A2 import rules; deliberate violation fails CI | Retained (with an adapters-only network exception, which needs explicit coverage in each stage's authorisation) | yes | yes | yes |
| S1-A3 write-once receipts; bucket versioning | Staged (versioning) | yes | inherits | yes |
| S1-A4 OBS-INV-001 vintages | Retained | cash series | FX series | yes |
| S1-A5 OBS-INV-002/003/007; the three modes | Retained | cash series | FX series | yes |
| S1-A6 OBS-INV-005, no UTC-derived `valid_time` | Retained | yes | yes | yes |
| S1-A7 cash legs exact (RA §3.2 fixtures; CASH-USD-INV-3/4; period `knowable_at`) | Staged | **yes**, on live data | — | yes |
| S1-A8 FXC-INV-1/2/4; RA-INV-007, RA-INV-016 | Staged | — | **yes** | yes |
| S1-A9 decomposition release | Staged | — | **yes** | yes |
| S1-A10a triangulation: FX RBA vs H.10 | Staged; **supersession proposed (wording)** only if the FX source is not RBA F11 (S10-B8 ii) | — | **yes**: the S1b-2 source against an independent FX publisher with `owner_verified` rights | yes. If no independent publisher's rights clear, reported **blocked**, not met |
| S1-A10b triangulation: USD cash vs bills (Treasury 4w, 13w) | Retained; independently gated (Treasury terms) | not required | not required | **yes**, or reported **blocked** |
| S1-A10c triangulation: AUD cash vs bills (RBA 1m BAB) | Retained; independently gated (ASX consent, or a substitute bill reference the owner approves; a substitute is itself a supersession needing an OD) | not required | not required | **yes**, or reported **blocked** |
| Index triangulations: AUD vs TRI, USD vs SOFR Index | **New** (added; substitutes for nothing) | **yes** | — | yes |
| S1-A11 rebuild reproduces `content_sha256`; releases §6.1 | Retained | yes | yes | yes |
| S1-A12 fail-closed rights on real sources, per operation | Retained; **per dataset** | D1–D4, D7–D9 | the FX source | yes |
| S1-A13 soak: ≥10 consecutive Sydney business days, punctuality, gaps, an alert on a failed run | Staged (two soaks) | **yes** (cash captures) | **yes** (FX captures) | yes |
| S1-A14 quality gates (quarantine; staleness) | Retained; plus the §4.3 rules 3 and 6, and §4.7's ingest check if adopted | yes | yes | yes |
| S1-A15 harness checks; handoff | Retained | yes | yes | yes |
| S1-A16 fresh-agent reproduction test | Retained | — | — | **once**, at S1b completion |
| S10-B2 "a cloud bucket with scoped keys" | Staged | **yes** | inherits | — |
| S10-B2 "scheduled capture" | Staged | cash sources | FX source | — |
| G2: `owner_verified` rights records for **all** S1 sources | Retained | its datasets | its datasets | yes, including each triangulation reference used |
| G2: release ids and hashes for the three factors and the decomposition; soak records; the three triangulation reports; an independent review; the fresh-agent record; STATUS; the handoff | Retained | partial | partial | **yes, all** |

**Nothing is deleted.** G2 cannot be claimed until both stages are complete and S1-A10a–c are
each met, or reported blocked and explicitly superseded by the owner in an OD that cites this
table.

## 6. Consequences

- **Capture can start on first-party cash sources** once S1b-1's gate is met, without any
  third-party consent.
- **S1's research output is unchanged in content.** It is delayed in part (S1b-2, the gated
  triangulations), and gains two index triangulations whose expected difference is about zero.
- **Two authorisations, two soaks and a separate FX-source decision.** The implementation
  plan's S1 stage mapping needs a matching update after approval, as a recommendation.
- **Forbidden by this ADR:**
  - substituting a publisher index for an S1-A10 triangulation without an explicit owner
    supersession;
  - using a series whose permissions are `unknown` or `deny`;
  - claiming `investable` for a cash benchmark;
  - any S1b change to S1a semantics.

## 7. Rollback or exit

- **Rejection** leaves revision 3 as the sole S1b definition.
- **Approval** is reversible before S1b-1 is authorised, by a further ADR.
- **After capture starts,** the stages can be merged again by finishing S1b-2 and the
  triangulations. Immutable receipts mean no evidence is discarded.
- **Reconsider if:**
  - an FX source is cleared before S1b-1 is authorised (merge the stages);
  - the S1b-1 rights cannot be verified (staging then buys nothing).

## 8. Evidence required before approval

1. The **independent review** of this exact revision, assigned by the owner
   ([draft assignment](HIO-ADR-0011-review-assignment-draft.md)).
2. The owner's answers to the matrix questions U1–U7. **Approving this ADR verifies no right.**
3. Confirmation that §3 holds: no change to the return mathematics, the observation invariants,
   evidence integrity, release integrity or the boundary.
4. The owner's renumbering decision for the equity ADR that earlier documents call
   "HIO-ADR-0011".

## Approval

_Unapproved._ (Set only by reference to an owner decision record: `OD-NNNN`, which approves or
rejects this file at commit `<sha>`.)

## Changelog

- 2026-10-25: drafted as "HIO-ADR-0010 revision 4 (proposed)" (OD-0046). Renumbered as a new
  ADR, HIO-ADR-0011, and revised (OD-0047):
  - the §2 provision-level supersession table;
  - §4.1 the funding-benchmark definition;
  - §4.3 the publication and revision windows;
  - §4.6 unavailable versus denied;
  - §5 the complete obligation mapping, with classes.
