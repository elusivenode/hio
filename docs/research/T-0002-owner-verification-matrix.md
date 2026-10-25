---
id: HIO-RESEARCH-T0002-MATRIX
title: "T-0002 owner-verification matrix: RBA and NY Fed datasets × S1b operations (proposals only)"
status: draft              # for owner verification; NOT owner_verified; registers/sources.yaml unchanged
owner: owner (verifies); prepared by claude/implementation-agent
created_at: 2026-10-25
task: T-0002 (OD-0009; held by OD-0013; prepared under OD-0046)
evidence: docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md   # URLs, access dates, quotations, uncertainties
---

# T-0002 owner-verification matrix

> **Nothing here is verified.** Every cell is a **recommended interpretation** for the owner to accept or reject,
> per dataset and per operation (rights standard §1 and §3). Until the owner records a value as
> `owner_verified`, the gate treats it as `unknown`, which means deny. The sources, access dates
> and quotations are in the [2026-10-25 evidence note](T-0002-rba-nyfed-evidence-2026-10-25.md)
> (§1–§2), all accessed on 2026-10-25.

## 1. The clauses, kept separate

| Key | Clause (source) | What it grants or adds |
|---|---|---|
| **CC** | RBA copyright §2: "all RBA Material is provided under a Creative Commons Attribution 4.0 International License" | the **copyright** permissions to reproduce, publish, communicate and adapt, subject to attribution. **It says nothing about the access method.** It does not cover third-party material |
| **A** | RBA §3 attribution: "Source: Reserve Bank of Australia [year] OR Source: RBA [year]"; it must not suggest endorsement | a condition on every artefact derived from RBA material |
| **CR** | RBA §4 **Cash Rate** (the RBA-administered benchmark, under its Cash Rate Procedures Manual): "personal or commercial use only if it is not stated, represented or in any way implied" that the RBA endorses it; no unlawful use; no "improper commercial exploitation"; the §7 disclaimers apply | **special conditions on top of CC**, for the Cash Rate and "Cash Rate Materials" |
| **FD** | RBA §5 **Financial Data** (every RBA statistic "other than the Cash Rate"): not a benchmark; users "assume the entire risk"; it may be withdrawn or changed without notice; the same no-endorsement and no-exploitation conditions; third-party content needs consent | **special conditions on top of CC**, for the other RBA-sourced series |
| **3P** | RBA §7.2 third party: "may not be reproduced, published, communicated to the public, adapted or otherwise used in whole or part" without the third party's consent | **overrides CC** for any series whose `Source` row is not RBA |
| **NY-L** | NY Fed terms (last updated 6/9/2023): "use, copy, and distribute Content" "for your personal or business purposes" | the licence |
| **NY-F** | "Access the Content, manually or through an automated process or device," provided access does not disable, damage or interfere with the site | **explicit automated access**, conditioned on load |
| **NY-S** | "Download, store, and use Content in any format or media" | retention and storage |
| **NY-D** | "Modify and create derivative works"; modified content must be "clearly label[led]" so that there is no confusion between the original and the modifications or their source | derivation, with **derived-work identification** |
| **NY-R** | the republication notice, "The [DATA NAME] is subject to the Terms of Use posted at newyorkfed.org.", plus the disclaimer that the New York Fed "is not responsible for publication of the [DATA NAME] by [NAME OF PUBLISHER], does not [sanction] or [endorse] any particular republication, and has no liability for your use" | a condition on any **republication** |
| **NY-E** | no statement or implication that the New York Fed endorses the use; its name not used as an endorsement | a condition on everything |
| **NY-T** | SOFR "calculated using data provided under a license granted to the New York Fed by DTCC Solutions LLC"; DTCC and its sources "have no liability" | a liability notice to carry |
| **NY-3P** | "Third-party content the New York Fed publishes … the New York Fed may only allow you to view those materials as they appear" | **open:** does it reach SOFR? (§4, U4) |

## 2. The matrix

**Legend:**
- **rec+C**: a **recommended interpretation** that the operation is permitted, with the conditions keyed after it. Not a rights value until the owner verifies it;
- **J**: the terms are silent, so allowing it needs an **owner judgment with reasoning**, or a
  publisher answer;
- **3P**: **unavailable**. The permission is absent or unverified (`unknown`) pending the third party's consent. This is **not** an explicit `deny`; the gate refuses both;
- **?**: the clause classification is undecided;
- **—**: not requested in S1b.

**Operations:**
- *Retrieve* = `automated_retrieval`;
- *Retain raw* = `raw_retention` (state the duration);
- *Calculate* = `internal_compute` + `derivation`;
- *Store derived* = `derived_storage`;
- *Rebuild / reconstruct* = re-running builds from retained receipts, and labelled
  `reconstructed(T)` history from a backfill;
- *Ext. processing* = `external_processing` (CI runners, the cloud bucket);
- *`hio_internal`* = `distribution.hio_internal`;
- *Consumer publication* = `distribution.smsf_*` and `quotation_in_documents`;
- *Agent* = `agent_context`.

| # | Dataset (series id; `Source` row) | Clauses | Retrieve | Retain raw | Calculate | Store derived | Rebuild / reconstruct | Ext. processing | `hio_internal` | Consumer publication | Agent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | RBA AONIA (`FIRMMCRID`; RBA) | CC + A + **CR** | **J** | rec+A,CR | rec+A,CR | rec+A,CR | rec+A,CR | rec+A,CR | rec+A,CR | — (later: A,CR) | rec+A,CR |
| D2 | RBA expert-judgement flags (F1 EJ file; RBA) | CC + A + **CR or FD ?** | **J** | rec+A,? | rec+A,? | rec+A,? | rec+A,? | rec+A,? | rec+A,? | — | rec+A,? |
| D3 | RBA Cash Rate TRI (`FIRMMCTRI`; RBA) | CC + A + **CR or FD ?** | **J** | rec+A,? | rec+A,? | rec+A,? | rec+A,? | rec+A,? | rec+A,? | — | rec+A,? |
| D4 | RBA Cash Rate Target (`FIRMMCRTD`; RBA), only to interpret fallback type B | CC + A + **FD** | **J** | rec+A,FD | rec+A,FD | rec+A,FD | rec+A,FD | rec+A,FD | rec+A,FD | — | rec+A,FD |
| D5 | RBA F11 AUD/USD (`FXRUSD`; **WM/Reuters**) | **3P** (CC does not apply) | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** |
| D6 | RBA F1 1m BAB (`FIRMMBAB30D`; **ASX**) | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** | **3P** |
| D7 | RBA holiday and RITS-hours pages (calendar reference) | CC + A + FD (facts) | — (manual, cited) | rec+A | rec+A | rec+A | rec+A | rec+A | rec+A | — | rec+A |
| D8 | NY Fed SOFR (`type: SOFR`) | NY-L, F, S, D, R, E, T; **NY-3P ?** | rec+F(load) | rec | rec+D | rec+D | rec+D | rec | rec+D,E,T | — (later: R,E,T) | rec+E |
| D9 | NY Fed SOFR Index (`type: SOFRAI`) | NY-L, F, S, D, R, E (NY-T if it is treated as SOFR-derived) | rec+F(load) | rec | rec+D | rec+D | rec+D | rec | rec+D,E | — (later: R,E) | rec+E |

**Notes:**
- **D1–D4 retrieval.** The RBA's CC licence grants copyright permissions, but **not an access
  method**. The `robots.txt` evidence (no rule against `/statistics/tables/csv/`) is a crawler
  convention, not a licence. The owner may allow retrieval by judgment, recording the reasoning:
  public statistical files, a modest schedule, a declared user agent. The alternative is a
  publisher answer, which is owner-only contact.
- **D1 is the benchmark itself.** CR's no-implied-endorsement and no-exploitation conditions
  apply to every operation, not only publication. They are satisfied by:
  - the attribution in every manifest;
  - a no-endorsement statement;
  - no commercial exploitation (HIO is internal research).

  The owner should record that reading.
- **D2 and D3 classification.** "Cash Rate Materials" are materials "that include the Cash
  Rate". The TRI is computed from the Cash Rate but is a distinct statistic. Under either CR or
  FD, the operative conditions are the same: attribution, no endorsement, no exploitation, and
  risk on the user. **The classification changes the record, not the outcome.**
- **D5 and D6 are third-party material.** No RBA clause can clear them.
  - They are recorded as `unknown` with the note "RBA §7.2: use requires the third party's
    consent; no consent evidence". **No rights holder has denied anything:** `deny` is
    reserved for an outright prohibition.
  - They need written consent or a licence from LSEG (WM/Reuters) or ASX, or the RBA
    confirming that its licence allows onward use.
  - Until then **every** operation, including retention of a sample, is unavailable.
- **D8 and D9 conditions to carry:**
  - **D:** each release identifies itself as an HIO derivation (series, construction and
    version) that is distinct from the published rate;
  - **E:** no endorsement;
  - **T:** the DTCC liability notice;
  - **R:** applies only when HIO republishes beyond itself, which S1b does not. Carrying the
    notice in every manifest anyway is cheap;
  - **F:** the capture schedule stays modest (a few requests a day).
- **Duration of raw retention** (all rows): the owner must state it. The proposal is
  "indefinite, for audit and rebuild", because the receipts are the system of record.
- **Not in this matrix:** US Treasury bills and FRB H.10. Their terms were not re-researched
  on 2026-10-25 and stay as in the 2026-10-18 note.

## 3. Timing facts the owner may verify alongside (R2)

| Fact | Evidence | Proposed record |
|---|---|---|
| AONIA is in arrears, published before 09:20 Sydney on the next RITS day, and final after 16:00 | the methodology, last updated 21 July 2026 | `cash.aud.overnight` regime: in arrears |
| F1 rows are labelled by the AONIA applicable date; the TRI by publication date | the F1 sample of 2026-10-23 (the Cash Rate empty, the TRI filled at 08:59 AEDT) | `valid_time` = b for AONIA; the TRI's publication date P equals the period end of the return it compounds, so the triangulation aligns on period ends with no shift |
| SOFR is published about 08:00 ET on the next SIFMA day; revised by about 14:30 ET only if it moves by more than 1 bp; the SOFR Index is labelled by publication date | the NY Fed page, last updated 10/5/2026; the API sample | `cash.usd.overnight` as specified; the SOFR Index aligns on period ends, like the TRI |
| The RBA FX fix is "4.00 pm (Sydney)", in local time | the definitions page; F11.1 Last-Modified 16:43 AEDT | resolves the OD-0013 DST question (S1b-2) |
| RITS closes on 8 named holidays where observed in NSW and Victoria; it is open on NSW-only holidays | the RITS hours page; an RBA RITS document (search extract only) | the RITS calendar ≠ the NSW calendar |

## 4. Unresolved questions (owner)

- **U1. RBA retrieval.** Allow automated retrieval of D1–D4 by owner judgment, or ask the RBA?
- **U2. D2/D3 clause.** Record them under CR or FD? (Proposal: CR, the stricter reading, since
  the conditions are the same.)
- **U3. CR reading.** Do HIO's internal research releases satisfy "no implied endorsement" and
  "no improper commercial exploitation" by attribution plus a no-endorsement statement?
- **U4. NY-3P.** Is SOFR NY Fed content (calculated from licensed DTCC inputs), and therefore
  outside the view-only third-party clause? (Proposal: yes, on the SOFR clause's own wording.)
- **U5. Retention duration.** Indefinite for D1–D4, D8 and D9?
- **U6. D5/D6.** Seek consent (owner contact), substitute a source, or leave them blocked?
- **U7. The quotation check.** The evidence quotations are fetch-tool extracts. Verifying needs
  the owner to read the live clauses: the RBA copyright §§2–5 and §7.2, and the NY Fed terms.
