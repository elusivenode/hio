---
id: OD-0210
title: "Owner authorises relocating EODHD-dependent research results to a local results store, leaving public stubs and pointers; one final verification of F-2 scoped to it"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-relocate-results.md (owner's messages, verbatim, with Claude's questions)
  sha256: 63f0f373b649f9904e50348a28eb64d9a08dfcc3334d60728fef3b0336a3245e
  date: 2026-11-22
  quote: "Y"
base_revision: e780e7c90a4ab41309005559b7d97faca077ce8f
related: {adrs: [], tasks: [T-0022, T-0023], findings: [F-REVIEW-2026-11-22-e0004-1-2], ods: [OD-0171, OD-0176, OD-0184, OD-0196, OD-0206, OD-0209]}
---

# OD-0210: results out of the public repository

Three verifications left F-2 open, each on redactions Claude had missed, and a stricter sweep found more. The architect advised (consultation `20261122T111637-ask-66f8`) that sentence-by-sentence redaction is poor value, that "no numerals" is not an evidenced safe harbour under EODHD's terms, and that the cleaner boundary is to keep result-bearing evidence locally. Claude had leaned to a written line with a waiver, and changed its view. **This supersedes OD-0206's line for the files it covers:** they no longer carry readings either.

**Authorised:**

1. **Relocate the result-bearing evidence** to a local results store under `~/.hio-research/`, each file copied byte-for-byte from named git revisions under a manifest with hashes, and replace each public file with a stub: its identifier, what kind of record it is, its status, and where the local copy is. The files: the E-0002 assessment and stability records; the E-0003 result; the T-0023 corroboration 1, episodes, recommendation and panel records; the E-0004 step 1, step 1b and result records.
2. **Replace result statements with pointers** in the repeated summaries: the experiments register, the findings index, the three handoffs that repeat them, `STATUS.md`, and the one rate in the T-0003 vendor assessment.
3. **One final Codex verification** of F-2, scoped to this relocation, assigned by Claude under OD-0184 A2.

**The store:** local only, one folder per record, a manifest, and a DuckDB catalogue of what it holds. The owner asked about a database or blob storage. A private, deletable blob container as a backup is a **separate design, not authorised here:** it needs the owner's reading that EODHD's terms allow private cloud storage of derived results, and its own yes for the Azure change. The immutable evidence account is not used: data under a subscription that may end must stay deletable.

**Stays public:** preregistrations, the CPI first-release records, the issuer-against-audited corroboration (`corroboration-2.md`), tools, tests and specs.

**Not touched:** owner decision records, `docs/history/`, and review records. They hold readings only; any residual in them is for a scoped owner decision after the verification. Git history is kept (OD-0196): relocation does not retract what was published.

## Not authorised

Closing or waiving F-2; any change to an acceptance, a verdict or a result; any cloud storage; rewriting history.

## Corrections (append-only)
