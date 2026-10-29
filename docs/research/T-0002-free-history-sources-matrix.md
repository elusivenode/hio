---
id: HIO-RESEARCH-T0002-FREE-HISTORY
title: "Free long-history sources: FRED/ALFRED, US Treasury, FRB H.10 and RBA historical tables × historical research operations (proposals only)"
status: draft              # for owner verification; NOT owner_verified; registers/sources.yaml unchanged
owner: owner (verifies); prepared by claude/implementation-agent
created_at: 2026-10-29
task: T-0002 (prepared under OD-0130 item 4)
---

# Free long-history sources: rights rows (draft)

> **Nothing here is verified.** Every cell is a **recommended interpretation** for the owner to accept or reject, in
> the same form as the [T-0002 owner-verification matrix](T-0002-owner-verification-matrix.md) (its legend applies).
> Until the owner records a value as `owner_verified`, the gate treats it as `unknown`, which means deny. Terms pages
> were read on **2026-10-29** by a page-to-text tool. That gives the same limit as U7: **the owner should read the live
> clauses** before verifying anything.

## Use requested

Historical research only, for base-camp criteria 7 and 8 (proposed, `docs/base-camp.md`):
- a one-off or occasional download of published history;
- retention of the raw files as sealed receipts;
- calculation of research series (for example a CMT duration return), stored internally;
- rebuilds from the retained files;
- processing on CI runners and in the cloud store;
- `hio_internal` distribution only.

**Not requested:** scheduled capture, consumer publication, SMSF use, quotation in documents.

**History is reconstructed, never captured.** Any series built from these files is labelled `reconstructed(T)`
(HIO-ADR-0012; P3). It supports no point-in-time knowability claim.

## 1. The clauses (quoted as read on 2026-10-29)

| Key | Source and clause | What it grants or restricts |
|---|---|---|
| **FRED-P** | FRED terms (fred.stlouisfed.org/legal, no date shown): free use "for your own personal use subject to certain limitations"; for public-domain and "Copyright: Citation required" series, "internal commercial uses" with attribution | the use licence, limited by the restrictions below |
| **FRED-X** | FRED prohibitions: "Store, cache, or archive any portion of the FRED® Services or FRED® Content" without permission; no incorporation "in any database, compilation, archive, cache, or other medium"; no "scripts, spiders, scrapers, bots" for excessive access; FAQ: "Don't do any data mining, scraping or extraction" | **forbids HIO's retention model** (sealed raw receipts, rebuilds) unless the St. Louis Fed grants permission |
| **FRED-3P** | FRED: for copyrighted third-party series, "you must contact the data owner to obtain permission" | per series; FRED cannot grant it |
| **FRED-API** | API terms (no date shown): a key is required; the bank may limit bandwidth and may "terminate the license at any time for any reason"; notice "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." | revocable; no retention right stated |
| **FRB-PD** | Federal Reserve Board website policies (updated 2024-08-02): "Unless otherwise indicated, information on Board's website is in the public domain and may be copied and distributed without permission. Please cite to the Board as the source"; no endorsement; third-party material needs the third party's permission | public domain with citation; **automated access is not addressed** |
| **UST** | No Treasury terms clause was found on the interest-rate pages or "Site Policies and Notices" (2026-10-29; the legal-notices page returned 404). Presumption: a US Government work under 17 U.S.C. §105 (public domain). The par yield curve's inputs are "indicative quotations obtained by the Federal Reserve Bank of New York" | public domain presumed, not stated. **Open:** whether the NY Fed's quotation inputs carry any condition (cf. NY-3P in the T-0002 matrix) |
| **RBA-CC/FD/A** | RBA copyright §2 (CC BY 4.0), §5 Financial Data, §3 attribution (as in the T-0002 matrix). The F2 file's `Source` row reads **RBA** for all five series (2-, 3-, 5- and 10-year, and the indexed bond), so §7.2 third-party consent does not apply | CC BY with the FD conditions and attribution; **automated access is not addressed** (as for U1) |

## 2. Rows

| # | Dataset | Clauses | Retrieve (one-off) | Retain raw | Calculate | Store derived | Rebuild / reconstruct | Ext. processing | `hio_internal` | Agent |
|---|---|---|---|---|---|---|---|---|---|---|
| **H1** | FRED / ALFRED (any series, including vintages) | FRED-P, FRED-X, FRED-3P, FRED-API | **deny (rec)** | **deny (rec)**: FRED-X | J | J | **deny (rec)** | J | J | J |
| **H2** | US Treasury daily par yield curve and bill rates (XML feeds; history) | UST | J (modest, manual or one-off) | rec+C (cite Treasury; no endorsement) | rec+C | rec+C | rec+C | rec+C | rec+C | rec+C |
| **H3** | FRB H.10 foreign exchange rates, history (the Board's XML zip, not FRED) | FRB-PD | J (modest, one-off) | rec+C (cite the Board) | rec+C | rec+C | rec+C | rec+C | rec+C (cite the Board; no endorsement) | rec+C |
| **H4** | RBA F2 government bond yields (daily from 2013-05-20; F2.1 monthly history) | RBA-CC, FD, A | J (as U1: owner judgement on the live terms) | rec+C (A; FD) | rec+C (FD: the user bears the risk; not a benchmark) | rec+C | rec+C | rec+C | rec+C (A; no endorsement) | rec+C |

**H1 recommendation.** Do not use FRED or ALFRED as a retained source. Its terms forbid the store-and-rebuild model
HIO depends on. Where a FRED series originates with a public-domain publisher (Treasury, the Board), take it from the
publisher (H2, H3). **ALFRED's vintages have no free substitute.** They are the one thing FRED offers that the
publishers do not, and they would need the St. Louis Fed's written permission. Contacting it needs an owner
instruction. FRED remains usable for a human's manual look-up, as reference only.

## 3. Owner questions

| # | Question |
|---|---|
| V1 | Accept H1 as **denied** for retention and rebuilds, with FRED kept for manual reference only? |
| V2 | H2 and H3: is a modest one-off download of public-domain history acceptable on your reading of the live pages, given that the terms are silent on automated access (as for U1)? |
| V3 | H2: does the NY Fed's role as collector of the par-curve inputs change Treasury's public-domain presumption? (Recommendation: no, because Treasury publishes the curve as its own; but it is unverified.) |
| V4 | H4: does F2's history suffice for the duration factor (daily from 2013 only; longer history is monthly)? This is a data-need question for criterion 9 as much as a rights one |
| V5 | ALFRED vintages: shall a permission request to the St. Louis Fed be drafted for later (a vendor contact needs your instruction)? |

## Not approved by this document

Every row is a proposal. No register value changes, nothing is downloaded and no publisher is contacted.
