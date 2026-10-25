---
id: HIO-ADR-0012
title: "Staged S1b live-observation implementation: S1b-1 official AUD and USD overnight cash benchmarks and publisher cash-return indices; S1b-2 FX and the AUD-investor USD cash excess return on a separately authorised FX source; further triangulations independently gated"
status: approved   # revision 3 approved by OD-0055. HIO-ADR-0010 rev 3 (OD-0011, 760f73e, blob 8ade1962cf28) stays approved and in force except the provisions listed in §2; S1b is NOT authorised
approved_by: OD-0055   # at d0965ccfd37a0ddefdbb5ff08a11674c3267792a, blob eb110ee394afa5b3a8abe612cf2e22196acbf51c
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
date: 2026-10-25
supersedes: [HIO-ADR-0010]   # IN PART ONLY (OD-0055): the HIO-ADR-0010 rev 3 S1b provisions S10-B2 and S10-B5, and the wording of S10-B8(ii) if its condition applies (§2); nothing else
superseded_by: null
gates: [S1b-1 authorisation, S1b-2 authorisation]
review_record: reviews/records/REVIEW-2026-10-25-adr0012.md   # received (OD-0050); verifications VERIFY-2026-10-25-adr0012-1 and -2 are unreceived Codex records on pushed branches (OD-0054, OD-0057)
drafted_under: [OD-0046, OD-0047, OD-0048, OD-0051, OD-0052]
revision: 3   # rev 1 = 1d68da3e90d879da6318082551bab943c60cf68b (REVIEW-2026-10-25-adr0012, REQUEST CHANGES); rev 2 = 860fd7879c6c663980bc4bf037a8c29e8c7df769 (VERIFY-2026-10-25-adr0012-1: F1 and F3 verified closed, F2 open); rev 3 corrects F2 only
evidence: [docs/evidence/S1B-readiness-assessment.md, docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md, docs/research/T-0002-owner-verification-matrix.md]
---

# HIO-ADR-0012: staged S1b live-observation implementation

> **Approved (revision 3, OD-0055).** It supersedes **only** the HIO-ADR-0010 revision 3 provisions
> marked "superseded" in §2, and every revision 3 S1b obligation is kept and re-mapped (§5).
> HIO-ADR-0010 revision 3 is otherwise in force. S1a acceptance (OD-0042) is unchanged. **S1b-1 and
> S1b-2 are not authorised**, and Q-013, the release-manifest schema, publisher header semantics,
> source permissions and the network and credential controls are not decided by this approval.

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
   - no backfill presented as captured;
   - S1b may **add** record types (the capture-attempt records, §4.3.3). It may not change the
     meaning or write behaviour of an existing one, including `capture()`.
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
| **Entry gate** | (a) S1a accepted (done, OD-0042); (b) **`owner_verified` rights for each S1b-1 dataset × each operation it performs** ([matrix](../research/T-0002-owner-verification-matrix.md)); (c) cited RITS, SIFMA and NSW calendars; (d) publication timing evidenced and the spec patches applied: AUD regime "in arrears", RITS selection, the §4.1 wording, the windows in §4.3; (d2) header and payload timestamp semantics evidenced per dataset, or that evidence declared unavailable (§4.3.1); (d3) Q-013 decided (§4.3.1); (e) the network and credential-control decision (OD-0038); (f) the bucket and keys decision, including a provider-assigned write timestamp for stored objects (§4.3.3, C5); (g) the owner's S1b-1 authorisation of scope and infrastructure | (a) S1b-1 authorised; (b) the **FX-source decision**, with `owner_verified` rights for that source × every operation; (c) publication timing, calendar, timestamp semantics (§4.3.1) and revision window (§4.3.4) for it; (d) the FX spec re-versioned if the source is not RBA F11 (quote convention per RA-INV-007); (e) the owner's S1b-2 authorisation | per triangulation: `owner_verified` rights for its reference; a cited calendar; a methodological-suitability note with a pre-registered expected-difference model; an owner instruction |
| **Excludes** | FX; equity, bonds, futures; any `smsf_*` distribution | the same, apart from FX | — |

### 4.3 Placing a vintage in time; publication and revision windows (both stages)

**Revision 2 (OD-0051).** Revision 1 treated the documented publication time as the time a
vintage became public. The independent review found that unsafe: a publisher may defer
publication, and some series are published "shortly after" a stated time (REVIEW-2026-10-25-adr0012,
F1). A schedule is an **expectation**. It is not vintage evidence (observations §3: "A schedule is
not vintage evidence").

For each dataset, the spec declares the publisher's documented schedule:

| Dataset | Documented publication P_doc | Documented window close W_doc | Evidence |
|---|---|---|---|
| `rba.cash_rate` (AONIA), `rba.cash_rate_tri` | before 09:20 Sydney, on the next RITS day after the rate's day b (the TRI is dated by its publication day); the RBA may defer | 16:00 Sydney on that day ("will not revise" after) | RBA cash-rate methodology, last updated 21 July 2026; deferral per the review record, F1 |
| `nyfed.sofr` | about 08:00 ET on the next SIFMA day | about 14:30 ET on that day, only if the rate moves by more than 1 bp | NY Fed reference-rate information, last updated 10/5/2026 |
| `nyfed.sofr_index` | "shortly after" SOFR, about 08:00 ET (dated by its publication day) | about 14:30 ET on that day; **also** for an error in the Index calculation, whether or not SOFR was revised (see §4.3.5) | the same page, as cited by the review record, F3; to be evidenced at the S1b-1 gate |
| FX | per the S1b-2 source | per the S1b-2 source | S1b-2 |

**P_doc and W_doc are used only to:** schedule captures and checks, define staleness, and define
the finality window (§4.3.4). **They are never, on their own, the `knowable_at` of a vintage.**

#### 4.3.1 Placing a vintage (first appearance and revision alike)

| Rule | Condition | `knowable_at` | `knowable_basis` |
|---|---|---|---|
| **P1 evidenced instant** | the receipt carries this vintage's own publication instant, in the payload or in response headers that the adapter records **unaltered** in the receipt metadata, **and** that instant is ≤ the vintage's `captured_at` | that instant | `publisher_timestamp` (observations §3 allows "payload or headers") |
| **P2 capture-time basis** | no P1 evidence | `captured_at` of the **first capture that contains the value**: the earliest instant HIO can prove it was public. It may be later than the true publication, never earlier | `captured_on_schedule` |
| **P3 fail-closed fallback** | P2 is not available (Q-013 undecided or declined) | the documented release instant, labelled as such | `schedule_only`: **excluded from `as_known_by_market`**; usable through `as_captured_by_hio` and `reconstructed(T)` |

**Conditions and consequences:**
- **P1 is available for a dataset only after its timestamp semantics are evidenced** at the S1b
  gate: what event the header or field times, that it is stable across requests, and that
  intermediaries do not skew it. Until then the dataset uses P2, or P3 if P2 is unavailable.
- A P1 instant **later** than `captured_at` is evidence of a clock or semantics fault. The vintage
  is **quarantined**, not placed.
- **Current evidence (2026-10-25 samples):**
  - the `nyfed.sofr` and `nyfed.sofr_index` API payloads carry **no** publication timestamp, and
    their header semantics have not been examined, so they would use P2 or P3;
  - the RBA CSV's "Publication date" row is a **date**, not an instant, so an RBA dataset needs
    header evidence for P1.
- **P2 uses the reading the accepted S1a code already applies to a revised value.**
  `src/hio/marketdata/knowability.py:51-52` gives a scheduled capture that sees a revised value
  `captured_on_schedule` with `knowable_at` = the capture instant ("HIO's own capture is the only
  evidence"). **The approved observations standard §3 defines `captured_on_schedule` as the
  "documented release time preceding that capture" and does not state this reading.** Extending
  it to first captures is therefore a **clarification of approved observation semantics**, and it
  needs a change to the accepted S1a placement behaviour (an opt-in S1b mode that leaves default
  behaviour, and so every S1a release, unchanged). **Both are escalated as Q-013 and are not
  decided here.** The S1b-1 gate (d3) requires Q-013 to be decided. If it is declined, P3 applies.
- **Q-004** (is a late first capture market evidence?) has no effect under P2, because the
  capture instant is used however late the capture is. It stays open for P3.

#### 4.3.2 Revisions and out-of-window changes

- A revision is a vintage like any other: it is placed by P1–P3 at its own capture. **No rule
  sets `knowable_at` to W_doc.**
- A material attribute change, such as SOFR's `revisionIndicator`, also makes a new vintage.
- **Out-of-window change.** A value that differs from a vintage already final (§4.3.4) for the
  same key becomes a new vintage (never an overwrite). It is logged and **quarantined pending
  owner review**, by a series-specific quality rule. This is additive: the observations §6 gates
  are a minimum.
- **Expert-judgement days.** An AONIA type-A day repeats the last rate by design. It is flagged
  from `rba.expert_judgement` and must not trip staleness.
- **Gaps and backfill.** A missed run is a recorded capture gap. A backfill is a single
  current-value receipt, `schedule_only`, usable only through `reconstructed(T)`.

#### 4.3.3 Capture-attempt records: completion evidence (additive)

**What this evidence can and cannot show.** A final check must show that a request was made,
that a response generated after W_doc was received, and that it was examined and matched to the
held value. **No self-recorded event can cryptographically prove network activity.** The capture
adapter makes the request, the same adapter writes the record, and the store that holds it is
HIO's own. A record can be internally consistent, can be checked against artefacts HIO retains,
and can be audited against witnesses outside HIO's bookkeeping. By itself it cannot prove that a
request happened. This section states what is replayable, what is witnessed, and what is simply
trusted, and it refuses finality unless every required check passes.

**Trust assumption (already implicit, now explicit).** The S1b capture adapter, running the pinned
`code_ref` in a scheduled or dispatched workflow on `main`, is a **trusted component**. HIO already
trusts it to write receipts and capture records honestly; this ADR claims nothing stronger.

**No second bookkeeping system.** The design adds one record type, written the same way as the
existing catalogue records, and validates it against artefacts and witnesses that already exist
(the retained receipt, the publisher's own response headers, the CI platform's run record, the
object store's write timestamp). It adds **no** signature scheme, hash chain, ledger or second
store. Those would move the same trust to a key or system held by the same adapter. Any such
mechanism would be a **trust-model change** and is not proposed here.

**The record.** Every capture run for a dataset writes exactly one write-once record at
`catalogue/attempts/<source_id>/<attempted_at>-<record_sha256>`, where `record_sha256` is the
SHA-256 of the record's canonical content. **On read the hash is recomputed and compared with the
key**, as for the other content-addressed records (S1-A3).

| Field | Content |
|---|---|
| `execution` | `platform`, `run_id`, `run_attempt`, `job`, and `sha` (the commit the run executed), copied **unaltered** from the CI environment. A run outside the scheduled or dispatched capture workflow on `main` records `platform: other` |
| `request` | method and the URL configured for the dataset |
| `response_envelope` | status; `Date`; `Age`, `Last-Modified` and `ETag` if present; `Content-Type`; `Content-Length`: as received, unaltered |
| `response_sha256`, `response_bytes` | the hash and length of the body read |
| `attempted_at`, `completed_at` | HIO's clock at the start of the request and when the body was fully read |
| `outcome` | `verified_changed`, `verified_unchanged` or `failed` |
| for a verified outcome | the `receipt_id` the body matches (a new capture, or the held capture whose bytes hash equals `response_sha256`); the keys checked, each with a digest of the value found |
| for `failed` | an error class (network, HTTP status, parse, schema, hash mismatch, key missing). No bytes |

**Completion checks.** A record is completion evidence only if **all** of these pass. Any failure,
or any missing field, makes it **not evidence** (fail closed).

| Check | Rule | Kind |
|---|---|---|
| **C1 integrity** | the key's hash matches the recomputed content hash; the object is the stored version, never rewritten | replayable |
| **C2 response binding** | `response_sha256` equals the referenced receipt's id, and re-hashing that receipt's stored bytes reproduces it | replayable |
| **C3 content** | parsing the stored bytes under the series schema reproduces each `keys_checked` digest, and each equals the digest of the held vintage's value for that key (for `verified_changed`, the new vintage) | replayable |
| **C4 freshness** | `Date` is present and parses, `W_doc(k) ≤ Date`, and `−ε ≤ completed_at − Date ≤ δ`. `Date` is the origin server's clock at generation, so a cached copy generated before the window fails even if it was fetched after it | publisher's clock, recorded unaltered |
| **C5 timing** | `W_doc(k) ≤ attempted_at ≤ completed_at`, and the object store's **provider-assigned write time** `s` satisfies `completed_at ≤ s ≤ completed_at + δ`. If the store cannot supply a provider-assigned write time, C5 fails | witnessed by the store provider |
| **C6 execution binding** | `execution.platform` is the CI platform, `sha` equals the pinned adapter `code_ref`, and the run identifiers are well formed. At build time this is checked for presence, format and consistency | witnessed by the CI platform (audit below) |
| **C7 uniqueness** | at most one record exists for the same (`platform`, `run_id`, `run_attempt`, `source_id`) | replayable |

δ and ε are declared per dataset in its spec. This ADR proposes δ = 10 minutes and ε = 2 minutes.

**Which evidence is which.**
- **Replayable from retained artefacts alone:** C1, C2, C3, C7, and the arithmetic of C4 and C5.
  A verifier needs only the stores.
- **Witnessed outside HIO's bookkeeping:**
  - the publisher's `Date` (C4);
  - the store's write time (C5);
  - the CI run record (C6), which the owner or an auditor can check against the platform's run
    history. This audit is required for a sample of runs in the soak (S1-A13) and for any release
    the owner promotes beyond exploratory use.
  - the value itself: the publisher documents no revision after W_doc, so **any later genuine
    fetch must return the same value**. That re-checks the content of a "final" claim, not the
    time of the original request.
- **Trusted-adapter assertions, not replayable:** that the request was actually sent; that the
  envelope is the response's; and that `attempted_at` and `completed_at` are truthful.

**The unchanged-response case.** Identical bytes cannot prove that a request was made, or when:
a record can reuse the held receipt's hash and length. An unchanged completion is therefore
accepted **only** through a fresh envelope (C4) together with C5–C7, with C2 and C3 showing that
the bytes equal the held receipt's. The forged case raised in the review (a `verified_unchanged`
record copying R's hash and length, with no request after W_doc) passes C1–C3 and **fails C4**,
because the genuine response carried a pre-window `Date`. To pass, the adapter would also have to
fabricate a post-window `Date`, write the record at a matching time (C5) and name a CI run that
exists (C6). That is the stated trust limit, and an audit against the CI run history and a later
genuine fetch can expose it.

**Constraints.**
- **`capture()` is unchanged.** It remains the only writer of receipts and vintages, and an
  identical consecutive re-fetch **still writes no capture record**
  (`src/hio/marketdata/capture.py:98-99`). The attempt record is the durable evidence that such a
  check happened.
- An attempt record is evidence of a **check**, never of **publication**. It never creates or
  changes an observation, a vintage or a `knowable_at`.
- Source-by-source evidence that `Date`, `Age` and the store's write time behave as assumed is a
  gate item (§4.2 (d2) and (f)). Where it cannot be evidenced, the dataset has **no finality**.

#### 4.3.4 Finality (fail closed)

A vintage v of key k in a dataset is **final at cutoff C** if and only if all of these hold:
1. an attempt record r exists with outcome `verified_changed` or `verified_unchanged`, covering
   k, that passes **C1–C7**, with `W_doc(k) ≤ r.attempted_at` and `s(r) ≤ C`;
2. r's value for k equals v's value (C3); and
3. no later vintage of k has `captured_at` ≤ C.

**Refused (not evidence for that cutoff):**
- **Missing:** no record, or a required field absent.
- **Failed:** a `failed` record, or a verified record whose parse, schema or key check failed.
- **Delayed:** a check made before W_doc, or one completed or stored after C. A check after C may
  support a **later** cutoff.
- **Inconsistent:** any of C1–C7 failing; two records for the same dataset and window that
  disagree about a key's value, which are also quarantined pending owner review; or two records
  claiming the same execution.
- **Unverified:** a record from a run with `platform: other`, a manual or local run, or a dataset
  whose header and write-time behaviour has not been evidenced.

An attempt alone establishes nothing. A **release is final only if every input vintage it uses is
final at the release's `knowledge_cutoff`**. Otherwise it is exploratory and identified by its
recorded cutoff. The evidence record ids are recorded among the release's inputs, so that they
fall inside its content identity. If the manifest schema cannot carry them without an amendment of
the releases standard, that is **escalated**, not decided here.

**If a "final" claim is later contradicted.** A later genuine fetch that returns a value other
than v, or an audit that finds no matching run, triggers the out-of-window rule (§4.3.2). Releases
that relied on v are then withdrawn or deprecated by an owner-recorded status event under
HIO-ADR-0006. No new mechanism is introduced.

**Worked cases.**
- *The review's original case (F2).* AONIA is revised at 15:50 Sydney, W_doc is 16:00, the final
  check runs at 16:30, and a build at 16:10 has no record with `attempted_at ≥ 16:00` and
  `s ≤ 16:10`, so it is **not final**. After a `verified_changed` check at 16:30, a build with a
  cutoff after the store's write time is final.
- *A cached response.* The check runs at 16:05, but the response carries `Date` 15:58 and
  `Age: 420`. C4 fails because the content predates W_doc, so the check does not count and is
  retried.
- *A forged completion (the verification's counterexample).* Refused at C4, as above.

#### 4.3.5 Independent checks per dataset (SOFR and the SOFR Index)

Each dataset has its own captures, attempt records, vintages and finality: `rba.cash_rate`,
`rba.cash_rate_tri`, `nyfed.sofr` and `nyfed.sofr_index`.

- **A verified post-window check is required for every dataset**, whether or not its sibling
  changed and whether or not `revisionIndicator` shows a revision.
- **SOFR revision rule:** a revision only if the rate moves by more than 1 bp, marked by
  `revisionIndicator`.
- **SOFR Index revision rule:** a revision at about 14:30 ET **also** for an error found in the
  Index calculation, with no SOFR revision. Revision 1 grouped the Index under the SOFR rule,
  which is wrong (F3). **This is the reviewer's citation of the NY Fed page, not independently
  re-read by the author; the S1b-1 gate requires it to be evidenced** (timing evidence, gate (d)).
- **Dependence:**
  - `cash.usd.overnight` is final on SOFR checks only;
  - the SOFR Index triangulation (§4.4) is final only if both SOFR and Index are final at its
    cutoff;
  - an Index-only correction creates a new Index vintage and does not change `cash.usd`.

**Capture schedule.**
- Each dataset has a **first check** shortly after P_doc and a **final check** after W_doc:
  - AONIA and TRI at about 09:45 and about 16:30 Sydney;
  - SOFR and SOFR Index at about 08:30 and about 15:00 ET.
- Jobs fire on several UTC cron slots, and act only when the local P_doc or W_doc is due, because
  the Sydney and New York daylight-saving switches move independently. Idempotence makes the extra
  runs no-ops.
- A final check that fails is retried within the day. If no verified check exists by the next
  publication day, the affected releases stay exploratory and the miss is recorded as a gap.
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
- S1b sources are declared **single-vintage per receipt**. Under §4.3 every revision becomes a
  later-captured vintage from a separate capture, never an intra-receipt vintage.
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
| S1-A14 quality gates (quarantine; staleness) | Retained; plus the §4.3.2 out-of-window quarantine and expert-judgement rule, the §4.3.1 later-than-capture quarantine, and §4.7's ingest check if adopted | yes | yes | yes |
| Capture-attempt records and finality evidence (§4.3.3–§4.3.4; remediates F-REVIEW-2026-10-25-adr0012-2) | **New** (additive; `capture()` unchanged) | **yes** | **yes** | yes |
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
  - using a documented schedule as the evidence of when a vintage became public;
  - calling a release final without verified post-window evidence (§4.3.4);
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
   ([draft assignment](HIO-ADR-0012-review-assignment-draft.md)).
2. The owner's answers to the matrix questions U1–U7. **Approving this ADR verifies no right.**
3. Confirmation that §3 holds: no change to the return mathematics, the observation invariants,
   evidence integrity, release integrity or the boundary.
4. The owner's disposition of **Q-013** (§4.3.1), which concerns the approved observation
   semantics and the accepted S1a placement behaviour. Approving this ADR does not decide it.
5. **F-REVIEW-2026-10-25-adr0012-1 and -3** were independently verified closed as design corrections by VERIFY-2026-10-25-adr0012-1 (reviewer commit `e1f60f9e04034c5b9cb21ac8b3c77b93afc516ce`, not yet received). **F-REVIEW-2026-10-25-adr0012-2** needs scoped re-verification by Codex at the new head.

## Approval

Approved by [OD-0055](owner/OD-0055-approve-adr-0012-rev3.md), revision 3 at commit
`d0965ccfd37a0ddefdbb5ff08a11674c3267792a`, file blob `eb110ee394afa5b3a8abe612cf2e22196acbf51c`
(2026-10-25). The approval records status only; no text of §1–§8 was changed. It does not resolve
Q-013, the release-manifest schema, publisher header semantics, source permissions,
infrastructure controls or S1b authorisation.

## Changelog

- 2026-10-25: **revision 3 approved** (OD-0055). Status-only edit: front matter `status`,
  `approved_by`, `supersedes`, the opening banner and this section. No policy text changed.
- 2026-10-25: drafted as "HIO-ADR-0010 revision 4 (proposed)" (OD-0046). Renumbered as a new
  ADR, HIO-ADR-0011, and revised (OD-0047):
  - the §2 provision-level supersession table;
  - §4.1 the funding-benchmark definition;
  - §4.3 the publication and revision windows;
  - §4.6 unavailable versus denied;
  - §5 the complete obligation mapping, with classes.
- 2026-10-25, **revision 3** (OD-0052): corrects **F-REVIEW-2026-10-25-adr0012-2 only**, after VERIFY-2026-10-25-adr0012-1
  (F1 and F3 verified closed, F2 open on a forged `verified_unchanged` counterexample):
  - §4.3.3 rewritten as completion evidence: an execution-bound record, seven completion checks
    (C1–C7), the replayable / witnessed / trusted split, an explicit statement that self-recorded
    events do not prove network activity, and the unchanged-response case;
  - §4.3.4 finality now requires C1–C7, and lists what is refused;
  - §4.2 gate (f) and §8 item 5 adjusted. §4.3.1 and §4.3.5 (F1 and F3) are not reopened.
- 2026-10-25, **revision 2** (OD-0051): remediates the three findings of REVIEW-2026-10-25-adr0012
  (see `reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-1.md`):
  - §4.3 rewritten as §4.3.1–§4.3.5: placing a vintage by evidenced instant, capture time or the
    fail-closed fallback; additive capture-attempt records; finality by verified post-window
    evidence; independent per-dataset checks;
  - §3, §4.2, §4.7, §5, §6 and §8 adjusted accordingly;
  - Q-013 raised. Nothing else is changed: §2's supersession table, §4.1, §4.4–§4.6 and the
    stage structure are as reviewed.
- 2026-10-25: renumbered **HIO-ADR-0012** by the owner (OD-0048). HIO-ADR-0011 stays reserved for
  the equity total-return source decision (T-0003). The numbering note and the renumbering item in
  §8 are removed. No substantive change.
