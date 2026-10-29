---
id: OD-0116
title: "Owner adopts Claude's proposed answers to T-0002 U1–U6 for the S1b-1 cash datasets (D1, D2, D3, D8, D9); D5 and D6 stay blocked; no right is marked owner_verified until the owner confirms the live-clause reading (U7)"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-rights-answers.md (owner's message AL, verbatim, with the questions Claude put)
  sha256: 59c5348b2682cd6ae626706cd4098a1c4b293ecd6f2edcef6563bdc07e8ecb7d
  date: 2026-10-29
  quote: "I approve proceeding with you proposed answers."
applies_to:
  - path: docs/research/T-0002-owner-verification-matrix.md
    revision: "section 4, at a56462cb60a002324f90097da28168396c8ae918"
related: {adrs: [HIO-ADR-0012], tasks: [T-0002, T-0009, T-0010], findings: [], ods: [OD-0013, OD-0064, OD-0076, OD-0115]}
---

# OD-0116: the owner's answers to U1–U6

## The answers adopted (message AL)

| # | Question (T-0002 matrix §4) | Owner's answer |
|---|---|---|
| U1 | RBA automated retrieval of D1–D3 | **Permitted on the owner's judgement**: one polite request per series per scheduled slot, with attribution. D4 is out of the minimal scope. |
| U2 | D2 and D3 under CR or FD | **CR** (the stricter reading) |
| U3 | Attribution plus a no-endorsement statement satisfies CR for internal research releases | **Yes, internal research use only** |
| U4 | SOFR is NY Fed content, outside the view-only third-party clause | **Yes**, on the SOFR clause's own wording |
| U5 | Raw retention for D1–D3, D8, D9 | **Indefinite.** The whole RBA F1 file is kept as a sealed receipt; its ASX and FENICS columns are never published and never used in a release (completes OD-0064's design assumption for these columns) |
| U6 | D5 (WM/Reuters) and D6 (ASX) | **Blocked** |

## What this does not yet do

**U7 is not confirmed.** The matrix states that verification needs the owner to read the live clauses (RBA copyright
§§2–5 and 7.2; the NY Fed terms of use); the evidence quotations are fetch-tool extracts. Message AL adopts the answers
but does not state that reading. So:
- `registers/sources.yaml` is **unchanged**; D1, D2, D3, D8 and D9 stay `unknown` (= deny);
- the rights gate still refuses; **H1 is not met**.

On the owner's confirmation of U7, a correction to this OD records it and `sources.yaml` is updated for the five datasets
and the operations above only.

## Not authorised

Any fetch; any right marked verified; D4, D5, D6; distribution beyond `hio_internal`; Authorisation B.

## Corrections (append-only)

### Correction 1 (2026-10-29): U7 confirmed; D1, D2, D3, D8 and D9 owner_verified

**Source:** `docs/history/2026-10-29-owner-azure-assessment-and-u7.md` (sha256
`68d8e6eadfbd4a76086d35ff9cbca50ce13efbdc543755f545e9472a5c351c1b`), message AN, "yes to all.", answering question 5:
"Have you read the live RBA and NY Fed terms yourself, and do they support the answers you adopted?"

**Effect.** `registers/sources.yaml` gains five dataset-level records (`rba.cash_rate`, `rba.expert_judgement`,
`rba.cash_rate_tri`, `nyfed.sofr`, `nyfed.sofr_index`; OD-0065: each dataset on its own record), `owner_verified` by this
OD, with raw retention indefinite. Their permissions follow the matrix and the adopted answers:
- **Capture is cleared.** `automated_retrieval`, `raw_retention` and `external_processing` are allow or conditional with
  the condition recorded as satisfied (internal use, two requests a day, declared User-Agent, nothing published).
  The gate now permits `fetch` and `store_raw` for the five datasets, on a CI or cloud host too.
- **Derivation is not yet cleared.** `internal_compute`, `derivation`, `derived_storage`, `distribution.hio_internal`
  and `agent_context` are conditional on release notices (RBA: attribution and no-endorsement statement; NY Fed: D
  derivation label, E no endorsement, T DTCC notice). No release carries them today, so the conditions are **not**
  recorded as satisfied and the gate refuses `build` until they are implemented and recorded.
- **Unchanged:** the parent records `rba_statistical_tables` and `nyfed_reference_rates` (still unverified), D4, D5, D6,
  every consumer class beyond `hio_internal`, quotation, post-termination and audit retention (unknown = deny).

H1 is met **for capture**. Authorisation B is still a separate act.
