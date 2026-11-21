---
id: OD-0188
title: "Owner verifies the BLS CPI-U rights (bls_cpi), on the public-domain statement and the API terms, with one notice as the condition; no download yet"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-verify-bls-cpi.md (owner's message, verbatim, with Claude's question)
  sha256: 7f8faf12dda428a86ec1ca5f30e927c12e8bc1f398b3b6b0048d858eaccdf856
  date: 2026-11-22
  quote: "yes, verify bls_cpi"
base_revision: c6886d9e50d034f3a21cb57fa5d736e2a078592c
related: {adrs: [], tasks: [T-0002], findings: [], ods: [OD-0156, OD-0166, OD-0181, OD-0187]}
---

# OD-0188: BLS CPI-U rights

The owner verified `bls_cpi` with the rights proposed in `docs/research/T-0002-cpi-reading-pack.md`, on BLS's public-domain statement ("everything that we publish … is in the public domain") and its Terms of Service (last modified 2023-08-30).

**The condition, on every use:** "Source: U.S. Bureau of Labor Statistics, CPI-U (CUUR0000SA0), retrieved <date>. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov." No BLS emblem or logo. Derived series are labelled as HIO's.

| Allowed on that condition | Still denied or unknown |
|---|---|
| raw retention (indefinite, for audit and rebuild), internal compute, derivation, derived storage, `hio_internal` distribution, agent context, external processing (Codex), quotation in documents | SMSF and third-party distribution; post-termination; audit retention |

**Automated retrieval** is `conditional`: one bounded download, with a declared User-Agent, **after its own yes**. No condition is recorded as met.

`alfred_fred.cpi_release_dates` stays `unverified`.

## Not authorised

The download; E-0004's adoption or any run; any SMSF or third-party release.

## Corrections (append-only)
