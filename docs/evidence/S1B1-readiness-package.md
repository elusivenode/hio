---
id: HIO-EVIDENCE-S1B1-READINESS
title: "S1b-1 implementation-readiness package: live AUD and USD cash-return research under HIO-ADR-0012"
status: proposed            # a report and a request; authorises nothing, verifies no right, decides nothing
owner: HIO architecture lead (owner); prepared by claude/implementation-agent
created_at: 2026-10-25
base_revision: 0665b66b1af4aa51ceda89d9e95451e365b2670d   # origin/main; revision 1 was drafted at 618059f
instruction: the owner's S1b-1 pivot message of 2026-10-25 (pasted in session; to be transcribed as an OD record on receipt)
governs: [HIO-ADR-0012 rev 3 (approved, OD-0055), HIO-ADR-0010 rev 3 (in part), HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0002]
---

# S1b-1 readiness package

> **Status: `proposed`. Role: implementation agent (Claude).** Nothing here verifies a permission,
> fetches data, provisions anything or amends an approved document. Every right stays
> `unverified`/`unknown` until the owner records it. [EXT] marks provider facts I could not confirm
> from a primary source this session.

## 0. Revision 2: reconciled with `origin/main`, and the owner's direction

**Reconciled.** Revision 1 of this package was written on a stale checkout (`618059f`) and wrongly
said OD-0061 was absent. After `git fetch`, local `main` was fast-forwarded to `origin/main` =
`0665b66b1af4aa51ceda89d9e95451e365b2670d` (no local commits were lost; only these two files were
untracked). Verified there: **OD-0061** (routine delegated receipt enabled under the OD-0060
conditions; Class S, conflicts and stop conditions keep the owner's go-ahead), STATUS (reflects
OD-0058 to OD-0061), and **harness-0.7.1** (approved by OD-0056, with the OD-0059 correction to §6.2
steps 5.7, 5.8 and 5.10). Nothing was recreated or reinterpreted. This package does not touch
any of them.

**Owner direction applied (2026-10-25 instruction).** Settled, and so removed from the request:
the five-dataset cash-first scope; WM/Reuters and ASX unavailable; the SOFR calendar derived from
NY Fed dates (no SIFMA; §1.2); exploratory-only releases with no finality claim (§2.2, §3.2);
Q-013 supported in principle, with its standards approval still separate (§3.1); no manifest
amendment until finality is needed; Azure Blob flat namespace provisionally (§4.2); every permission
`unverified` until approved; R10 resolved by OD-0061.

**No conflict found that stops this slice** (ADR-0012 §3 invariants checked).

## 1. Source rights: dataset × operation (item 1)

Sources: [matrix](../research/T-0002-owner-verification-matrix.md) and
[evidence note](../research/T-0002-rba-nyfed-evidence-2026-10-25.md). I have not re-read the live
clauses (U7), so the quotations remain fetch-tool extracts.

### 1.1 The datasets S1b-1 needs

| Id | Dataset | Needed for | Clauses | Judgement required |
|---|---|---|---|---|
| D1 | `rba.cash_rate` AONIA (`FIRMMCRID`) | `cash.aud.overnight` | CC + A + CR | **retrieval (U1)**; CR reading (U3) |
| D2 | `rba.expert_judgement` | type-A staleness exemption (ADR §4.3.2) | CC + A + CR/FD | retrieval; classification (U2) |
| D3 | `rba.cash_rate_tri` (`FIRMMCTRI`) | AUD index triangulation | CC + A + CR/FD | retrieval; classification (U2) |
| D8 | `nyfed.sofr` | `cash.usd.overnight` | NY-L,F,S,D,E,T | NY-3P reach (U4) |
| D9 | `nyfed.sofr_index` | USD index triangulation | NY-L,F,S,D,E | as D8 |
| D7 | RITS/NSW calendars (RBA pages) | calendars (gate c) | CC + A + FD | none (facts, manual, cited) |

**Omitted from S1b-1:** D4 (Cash Rate Target), which the ADR makes optional. Without it, a type-B
fallback day (new target) is flagged from D2 and quarantined for owner review rather than
interpreted. This removes one rights decision. D5 (WM/Reuters) and D6 (ASX) stay `unknown` and
unavailable; they are S1b-2 and later.

### 1.2 Recommended owner values (the rest of the matrix is as written)

- **Retrieval, D1–D3 (U1): allow by recorded owner judgement**, reasoning: CC BY 4.0 grants
  reproduction without an access-method restriction; public statistical files; `robots.txt` does not
  disallow the path; at most four requests per day per dataset; declared user agent with a contact.
  Asking the RBA is the stricter alternative and costs a delay. A publisher answer is owner contact.
- **U2:** record D2 and D3 under **CR** (the stricter reading; same operative conditions).
- **U3:** accept attribution plus a no-endorsement statement plus "internal research, no commercial
  exploitation" as satisfying CR.
- **U4:** treat SOFR as NY Fed content (its own page says it is calculated from licensed DTCC
  inputs, with a liability disclaimer, not a consent requirement).
- **U5:** raw retention indefinite for D1–D3, D8, D9.
- **U6:** leave D5/D6 blocked; S1b-2's FX-source decision is separate.
- **U7:** the owner reads the live RBA copyright §§2–5, §7.2 and the NY Fed terms once, and records
  that reading with the access date. That is the only step that cannot be delegated.
- **Operations to mark `owner_verified`, per dataset:** `automated_retrieval`, `raw_retention`,
  `internal_compute`, `derivation`, `derived_storage`, `external_processing` (CI runner and cloud
  bucket), `distribution.hio_internal`, `agent_context`. Leave **`distribution.smsf_*` and
  `quotation_in_documents` `unknown`**: S1b does not publish beyond `hio_internal` (S10-B3).
- **SIFMA (settled by the owner):** no SIFMA dependency. The SOFR observation calendar is derived from
  verified NY Fed publication dates (observed, not predicted), so it rests on the D8 rights approval alone.

## 2. Timing evidence (item 2)

### 2.1 What must actually be demonstrated

ADR-0012 uses publisher response headers in exactly two places, so only these semantics matter:

| Needed for | Semantics to show | If not shown |
|---|---|---|
| **P1 evidenced instant** (§4.3.1) | which event a header (`Last-Modified`) times; stable across requests; not skewed by intermediaries | dataset uses **P2** (capture-time basis). **Nothing is lost for S1b-1:** NY Fed payloads carry no timestamp anyway, and the RBA CSV carries a date only |
| **C4 freshness** (§4.3.3) | `Date` is the origin's generation time (or a cache's), and `Age` is present when a cache serves it; `Date` is ≥ W_doc after the window | the dataset has **no finality**; releases stay exploratory (a fail-closed state the ADR already defines) |

Correction-window semantics (W_doc: RBA 16:00 Sydney; SOFR and Index about 14:30 ET; the Index
rule's extra "calculation error" trigger) are **publisher statements, not things a probe can show**.
A probe cannot cause a revision. Evidence is (a) the publisher's own page, which the owner reads
alongside U7 (the Index clause is currently only the reviewer's citation, per ADR §4.3.5) and (b)
revisions observed during the soak.

### 2.2 Smallest permitted evidence-gathering operation

**Recommended: no separate probe.** Use the attempt records the design already writes
(ADR §4.3.3 stores `Date`, `Age`, `Last-Modified`, `ETag` unaltered). Declare P1 and finality
**unavailable at the gate** per ADR §4.2 (d2), which expressly allows it. S1b-1 releases are
exploratory during the first soak. After ten Sydney business days the owner reviews the envelopes
and may promote a dataset to "header semantics evidenced" by an OD. Zero extra requests, no extra
rights, and the capture clock starts earliest.

**Alternative, if the owner wants finality from day one:** a one-off probe, bounded as follows.

| Parameter | Value |
|---|---|
| Datasets | D1, D3, D8, D9 (D2 shares RBA delivery with D1) |
| Requests | per dataset per day, 4: before P_doc, after P_doc, before W_doc, after W_doc; for 5 consecutive business days: **at most 80 requests** in total |
| Retained | response headers and the body's sha256 and length. **No body retained**, so it needs `automated_retrieval` and `internal_compute` only, not `raw_retention` |
| Where | the owner's local machine, run by the owner or by an owner-authorised script, not CI and not the cloud (no `external_processing`) |
| Precondition | those two operations `owner_verified` for those four datasets, and a recorded OD scoping it |
| Output | a header-semantics note per dataset: `Date` vs wall clock, `Age` presence, `Last-Modified` meaning, cache layer signs (`Via`, `X-Cache`, `Cache-Control`) |

It still cannot evidence revisions, so it buys C4 only. I judge that not worth a pre-gate step.

## 3. Q-013 and the release manifest (item 3)

Both are decided **without changing S1a behaviour or amending an approved standard in place**.

### 3.1 Q-013

**Recommend: decide P2 (capture-time basis), as an opt-in S1b mode.**
- Observations §3 defines `captured_on_schedule` by the documented release time. The S1a code
  (`knowability.py:51-52`) already uses the capture instant for a revised value. ADR §4.3.1
  describes extending that reading as a *clarification of approved semantics*.
- **Vehicle: do not edit the approved standard.** Either fold the clause into the awaiting
  observations **v0.3 candidate** (its §3 row carries the old wording unchanged, so it does not
  cover this) as a separately approved revision, or record the owner decision as a **standing
  interpretation** in an OD that the v0.3 approval later absorbs. I recommend the second; it needs no
  standard change today.
- **Implementation:** a new keyword-only placement policy, default = current behaviour, selected only
  by S1b adapters, so the four S1a `data.csv` sha256 are unchanged. Acceptance test: rerun
  `hio.jobs.s1a` and compare them.
- **If declined:** P3. Every S1b-1 vintage is `schedule_only`, excluded from `as_known_by_market`,
  and the slice still runs on `as_captured_by_hio` and `reconstructed(T)`. This degrades the research
  value only for "was it knowable at T" queries.

### 3.2 Release manifest

The releases standard says the manifest core "contains exactly" a fixed field list, whose `inputs`
are receipt hashes and upstream content hashes. ADR §4.3.4 wants finality-evidence record ids inside
content identity, and the ADR already says to escalate if the schema cannot carry them.

**Recommend: for S1b-1, change nothing in the manifest.**
- S1b-1 releases are **exploratory** and identified by their recorded `knowledge_cutoff`. The
  attempt records are written and retained, but **no finality claim** is made, so no evidence ids are
  needed in the core.
- The limitations wording (§4.1) and the primary-source conditions (§4.5) go in the fields the
  standard already has (`rights`, `quality_summary`) and in the release's README artefact; I will
  confirm in the first implementation task that the existing fields carry them. If they cannot, that
  is a new escalation (see Stop conditions).
- A **later** decision, taken with the first request to call a release final: amend the releases
  standard with a versioned `inputs` kind for attempt records (a v0.3 of the standard, reviewed).
  Not needed for this slice.

## 4. Cloud storage: Tigris vs Azure Blob / ADLS Gen2 (item 4)

**Evidence quality.** The two searches this session returned a Tigris snapshots page and a 2021
Microsoft Q&A, nothing authoritative on object lock or current Azure pricing. Provider rows below are
my recollection and are **[EXT], unconfirmed**. The owner decision should be conditional on a short
verification (§4.2).

### 4.1 Against the approved requirements

| Requirement (source) | Tigris (S3 API) | Azure Blob, flat namespace | Azure ADLS Gen2 (HNS) |
|---|---|---|---|
| Separate from `macsmsf` (ADR-0002 §3: no shared bucket, credential, runtime) | separate bucket and keys satisfies it; same vendor, and ideally a **separate organisation** so one account compromise does not span both | separate subscription or storage account: a distinct trust domain by default | same |
| Versioning (S1-A3) | per-object versioning [EXT]; opt-in **snapshots** (`X-Tigris-Enable-Snapshot` at bucket creation, per its docs) | blob versioning [EXT] | versioning/immutability support on HNS has been historically limited [EXT]; verify |
| Immutability beyond code (evidence integrity) | **Object Lock not confirmed.** Without it, a leaked write key can delete or overwrite and recovery relies on versions/snapshots | version-level or container-level WORM, time-based retention and legal hold [EXT] | container-level only historically; blobs cannot be renamed while immutable [EXT] |
| Write-once on put (code enforces it in S1a) | S3 `If-None-Match: *` on PUT: support unconfirmed | `If-None-Match: *` on Put Blob [EXT] | same |
| Provider-assigned write time (ADR C5: if absent, C5 fails) | `Last-Modified` on a geo-replicated store; semantics at replication unconfirmed | `Last-Modified` / version id from one account endpoint [EXT] | same |
| Credential isolation (OD-0038; public repo) | **static access keys** held as a GitHub Environment secret; scope per bucket [EXT] | **GitHub OIDC workload-identity federation**: no long-lived secret in GitHub; RBAC limited to one container (write) and a separate reader identity [EXT] | same |
| Cost (estimates, not quotes) | trivial: capture is kilobytes a day; no egress fees [EXT] | trivial: well under a dollar a month at this volume; transactions, versions and retention add pennies [EXT] | HNS transaction pricing is higher and buys nothing here |
| Operational simplicity | simplest: S3 client, one CLI (the `tigris` skill exists); known to the owner | more moving parts: tenant, subscription, storage account, Entra app, federated credential, policy | most |
| Dependency (Q-007 stack list) | needs an S3 client (`boto3`) in the adapter layer only | needs the Azure SDK (`azure-storage-blob`, `azure-identity`) in the adapter layer only | same |
| Keys are flat content-addressed paths | fits | fits | HNS directory semantics are unnecessary |

### 4.2 Recommendation

**Azure Blob Storage, flat namespace (not ADLS Gen2), in an Australian region, version-level or
container immutability on, writer via GitHub OIDC and a separate read-only identity.** Reasons, in
order: (1) it is the only option here with server-enforced immutability *and* no stored secret,
which are the two controls that matter most for a public repository that writes evidence;
(2) the HIO charter makes receipts the system of record; (3) cost and volume are immaterial;
(4) HNS adds nothing for flat content-addressed keys.

**The counter-case for Tigris** is real: lower setup, one fewer vendor, the owner's existing
familiarity. It becomes the better choice **if** Object Lock (or an equivalent delete-protection) is
confirmed *and* the owner accepts a static key. If the owner prefers it, the same design holds with
the immutability row conditional.

**Pre-decision verification (reading only, no provisioning):** confirm from primary documentation
(a) Tigris Object Lock and `If-None-Match` support; (b) Azure version-level immutability availability
without HNS, `If-None-Match` and OIDC federation for GitHub Actions; (c) each provider's
write-timestamp semantics for C5. I can complete that with the owner's go-ahead; it fetches only
documentation.

## 5. Delivery scope: the first slice (item 5)

### 5.1 Slice **S1b-1.0: live cash capture and reproducible cash-return output**

**In:**
- adapters for D1, D2, D3, D8, D9 behind the fail-closed rights gate, one source id per dataset;
- the capture-attempt record type (ADR §4.3.3) written beside, not inside, `capture()`;
- an object-store adapter for the chosen provider behind the existing `LocalObjectStore` interface;
- the scheduled capture workflow on `main` (first and final checks, multi-slot UTC cron, local-time
  gating);
- spec patches (ADR gate (d)): AUD "in arrears", RITS selection, §4.1 wording, windows;
- `cash.aud.overnight` and `cash.usd.overnight` releases at `as_captured_by_hio`, with labelled
  `reconstructed(T)` history from one backfill receipt (`schedule_only`);
- the two index triangulations (AUD vs TRI, USD vs SOFR Index).

**Out:** FX (any), the three S1-A10 bill/FX triangulations, equity/bonds/futures, finality claims
(§3.2), any `distribution.smsf_*`, S1b-2, the S1-A16 test (owed once at S1b completion), alerts
beyond one failure channel, an egress firewall.

### 5.2 Acceptance tests

| Id | Test | Maps to |
|---|---|---|
| A-1 | S1a unchanged: `hio.jobs.s1a` twice into empty stores reproduces the four recorded `data.csv` sha256; S1a tests and `tools/check_repo.py` pass | ADR §3.1, S10-A |
| A-2 | Gate: with any of D1–D3, D8, D9 missing any listed operation, the adapter refuses before any request; D5/D6 refuse for every operation | S1-A12 |
| A-3 | Independence: no `macsmsf` import, credential or route; adapters-only network import rule; a deliberate violation fails CI | S1-A1, A2 |
| A-4 | Receipts write-once and verified on read against the **cloud** store; a second write is refused; versioning/immutability demonstrated by a failed overwrite and a failed delete | S1-A3 |
| A-5 | Vintage and mode invariants on live captures (OBS-INV-001…007), with Q-013's decided policy; P3 fallback test if declined | S1-A4…A6 |
| A-6 | Cash exactness: RA §3.2 fixtures and CASH-USD-INV-3/4 hold; period `knowable_at`; RITS selection verified against a dated RITS fixture | S1-A7 |
| A-7 | Reproduction: a release rebuilt from the retained receipts reproduces `content_sha256` and `data.csv` | S1-A11 |
| A-8 | Index triangulations: pre-registered expected difference about 0; outcome classified; **no pass/fail on agreement**; residuals explained or labelled unexplained | ADR §4.4 |
| A-9 | Attempt records: C1, C2, C3, C7 replay from the stores alone; a forged `verified_unchanged` with a pre-window `Date` is classed not-evidence; releases declared exploratory | ADR §4.3.3 |
| A-10 | Quality: quarantine for P1 later than capture, out-of-window changes and ingest of multi-vintage receipts (if §6 D7 accepts); an AONIA type-A day does not trip staleness | S1-A14 |
| A-11 | Soak: ten consecutive Sydney business days of cash captures, punctuality and gaps recorded, an alert fires on a deliberately failed run | S1-A13 |
| A-12 | Secrets: none in files, logs or handoffs; a secret-pattern check runs on logs; no secret reaches fork-PR workflows | OD-0038 |
| A-13 | Every release manifest states "benchmark accrual; not an achievable deposit or fund return; replicable only with a basis", attribution and the NY Fed derivation/DTCC notices | ADR §4.1, §4.5 |
| A-14 | Independent review at the head by Codex, then owner acceptance (separate actions) | S1-A15, AGENTS rule 3 |

**Durability and reproducibility claim:** a live capture exists in an off-machine immutable store,
and a clean checkout plus that store reproduces the two cash releases byte-for-byte.

### 5.3 Controls to record at gate (e) (OD-0038 successor)

Minimum, from the S1b readiness assessment, unchanged except for the credential method:
- a separate capture workflow whose only post-install network use is the adapters; actions pinned
  by commit SHA; minimum token permissions; triggers `schedule` and `workflow_dispatch` only, never
  `pull_request_target`;
- the capture identity is limited to one container/bucket and **only to `main`** through a GitHub
  Environment;
- a read-only identity held by the owner; documented rotation (static keys only);
- no `macsmsf` credential; no data-source credential (all keyless);
- no runner egress firewall, recorded as the S1b successor to Q-008.

## 6. The one implementation-authorisation decision (revision 2)

Only hard prerequisites remain. Settled items are in §0 and are not repeated.

### 6.1 Rights evidence awaiting your approval (H1)

Nothing is verified. These are the exact cells for you to approve or reject after reading the live
clauses (U7). Sources and extracts: [matrix](../research/T-0002-owner-verification-matrix.md) §1–§2,
[evidence](../research/T-0002-rba-nyfed-evidence-2026-10-25.md) §1–§2, accessed 2026-10-25. The
extracts are fetch-tool excerpts, **not yet checked against the live pages**.

| Dataset | Clause evidence to read | Approve (operations) | Judgement you record |
|---|---|---|---|
| D1 AONIA `FIRMMCRID` | RBA copyright page §2 (CC BY 4.0), §3, **§4 Cash Rate** | retrieve, raw retention (indefinite), compute, derive, store derived, external processing (CI runner, cloud store), `hio_internal`, agent context | **Retrieval is not addressed by the terms** (U1): approve by reasoned judgement or ask the RBA. CR conditions met by attribution, no-endorsement, no commercial exploitation (U3) |
| D2 expert-judgement flags | same; §4 or §5 | same | classification CR or FD (U2); I recommend CR |
| D3 Cash Rate TRI `FIRMMCTRI` | same; §4 or §5 | same | classification (U2) |
| D8 SOFR | NY Fed terms of use ("Last Updated 6/9/2023"): licence, automated access, store, derive, labelling, DTCC notice; the third-party-content clause | same, but `external_processing` and `hio_internal` carry the labelling, no-endorsement and DTCC conditions | U4: SOFR is NY Fed content, not view-only third-party content |
| D9 SOFR Index | NY Fed terms of use; same | same | as D8 |
| D7 RITS/NSW calendars | RBA RITS hours and bank-holiday pages | retain and cite as reference data | none (facts) |

**Finding for H1, raised while building the adapters (not yet in the matrix).** AONIA, the TRI and the
Cash Rate Target come in the **same F1 CSV file** as the ASX bank-bill and FENICS OIS columns
(evidence note §1: their `Source` rows are ASX and FENICS, RBA copyright §7.2 third party). So
`raw_retention` of "the F1 file as published" retains third-party material whose permission is
`unknown`, even though the parser reads only the RBA columns. Options for you: (1) record a reasoned
judgement that retaining RBA's own published file unaltered is covered; (2) ask the RBA/ASX;
(3) retain a column-filtered copy as the receipt and record only the original's hash (loses the exact
raw bytes the evidence design wants); (4) a different RBA-only source for AONIA and the TRI.
I recommend deciding this together with U1. The adapters are unaffected; the parser already ignores
those columns.

Left `unknown`: `distribution.smsf_*`, `quotation_in_documents`, D4 Cash Rate Target, D5 WM/Reuters,
D6 ASX, and SIFMA (no dependency). Raw retention duration (U5): indefinite.
Verifying U1–U5 and U7 is the only part that cannot be delegated.

### 6.2 Minimum authorisation requested

The ADR gate for **live** S1b-1 needs every item (b) to (g). I propose splitting the authorisation
so that implementation does not wait on the live prerequisites. **This split is my reading of
ADR-0012 §4.2 and S1a's "authorises no live data operation"; please confirm it, since an ambiguous
instruction is not permission.**

**Authorisation A (now): S1b-1.0 development without live operations.** Scope, bounded and reversible:
- a new task card (T-0009) for S1b-1.0, drafted as `proposed` until you authorise it;
- on synthetic fixtures only: the five dataset adapters (all behind the fail-closed rights gate),
  the capture-attempt record type, the cloud object-store interface, the RITS/NY Fed-date calendars
  as cited reference data, the spec patches (gate (d)) and the two index triangulations;
- the **documentation-only** storage verification (Azure Blob: versioning, immutability without a
  hierarchical namespace, `If-None-Match`, GitHub OIDC, write-timestamp semantics, pricing, region);
- no network call outside documentation reads, no credential, no provisioning, no real source, no
  change to S1a semantics (acceptance test A-1).

**Authorisation B (later, separate, triggered by these hard prerequisites).**

| # | Prerequisite | Needed for | Who |
|---|---|---|---|
| H1 | the rights approvals in §6.1, recorded per dataset and operation | the first live fetch | you |
| H2 | **Q-013 disposition**: P2 in principle (your direction); the observations standards approval stays separate, so **P3 is in force until it is approved**. ADR gate (d3) asks for "decided"; confirm this satisfies it | first release claims | you, then standards approval |
| H3 | the network and credential-control decision (OD-0038 successor): the controls in §5.3, "no egress firewall" recorded as Q-008's S1b successor | provisioning and fetch | you |
| H4 | the verified storage facts (Authorisation A's documentation check), then your go-ahead to provision a flat-namespace Azure Blob account with immutability and a writer OIDC identity | provisioning | you |
| H5 | the Q-010 additive ingest check: adopt or decline (default: decline, rely on suppression) | ingest code | you |

I do not ask you to decide H1 to H5 now apart from H2's confirmation. They are listed so that
nothing blocks first-fetch by surprise. Authorisation B is requested later as one record, when the
documentation check is complete and H1 is done.

**Decision requested:** (1) approve Authorisation A as scoped, (2) confirm the split reading,
(3) confirm H2's P3-until-approved reading. Any one "no" and I stop at the document.

## 7. Revision 3 note: superseded by T-0009 (OD-0062)

After this package, the owner approved Authorisation A and directed a simpler first slice
([T-0009](../../registers/tasks/T-0009-s1b1-cash-capture-and-research.md), proposed). Where they differ,
**T-0009 governs** and these sections are history:
- §5.1 and §5.2: scope and acceptance now follow T-0009 §2, §3 and §7 (P3 only; no P2 or Q-013
  implementation; lean capture without C1–C7; A-9 and A-10 replaced).
- §3.1 (Q-013): stays an open standards decision, not implemented in this slice.
- §4 and §5.3: Azure Blob is the working assumption (an account exists); the writer uses OIDC;
  infrastructure is authored as OpenTofu or Terraform (T-0009 §5), never applied under Authorisation A.
- §2.2: unchanged (no probe). §6.1 rights evidence: unchanged and still unapproved.

## Stop conditions I will honour

I will stop and flag if: a right is read differently from §1.2; the existing manifest fields cannot
carry the limitations and conditions; the chosen store cannot supply a provider-assigned write time
(ADR C5 then fails and finality is unavailable); an S1a hash changes; or a secret would need to
enter a prompt, file or log.

## Not approved by this document

No permission, ADR, standard, Q-013, storage provider, scope or S1b-1 authorisation.
