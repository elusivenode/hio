---
id: HIO-EVIDENCE-S1B-READINESS
title: S1b readiness assessment (rights, timing, controls, Q-010, first output; not authorisation)
status: prepared_for_owner   # NOT authorisation; S1b is not authorised (HIO-ADR-0010 rev 3; OD-0042)
owner: implementation agent (prepared); owner (decides)
created_at: 2026-10-25
authorised_by: [OD-0044]
evaluated_revision: 1f5e5e29960ecb0bd07fa82f68e312b4cc80664b   # main when the assessment was made
method: >-
  Repository documents only. No real data fetched, no publisher page re-read, no vendor
  contacted, no infrastructure or credential created. Every external fact below is quoted from
  the T-0002/T-0003 research as retrieved on 2026-10-18 and is [EXT], unverified.
---

# S1b readiness assessment

> **Prepared for the owner. S1b is not authorised, and nothing here authorises it.** It assesses
> what S1b needs under [HIO-ADR-0010 rev 3](../decisions/HIO-ADR-0010-first-slice-scope.md)
> (S1b entry gate) and what is still missing. Inputs: ADR-0010 rev 3; the
> [T-0002 research](../research/T-0002-source-rights-and-timing.md) and
> [`registers/sources.yaml`](../../registers/sources.yaml); the
> [T-0003 scorecard](../research/T-0003-equity-total-return-sources.md); the three S1 specs
> (`specs/factors/*`, v0.2.0); the S1a implementation at `084154c`; the
> [open-decisions register](../decisions/open-decisions.md).

## 0. Summary

**Recommendation.** S1b is **not ready to authorise**. Every source permission is still
`unverified` (OD-0013), so the S1a rights gate correctly refuses every real operation.

The shortest safe path:
1. **Stage S1b so the capture clock starts on the two publishers that the primary factor
   needs**: RBA (cash rate, F11 AUD/USD) and the NY Fed (SOFR).
2. **Add Treasury bills, FRB H.10 and the RBA bank-bill rate when their rights clear.** They
   only feed the triangulations, and those can use history later.
3. **Replace the bill-based cash triangulations with publisher indices** (the RBA Cash Rate
   TRI and the NY Fed SOFR Index). These have an expected difference of about zero, so they
   are a sharper financial check.

Steps 1 and 3 **change HIO-ADR-0010 rev 3's S1b scope**, which names four sources and three
triangulation reports. So they are **escalated** (§8), not assumed.

**The next owner decision:** the T-0002 verification of RBA and NY Fed rights, per dataset and
per operation (§1). Recording it needs a one-off manual sample per dataset, which T-0002 allows
but which this instruction excluded. The ADR-0010 staging question (§8, E1) should be decided
alongside.

## 1. Rights evidence still needed, per source and operation

**The rule** (rights standard §3): every S1b operation checks every input source for its
required permissions. `unknown` and `unverified` refuse. Each permission the owner verifies must
record its value, the clause, URL and retrieval date, the verifier, and a `review_due` date
(standard §1). A `conditional` also needs the condition and how it is satisfied (for example,
the attribution string written into every release manifest).

**S1b operations and the permissions they need** (all S1b jobs run on a CI runner and a cloud
bucket, so `external_processing` is required by every one):

| S1b operation | Permissions |
|---|---|
| fetch (scheduled capture) | `automated_retrieval`, `external_processing` |
| store raw (bucket) | `raw_retention` (with its duration), `external_processing` |
| build | `internal_compute`, `derivation`, `external_processing` |
| store derived | `derived_storage`, `external_processing` |
| rebuild (CI) | as build and store derived, plus `raw_retention` still valid |
| publish to `hio_internal` | `distribution.hio_internal` |
| agent review of values (optional) | `agent_context`; otherwise agents see ids and hashes only (standard §4) |

**What each dataset still lacks.** The 2026-10-18 findings are proposals only (OD-0013).

| Dataset (S1b use) | Missing evidence | What would resolve it |
|---|---|---|
| **RBA cash rate (AONIA)**: `cash.aud.overnight` | `automated_retrieval`: the RBA terms are silent. `internal_compute`/`derivation` are conditional on "no implied endorsement" under the separate "Cash Rate" clause | an owner judgment, with reasoning, that silence plus CC BY suffices, or a written RBA answer; the condition text recorded, and how releases satisfy it |
| **RBA F11 AUD/USD 4pm**: `fx.usd_cash_vs_aud.excess` | `automated_retrieval` silent. The page caveat "not … relied upon for regulatory or commercial purposes" is not interpreted | the same retrieval judgment; an owner reading that HIO's internal research is neither regulatory nor commercial reliance; the attribution text |
| **RBA Cash Rate TRI** (proposed triangulation) | not researched: is it "Cash Rate" or "Financial Data"? Is it automated? | read its terms and table notes (T-0002 scope) |
| **RBA F1 1m BAB** (ADR triangulation) | its **source is undetermined**. If it is ASX BBSW, it is third-party material needing ASX consent | the table notes inside the data file: one manual sample. Or drop it (OD-0013 item 2) |
| **NY Fed SOFR and SOFR Index**: `cash.usd.overnight` | none of substance: the terms allow automated access, storage, derivation and redistribution, with labelling. Only the owner's verification is missing, and SOFR's DTCC inputs need no separate consent under those terms | owner verification against the live page (last updated 9 June 2023) |
| **US Treasury bills** (ADR triangulation) | **no terms located.** The 17 U.S.C. §105 presumption is not evidence for this data. Posting time not stated | a located terms statement, or an owner decision to rely on §105 with reasoning |
| **FRB H.10** (ADR triangulation) | `automated_retrieval` silent; the Data Download Program is retiring in favour of FRED (other terms, an API key) | an owner decision: keep H.10 (and through which channel), or replace it (T-0002 question 4) |

**One code gap, not a standard change.** The standard allows per-dataset rights "where terms
differ" (§1). The accepted gate (`src/hio/rights/register.py`) reads rights **per source**, and
RBA's datasets differ. The S1b design should register them as **separate source ids**, for
example `rba.cash_rate`, `rba.f11` and `rba.f1`. That needs no change to accepted S1a code.

## 2. Publication timing, observation calendars and the AUD cash-rate regime

**Timing, converted to UTC.** The conversions below are this assessment's own arithmetic from
the T-0002 times. Sydney is UTC+11 (AEDT, October to April) or UTC+10 (AEST); New York is
UTC−4 (EDT, March to November) or UTC−5 (EST). The two daylight-saving switches fall on
different dates, so the offset between the cities moves twice a year.

| Series | Published | Final | Calendar | `knowable_at` for a captured vintage |
|---|---|---|---|---|
| AONIA for RITS day b | before 09:20 Sydney on the next RITS day | 16:00 Sydney that day (republication window) | **RITS** days | the publication before 09:20; **finality** shown by a second capture after 16:00 |
| F11 AUD/USD for day t | about 17:00 Sydney on t (indicative; no time zone stated) | revisions "rare" [EXT] | NSW business days (weekdays except NSW public and bank holidays) | **the publication (~17:00), not the 16:00 fixing.** The S1 spec says "about 4pm"; that should be patched to the later instant |
| SOFR for NY day b | about 08:00 ET on the next SIFMA day | after the 14:30 ET revision (only if >1bp) | **SIFMA** US government securities | about 08:00 ET; finality shown by a capture after 14:30 ET |

**The binding instant is SOFR.** For a period (t−1, t] in AEDT/EDT:
- the AUD leg uses AONIA for t−1, published by about 09:20 on t;
- the spot uses F11 at about 17:00 on t;
- the USD leg uses SOFR for NY t−1, published about 08:00 ET on NY day t, **about 23:00
  Sydney on t**, and final about 05:30 Sydney on t+1.

So `X_t` is first knowable late on Sydney day t. That is exactly what CASH-USD-INV-4 and the
FX spec's period `knowable_at` require.

**The open RBA question (4pm "AEST" in daylight saving) does not block point-in-time
correctness.** `knowable_at` is set from the publication and the capture, never from the fixing
time. If an instant is uncertain, use the **later** candidate: that can only understate
knowability, never look ahead. The question still matters for the H.10 expected-difference model,
because the fixing-time gap to New York noon changes by an hour. The answer can be inferred from
captured data, or asked.

**Calendars are reference data with sources of their own.** S1b needs three calendars:
- **RITS**, for AONIA rate selection;
- **NSW**, for the F11 fixings and the joint calendar J;
- **SIFMA**, for SOFR.

Each needs a cited holiday list, committed with its evidence before capture starts. Otherwise
the S1a completeness and staleness gates cannot run. SIFMA's holiday recommendations are a
SIFMA publication with its own terms.

**A spec/standard alignment issue, not a change to the mathematics.** RA §3.2 step 2 selects
"the latest business day b ≤ d **of that rate's market**". `cash.aud.overnight` v0.2.0 declares
"XSYD business days". If RITS days and NSW days ever differ, the spec as written would select the
wrong rate, or find none. The fix is a spec patch to the RITS calendar for rate selection, with a
version bump if numbers change. It needs no change to the standard.

**The AUD cash-rate regime is in arrears** (RA §3.2 step 4). AONIA for day b is a measured
outcome of day b's transactions, published the next morning. The consequences:
- `investability: replicable_with_basis` (already declared);
- the period `knowable_at` is the AONIA publication on t, final at 16:00;
- the cash-rate **target** is a different series, known in advance, and must not be
  substituted.

The spec patch that T-0002 R4 anticipates should state "in arrears". Open evidence:
- how the RBA publishes on a low-volume day (the methodology fallback);
- the earliest history, recorded at first capture.

## 3. Controls: network, credentials, storage, scheduled capture

**Scope.** S1b's sources are public and keyless [EXT]. The proportionate aim is to contain blast
radius and keep evidence honest, not enterprise isolation. Two facts shape the controls:
- **the repository is public** (OD-0019), so GitHub Actions logs are public;
- Q-008 accepted "no egress firewall" **for S1a only**.

**Network.**
- Network code only in a new `hio.marketdata.adapters` package. CI enforces this and keeps
  blocking sockets everywhere else, so S1a's import rule becomes "only adapters may import a
  network client".
- Prefer the standard library's `urllib` to a new dependency, which would otherwise need a
  ratification like Q-007.
- A per-source host allow-list in code; off-list redirects refused; HTTPS only; a size cap and
  timeout.
- A separate capture workflow whose only network use after install is the adapters. Actions
  pinned by commit SHA.
- A runner egress firewall is **not** recommended: it needs a third-party action, a new
  supply-chain dependency, for little gain on keyless public sources. Record this as the S1b
  successor to Q-008.

**Credentials.**
- **No data-source credentials** (all keyless). If H.10 needs FRED, its key is a separate owner
  decision.
- **One bucket write key**, scoped to the HIO bucket only, held in a GitHub *Environment*
  limited to `main`, used only by `schedule` and `workflow_dispatch` jobs. Never
  `pull_request_target`; no secret reaches a fork-PR workflow.
- **One read-only key**, held by the owner locally.
- Rotation on a stated cycle (for example 90 days), and a secret-pattern check on logs.
- No `macsmsf` credential is ever present (S1-A1).

**Storage.**
- **One dedicated bucket**, not `macsmsf`'s, with versioning on (S1-A3). Write-once enforced by
  code, as in S1a; object lock if the provider has it [EXT].
- An Australian or nearby region; no lifecycle deletion.
- A **second copy off the provider** (for example a periodic owner-local sync), because the
  bucket becomes the only system of record for captured days.
- Nothing from receipts in git or in logs: logs carry hashes, counts and ids only.

**Scheduled capture.**
- Two captures per series per day: **first** after publication, **final** after the revision
  window:
  - AONIA: about 09:45 and about 16:30 Sydney;
  - F11: about 17:30 and about 19:00 Sydney;
  - SOFR: about 08:30 and about 15:00 ET.
- Cron runs in UTC and the daylight-saving switches move, so each job runs on several cron slots
  and decides in local time whether the release is due. Idempotence (OBS-INV-001) makes extra
  runs harmless.
- GitHub cron is best-effort, and is disabled in public repositories after 60 days without
  activity [EXT]. So add a staleness check that alerts (S1-A13), record capture gaps as gaps
  (observations §5), and apply the architecture §5 punctuality trigger and the plan's 20% stop
  condition.

## 4. Q-010: archive receipts on the capture clock

**The issue.** One receipt holding several vintages of a key gives them the same `captured_at`
and equal basis strength. Under the approved ranking (Q-002 r5), that is a capture-clock
conflict, so `as_captured_by_hio` suppresses the key. This fails closed.

**Assessment.** S1b's planned sources do not produce such receipts:
- SOFR and AONIA revise only within the same day;
- each capture returns the current value;
- a revision is seen as a **second capture with a later `captured_at`**, which is a new vintage
  and not a conflict.

The two-capture schedule in §3 is what makes this hold. A history backfill is a single receipt
with one value per key (`schedule_only`), so it is not a multi-vintage archive either.

**Recommendation: keep the approved behaviour unchanged for S1b.** In the S1b design:
1. declare every S1b source **single-vintage per receipt**;
2. **quarantine** at ingest any S1b receipt that carries more than one vintage of a key. This is
   additive S1b code; it uses the existing quarantine path and changes no S1a behaviour;
3. carry Q-010 forward to the first slice that ingests a real vintage archive (ALFRED, or
   publisher vintage files).

**Escalated, not proposed here.** Any rule that ranks vintages *within* a receipt on the
capture clock would amend the approved observations standard (Q-002 r5). For example, such a
rule might credit `as_captured_by_hio` with only the archive's latest vintage, or order by the
archive's own dates. None of this weakens OBS-INV-001…007, and none is needed for S1b.

**Related:** **Q-004** (is a late first capture market evidence?) does arise in S1b, through
missed or late runs. Proposed S1b default:
- a capture after release plus `capture_grace` keeps `captured_at` as fact;
- it does **not** claim `captured_on_schedule`;
- so it is absent from `as_known_by_market` unless other evidence exists.

This is the approved standard's current reading. The owner should confirm it.

## 5. Minimum first live-data research output and its validation

**Output.** `hio_internal` releases at `as_captured_by_hio`, over the soak window, of:
- `cash.aud.overnight`;
- `cash.usd.overnight`;
- `fx.usd_cash_vs_aud.excess`, with its spot, carry and cross decomposition (S1-A9).

Also a **labelled `reconstructed(T)` history** from one backfill, for descriptive use only. No
trustee-pack or `smsf_*` distribution.

**Financial validation** (each test pre-registered with its expected-difference model; triangulations never pass or fail on agreement, S1-A10):

| Check | Expectation |
|---|---|
| FXC-INV-1/2 and RA-INV-016 on live data | exact, every period |
| AUD cash index vs the RBA **Cash Rate TRI** | about 0. Residuals explained only by rounding of the published rate and by day-count |
| USD cash index vs the NY Fed **SOFR Index** | about 0. The SOFR Index is ACT/360, compounded in arrears, from 2018-04-02. Residuals are only rounding (8 decimal places) and the date-label alignment limitation |
| Spot: RBA F11 vs H.10 (if kept) | ~0 mean; large daily and small weekly differences; missing-day patterns from the calendars |
| Carry sanity | annualised `carry_t` ≈ SOFR − AONIA (ACT/360 vs ACT/365F), sign consistent with the policy-rate differential |
| Quote convention | F11 is USD per AUD; `s_t = q_{t−1}/q_t − 1` (RA-INV-007) checked on a rising and a falling day |
| Knowability | the period `knowable_at` equals the SOFR publication instant (CASH-USD-INV-4); no release uses a vintage captured after its cutoff (OBS-INV-002) |
| Calendars | the period count over the soak equals J's business days; every holiday and weekend handled as in the RA §3.2 fixtures |
| Operations | ≥10 consecutive Sydney business days unattended (S1-A13); punctuality distribution; ≤20% misses (stop condition 2); rebuild reproduces every `content_sha256` (S1-A11); S1a's four `data.csv` hashes unchanged |

## 6. Contribution to the factor-based portfolio-construction framework

- **Financing legs.** Every later excess return is measured over these cash legs: equity (S2),
  government bonds (S3) and futures collateral (S4). Without them, S2–S4 cannot state an excess
  return honestly (RA §1).
- **The currency building block.** For an AUD investor, USD exposure is the largest unmanaged
  exposure (FX spec rationale). `fx.usd_cash_vs_aud.excess` turns unhedged versus hedged foreign
  equity into an explicit, decomposed exposure. It is the input to any hedge-ratio research and
  to H-0002 (AUD defensiveness).
- **Exposure before vehicle** (charter §3.7). The outputs are exposures, not funds. A future
  mandate (portfolio-construction context) allocates risk to them; vehicle mapping comes later.
- **The capture clock.** Year-4 tactical research is limited to captured or publisher-vintage
  data (charter §6). Every day before S1b starts is lost evidence for carry and state signals.
  That is the one irreversible cost of delay.
- **The SMSF boundary.** S1b publishes only to `hio_internal`. SMSF use is through G5, pinned
  artefacts and verified `smsf_trustee_pack` rights. None of these is in S1b.

## 7. Authorised already vs needing a new owner decision

| Already authorised (T-0002/T-0003 under OD-0009/OD-0010; held by OD-0013) | Needs a new owner decision |
|---|---|
| Reading publishers' terms and documentation pages; recording findings, with evidence, in `sources.yaml` as proposals (T-0002 approved scope) | Setting any permission to `owner_verified` (owner only; OD-0013 hold lifted per source) |
| Researching the RBA Cash Rate TRI terms, the SIFMA, RITS and NSW calendar sources, and the Treasury terms (within T-0002's objective) | The judgment on `automated_retrieval` where terms are silent (RBA, Treasury, H.10) |
| Drafting the R4 spec patches (`cash.aud` regime and calendar, F11 `knowable_at`) as proposals | **A one-off manual sample per dataset.** T-0002 allows it, but this instruction excluded it. Needed for the BAB table notes and the format |
| The T-0003 scorecard and the vendor-question draft (done; **not sent**) | Sending the T-0003 vendor questions (OD-0013) |
| Drafting, on instruction, the S1b control decision and the S1b task-card scope | The S1b network and credential-control decision (OD-0038); the bucket provider and keys; Q-004; Q-010's S1b disposition (§4); **S1b authorisation** of scope and infrastructure |

## 8. Escalations: proposals here that touch approved documents

| # | What | Touches | Status |
|---|---|---|---|
| E1 | Stage S1b: capture first on RBA and NY Fed; add Treasury, H.10 and BAB when their rights clear | HIO-ADR-0010 rev 3's S1b scope (four adapters; three triangulations) | **escalated**: needs an ADR revision or an explicit owner ruling |
| E2 | Replace the bill triangulations with the Cash Rate TRI and SOFR Index (or add them alongside) | ADR-0010's "three triangulation reports"; S1-A10 (the plan is a recommendation) | **escalated** with E1. "Alongside" needs no change |
| E3 | Any within-receipt ranking for Q-010 | the approved observations standard (Q-002 r5) | **escalated; not recommended for S1b** |
| E4 | An adapters-only exception to S1a's "no network client in `src/`" rule | S1a's accepted CI rule (OD-0038 context) | needs explicit coverage in the S1b authorisation |
| — | Separate RBA source ids; the `cash.aud` calendar patch; the F11 `knowable_at` patch | the register and draft specs only | within T-0002 R4; no approved standard or return mathematics changes |

## 9. Unresolved blockers (S1b gate, HIO-ADR-0010 rev 3)

1. **The T-0002 rights are `unverified` for every source** (OD-0013). This is the critical path.
2. `automated_retrieval` for RBA, Treasury and H.10; the BAB source; the Treasury terms.
3. The cited calendars (RITS, NSW, SIFMA) and the regime spec patch (R2, R4).
4. The network and credential-control decision (OD-0038), and the bucket and key provisioning
   decision.
5. Q-010 disposition (§4) and Q-004 confirmation.
6. The ADR-0010 scope question (E1/E2), if the owner wants staging.
7. The S1b authorisation itself.
