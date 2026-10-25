---
id: T-0009
title: "S1b-1.0: immutable live cash-rate capture and reproducible exploratory cash-return research (AONIA, expert-judgement flags, Cash Rate TRI, SOFR, SOFR Index), staged under HIO-ADR-0012"
status: proposed   # drafted under OD-0062; Authorisation A (development on synthetic fixtures) is approved, nothing else is. Not authorised for live operations
owner: owner
assignee_role: "implementation engineer (independent reviewer: Codex)"
created: 2026-10-25
authorised_by: OD-0062   # Authorisation A ONLY: synthetic-fixture development and a documentation-only storage check
staging_approved_by: OD-0063   # section 6 (finality staging) and OpenTofu (section 5); no live operation
base_revision: 0665b66b1af4aa51ceda89d9e95451e365b2670d
links:
  adrs: [HIO-ADR-0012, HIO-ADR-0010, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0002]
  specs: [cash.aud.overnight@0.2.0, cash.usd.overnight@0.2.0]
  evidence: [docs/evidence/S1B1-readiness-package.md]
  depends_on:
    authorisation_B: ["T-0002 rights per dataset and operation", "network and credential controls (OD-0038 successor)", "storage selection and verification", "explicit live authorisation"]
  blocks: ["S1b-1 stage completion", "S1b-2"]
---

# T-0009: S1b-1.0

> **Proposed.** Authorisation A lets work start on synthetic fixtures. **Nothing here permits a live
> fetch, a credential, provisioning, or a right to be treated as verified.** Role: implementation
> agent. This card narrows no approved text. Its one staging decision (§6) and OpenTofu (§5) were
> **approved by OD-0063**.

## 1. Purpose

Deliver real, immutable capture of five cash datasets and reproducible **exploratory** cash-return
research from them: `cash.aud.overnight`, `cash.usd.overnight`, and two publisher-index comparisons.
It does **not** deliver point-in-time knowability or finality.

| Dataset | Source id |
|---|---|
| AONIA | `rba.cash_rate` |
| Expert-judgement flags | `rba.expert_judgement` |
| Cash Rate TRI | `rba.cash_rate_tri` |
| SOFR | `nyfed.sofr` |
| SOFR Index | `nyfed.sofr_index` |

## 2. Scope: in

1. Five adapters behind the **unchanged fail-closed rights gate**, one source id each.
2. **Raw receipts** (S1a `capture()` unchanged, write-once, content-addressed) and the existing
   vintages, placed with **P3 `schedule_only`** only: no `as_known_by_market` claim.
3. A **capture-run record** (§4) written for every run, including unchanged re-fetches and failures.
4. A cloud object-store adapter behind the existing store interface, written against a **local
   emulator or fake in tests**.
5. Scheduled capture workflow definition (cron slots, local-time due check), not enabled.
6. Spec patches (ADR gate (d)): AUD "in arrears", RITS selection, §4.1 wording.
7. Calendars: RITS and NSW as cited reference data; the **US observation calendar derived from
   verified NY Fed publication dates**, with no SIFMA dependency.
8. Exploratory releases for the two cash factors, `as_captured_by_hio` plus labelled
   `reconstructed(T)` history; the two index comparisons (ADR §4.4).
9. **IaC authoring only** (§5).
10. The documentation-only storage verification (readiness package §4.2).

## 3. Scope: out

P1 header interpretation; the P2 mode and Q-013; C1–C7 verification and finality claims (§6); manifest
schema amendments; the three S1-A10 triangulations; FX of any source; WM/Reuters and ASX; SIFMA;
equity/bonds/futures; any consumer distribution; `tofu apply`/`plan`/`init` with a provider; any
network call beyond documentation reads; S1b-2.

**Invariants kept** (ADR-0012 §3): S1a semantics and the four S1a `data.csv` sha256, return
mathematics, observation invariants, release integrity, the `macsmsf` boundary.

## 4. What must be captured now (it cannot be reconstructed later)

Receipts hold the **body**. Everything below is lost if not written at capture time. Each capture run
writes one write-once, content-addressed record at
`catalogue/attempts/<source_id>/<attempted_at>-<record_sha256>`. **The fields are exactly ADR-0012
§4.3.3's, so later verification needs no new data.**

| Lost forever if not recorded | Recorded as |
|---|---|
| That a check happened and found **no change** (S1a writes nothing for an identical re-fetch) | the run record, `outcome: verified_unchanged`, with the matching `receipt_id` |
| A failed or partial attempt | `outcome: failed` and an error class; no bytes |
| Actual request start and body-complete time on HIO's clock | `attempted_at`, `completed_at` |
| The publisher's own clock and cache state at that moment | `response_envelope`: status, `Date`, `Age`, `Last-Modified`, `ETag`, `Content-Type`, `Content-Length`, and `Cache-Control`/`Via` if present, **unaltered** |
| Request identity | method and the configured URL; the final URL after any redirect; the user agent sent |
| Exact bytes before parsing | `response_sha256`, `response_bytes`; the receipt itself |
| Which code ran, and which scheduled run | `execution`: platform, `run_id`, `run_attempt`, job, `sha`, copied unaltered; `platform: other` for a manual run |
| Intended slot versus actual | the due local time computed by the gate |
| HIO runner clock skew against the publisher | derivable from `completed_at` and `Date`; no extra field |

**Reconstructable later, so not a capture burden:** the store's provider write time and version history
(kept by versioning and immutability); parsed values (from the stored bytes); `keys_checked` digests
(from the stored bytes); the C1–C7 results (computed over the above).

**Not recoverable under any design:** the past state of an overwritten publisher file. A backfill is a
single current-value receipt, `schedule_only`, as ADR §4.3.2 says.

## 5. Infrastructure as code (new, from the owner's note)

- **Working assumption:** Azure Blob Storage, flat namespace, in the owner's Azure account. Terraform
  files are authored and reviewed in this slice. **They are never applied under Authorisation A.**
- **"Fully open-source Terraform" resolved to OpenTofu.** HashiCorp Terraform has been
  under the Business Source Licence since 2023 [EXT]. The open-source (MPL-2.0) fork is **OpenTofu**,
  with HCL and `.tf` files compatible. **OpenTofu is approved (OD-0063)** as an authoring tool, one new entry in
  the Q-007-style stack list.
- **State.** The state holds the account's resource detail, so it never enters git (public repository).
  Remote state belongs in a separate container or account, **not** the evidence store. `*.tfstate`,
  `*.tfvars` and plan files go in `.gitignore`, and the repository check refuses them.
- **Credentials.** None committed. The writer is a GitHub OIDC federated identity; the reader is a
  separate identity. No static key.
- **`tofu fmt` is allowed. `init`, `validate` and `plan` are not,** because they download providers.
  They move to Authorisation B (control decision H3).

## 6. Staging decision (approved by OD-0063)

ADR-0012 §5 lists **"Capture-attempt records and finality evidence (§4.3.3–§4.3.4)" as owed in
S1b-1**. T-0009 writes the record (every §4.3.3 field, so nothing is lost) but does not implement the
**verification** and **finality**. That is a staging of an approved obligation, so please record:

> **For S1b-1.0 only:** (a) the §5 row "Capture-attempt records and finality evidence" is discharged
> **in part**: records are written in full; the **C1–C7 checks, finality (§4.3.4) and the 'final'
> release label are deferred and remain owed** before any release is called final, and before S1b-1
> stage completion or G2. (b) ADR-0012 gate (d2) is met by declaring header semantics **unavailable**,
> and gate (d3) by the P3 rule being in force **with Q-013 left open and undecided**. (c) Every S1b-1.0
> release is `exploratory` and states its knowledge cutoff; none may be labelled final.

No text of ADR-0012 changes. The sections above stay as approved. Everything that holds the staging
within the ADR's own wording is §4.3.1 (P3 when P2 is unavailable) and §4.3.4 (otherwise
exploratory). Only (a) is a real narrowing.

Approved by OD-0063 as worded above. Had it been declined, T-0009 would have added C1–C7 to its scope.

## 7. Acceptance tests

Replaces readiness package §5.2 in scope. **A-9 and A-10 change, A-4 gains IaC checks.**

| Id | Test |
|---|---|
| A-1 | S1a unchanged: `hio.jobs.s1a` twice reproduces the four recorded `data.csv` sha256; S1a tests and `check_repo.py` pass |
| A-2 | Rights gate: with any of the five datasets missing any needed operation, the adapter refuses before a request; WM/Reuters and ASX sources refuse for every operation |
| A-3 | Independence: no `macsmsf` import, credential or route; a deliberate violation fails CI; no secret in files or logs |
| A-4 | Store: write-once and verified-on-read against the cloud interface (emulator in tests); an overwrite and a delete fail in the emulator's immutability mode; `.tfstate`/`.tfvars` refused by the repo check; the Terraform files pass `tofu fmt -check` |
| A-5 | **Capture**: a scheduled run on fixtures writes a receipt and a run record; a second identical run writes **no receipt and one new run record**; a failed run writes a failed record; the §4 fields are all present |
| A-6 | **Replay**: from the receipts and run records alone, every capture is re-parsed to the same vintages |
| A-7 | **Reconstruction**: a release rebuilt from retained receipts reproduces `content_sha256` and `data.csv` |
| A-8 | **Cash exactness**: RA §3.2 fixtures and CASH-USD-INV-3/4; RITS selection verified against a dated RITS fixture; an AONIA type-A day does not trip staleness |
| A-9 | **Placement**: every vintage is `schedule_only`; `as_known_by_market` returns nothing; no release is labelled final; each states its `knowledge_cutoff` and "benchmark accrual; not an achievable deposit or fund return; replicable only with a basis" |
| A-10 | **Index comparisons**: AUD vs TRI and USD vs SOFR Index, pre-registered expected difference about 0, classified, **no pass/fail on agreement**; residuals explained or labelled unexplained |
| A-11 | Quality: a payload or header instant later than `captured_at` is quarantined, never placed; out-of-window changes become quarantined new vintages |
| A-12 | Independent review by Codex at the head; owner acceptance is a separate action |

**Deferred with the finality staging, owed before final labels, S1b-1 completion or G2:** C1–C7 checks,
finality, the 10-business-day soak with a CI-run audit (S1-A13), the P2 mode.

**Live acceptance (Authorisation B, not this slice):** the first scheduled capture reaches the real
store; the soak records punctuality and gaps; replay and reconstruction (A-6, A-7) run on live receipts.

## 8. Authorisation B prerequisites (the real blockers)

| # | Prerequisite | Status |
|---|---|---|
| H1 | rights approved per dataset and operation (package §6.1) | unverified |
| H2 | Q-013 | open; **P3 in force**, so no blocker for this slice |
| H3 | network and credential controls (OD-0038 successor), including the IaC tool and state decisions | undecided |
| H4 | storage facts verified, then go-ahead to provision | documentation check is in scope; provisioning is not |
| H5 | the Q-010 ingest check | undecided (default: decline) |
| H6 | the §6 staging decision | **approved, OD-0063** |

## 9. Not approved

Everything outside OD-0062's Authorisation A. No right, no provider, no IaC tool, no staging, no live
operation, and no finality is approved by this card.
